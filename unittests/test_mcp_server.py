"""
Tests for the read-only MCP server that wraps the REST API (see app.mcp_server).

These assert the *contract* we care about: the MCP is mounted, only the allowlisted
(non-mutating) endpoints are exposed, the tool names are the clean remapped ones, auth
is off in the test environment (no MCP_AUTH0_* configured) but wires up correctly when
enabled, and a wrapped tool actually works end-to-end over an MCP session.
"""

import asyncio

import pytest  # type: ignore[import]
from fastapi.testclient import TestClient

from app.main import _mcp_app, app
from app.mcp_server import _MCP_NAMES, _annotate_read_only, _build_route_map_fn
from app.mcp_server.settings import McpSettings


def _build_test_mcp(fastapi_app):  # type: ignore[no-untyped-def]
    """build an MCP from the app exactly as attach_mcp does (route filter + read-only tags)"""
    from fastmcp import FastMCP

    return FastMCP.from_fastapi(
        app=fastapi_app,
        name="test",
        route_map_fn=_build_route_map_fn(),
        mcp_component_fn=_annotate_read_only,
        mcp_names=_MCP_NAMES,
    )


# the exact read-only tool set we expect (the JSON data endpoints; the two ICS-export
# endpoints are intentionally excluded -- see app.mcp_server._MCP_NAMES)
EXPECTED_TOOL_NAMES = {
    "is_working_day",
    "next_working_day",
    "previous_working_day",
    "add_working_days",
    "add_calendar_days",
    "generate_all_fristen",
    "generate_fristen_for_type",
}


def _tool_names(fastapi_app) -> set[str]:
    """build an MCP from the app the same way attach_mcp does and return its tool names"""
    tools = asyncio.run(_build_test_mcp(fastapi_app)._list_tools())  # pylint: disable=protected-access
    return {t.name for t in tools}


def test_mcp_is_served_at_mcp_path() -> None:
    """the MCP endpoint is served at /mcp on the main app (root-level, not mounted)"""
    assert _mcp_app is not None, "MCP should be available (fastmcp installed)"
    assert any(getattr(route, "path", "") == "/mcp" for route in app.routes)


def test_only_expected_readonly_tools_are_exposed() -> None:
    """exactly the allowlisted endpoints become tools; nothing more, nothing less"""
    assert _tool_names(app) == EXPECTED_TOOL_NAMES


def test_ics_export_endpoints_are_not_exposed_as_tools() -> None:
    """
    the two ICS-export endpoints return binary file downloads and are deliberately NOT
    allowlisted -- they must never appear as MCP tools.
    """
    names = _tool_names(app)
    assert not any("export" in n.lower() for n in names)
    assert "generate_and_export_whole_calendar" not in names
    assert "generate_and_export_fristen_for_type" not in names


def test_only_allowlisted_operations_become_tools() -> None:
    """
    read-only is enforced structurally: an endpoint that is not in the allowlist is
    excluded regardless of verb -- a new GET *or* a new write POST both stay out until
    deliberately added to _MCP_NAMES.
    """
    from fastapi import FastAPI

    throwaway = FastAPI()

    @throwaway.post("/CreateFoo")  # a future write endpoint
    async def create_foo() -> dict:  # pragma: no cover - never called
        return {}

    @throwaway.get("/NewReadThing")  # a future read endpoint, not yet allowlisted
    async def new_read_thing() -> dict:  # pragma: no cover - never called
        return {}

    assert _tool_names(throwaway) == set(), "nothing outside the allowlist may become a tool"


def test_mcp_names_keys_match_real_operation_ids() -> None:
    """
    guard for the fragile part: every _MCP_NAMES key must be a real operationId on the app,
    otherwise the remap silently no-ops.
    """
    operation_ids = {op["operationId"] for methods in app.openapi()["paths"].values() for op in methods.values()}
    unknown = set(_MCP_NAMES) - operation_ids
    assert not unknown, f"_MCP_NAMES has keys that are not operationIds on the app: {unknown}"


def test_all_tools_are_annotated_read_only() -> None:
    """every exposed tool must carry readOnlyHint=True (this API is strictly read-only)"""
    tools = asyncio.run(_build_test_mcp(app)._list_tools())  # pylint: disable=protected-access
    assert tools, "expected some tools"
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.readOnlyHint is True, tool.name


def test_tool_names_are_the_clean_remapped_ones() -> None:
    """every remapped name is present and the clunky auto-generated ones are gone"""
    names = _tool_names(app)
    assert set(_MCP_NAMES.values()) <= names
    # none of the raw operationIds leaked through
    assert not any(raw in names for raw in _MCP_NAMES)


def _clear_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("MCP_AUTH0_ISSUER_BASE_URL", "MCP_AUTH0_AUDIENCE", "MCP_RESOURCE"):
        monkeypatch.delenv(var, raising=False)


def test_auth_disabled_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """with no MCP_AUTH0_* env vars, auth is disabled (the dev bypass)"""
    _clear_auth_env(monkeypatch)
    assert McpSettings().auth_enabled is False


def test_auth_enabled_when_issuer_and_audience_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """issuer + audience present -> auth is enabled, with derived jwks/base_url"""
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("MCP_AUTH0_ISSUER_BASE_URL", "https://auth.hochfrequenz.de/")
    monkeypatch.setenv("MCP_AUTH0_AUDIENCE", "https://fristenkalender-api.example/mcp")
    settings = McpSettings()
    assert settings.auth_enabled is True
    assert settings.jwks_uri == "https://auth.hochfrequenz.de/.well-known/jwks.json"
    # base_url is the host root so the RFC 9728 PRM lands at the correct path
    assert settings.base_url == "https://fristenkalender-api.example"
    assert settings.resource_uri == "https://fristenkalender-api.example/mcp"


def test_partial_auth_config_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """exactly one of issuer/audience is a misconfig and must fail loudly, not silently open"""
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("MCP_AUTH0_AUDIENCE", "https://fristenkalender-api.example/mcp")
    with pytest.raises(ValueError, match="partially configured"):
        McpSettings()


def test_attach_mcp_propagates_partial_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    a half-configured deployment must abort startup, not be swallowed: attach_mcp lets the
    partial-config error propagate (main.py calls it directly, with no error guard), so /mcp
    is never left silently unmounted when auth was meant to be on.
    """
    from fastapi import FastAPI

    from app.mcp_server import attach_mcp

    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("MCP_AUTH0_ISSUER_BASE_URL", "https://auth.hochfrequenz.de/")  # audience missing
    with pytest.raises(ValueError, match="partially configured"):
        attach_mcp(FastAPI())


def test_audience_must_end_in_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    the advertised resource is always <host>/mcp, so an audience with a different/trailing
    path would silently make every real token 401 -- it must fail loudly at config time.
    """
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("MCP_AUTH0_ISSUER_BASE_URL", "https://auth.hochfrequenz.de/")
    monkeypatch.setenv("MCP_AUTH0_AUDIENCE", "https://fristenkalender-api.example/mcp/")  # trailing slash
    with pytest.raises(ValueError, match="ending in exactly '/mcp'"):
        McpSettings()


def test_rest_api_still_works_alongside_mcp(tester_client: TestClient) -> None:
    """serving the MCP must not break the underlying REST endpoints"""
    response = tester_client.get("/api/IsWorkingDay/2024-01-02")
    assert response.status_code == 200
    assert response.json()["is_working_day"] is True


def _middleware_class_names(asgi_app: object) -> set[str]:
    """unwrap a chain of ASGI middleware (each holds its inner app in `.app`) into class names"""
    names: set[str] = set()
    current = asgi_app
    for _ in range(20):  # bounded; the real chain is short
        names.add(type(current).__name__)
        current = getattr(current, "app", None)
        if current is None:
            break
    return names


def test_auth_is_scoped_to_mcp_route_not_the_whole_app(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The REST API must stay unauthenticated: auth middleware may wrap ONLY the /mcp route,
    never the parent app. Regression for copying routes without the auth middleware (which
    would 401 valid tokens) AND for accidentally authenticating the whole HTTP API.
    """
    from fastapi import FastAPI
    from starlette.routing import Route

    from app.mcp_server import attach_mcp

    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("MCP_AUTH0_ISSUER_BASE_URL", "https://auth.hochfrequenz.de/")
    monkeypatch.setenv("MCP_AUTH0_AUDIENCE", "http://testserver/mcp")

    host_app = FastAPI()
    attach_mcp(host_app)

    # nothing auth-related on the parent app -> REST is untouched
    app_level = {getattr(m.cls, "__name__", "") for m in host_app.user_middleware}
    assert "AuthenticationMiddleware" not in app_level
    assert "AuthContextMiddleware" not in app_level

    # ...but the /mcp route itself is wrapped with the token-validation middleware
    mcp_route = next(r for r in host_app.routes if isinstance(r, Route) and r.path == "/mcp")
    on_route = _middleware_class_names(mcp_route.app)
    assert "HostOriginGuardMiddleware" in on_route
    assert "AuthenticationMiddleware" in on_route
    assert "RequireAuthMiddleware" in on_route
    assert "RequestContextMiddleware" in on_route


def test_no_auth_middleware_when_auth_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """with auth off, the /mcp route carries no auth middleware (nothing to validate)"""
    from fastapi import FastAPI
    from starlette.routing import Route

    from app.mcp_server import attach_mcp

    _clear_auth_env(monkeypatch)
    host_app = FastAPI()
    attach_mcp(host_app)
    mcp_route = next(r for r in host_app.routes if isinstance(r, Route) and r.path == "/mcp")
    assert "AuthenticationMiddleware" not in _middleware_class_names(mcp_route.app)


def test_valid_bearer_token_is_accepted() -> None:
    """
    End-to-end proof that the scoped auth wiring lets a *valid* token through (the case the
    unauthenticated-401 test cannot see). Uses an HS256 verifier so the test can mint a token;
    the /mcp route is wrapped with the same auth-middleware pattern as attach_mcp (the token
    middleware from ``auth.get_middleware()``; the Host/RequestContext guards are omitted as
    they are irrelevant to token validation). A valid token must get past auth (reaching the
    session layer), not be rejected with 401.
    """
    import time
    from contextlib import AsyncExitStack, asynccontextmanager
    from typing import Any, AsyncGenerator

    import jwt
    from fastapi import FastAPI
    from fastmcp import FastMCP
    from fastmcp.server.auth import JWTVerifier, RemoteAuthProvider
    from pydantic import AnyHttpUrl
    from starlette.routing import Route

    secret = "unit-test-secret-that-is-long-enough-for-hs256"  # >=32 bytes
    issuer, audience = "https://auth.hochfrequenz.de/", "http://testserver/mcp"
    auth = RemoteAuthProvider(
        token_verifier=JWTVerifier(public_key=secret, algorithm="HS256", issuer=issuer, audience=audience),
        authorization_servers=[AnyHttpUrl(issuer)],
        base_url="http://testserver",
    )
    mcp_app = FastMCP(name="test", auth=auth).http_app(path="/mcp")
    for route in mcp_app.routes:
        if isinstance(route, Route) and route.path == "/mcp":
            wrapped = route.app
            for middleware in reversed(auth.get_middleware()):
                wrapped = middleware.cls(wrapped, *middleware.args, **middleware.kwargs)
            route.app = wrapped

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(mcp_app.lifespan(app))
            yield

    host_app = FastAPI(lifespan=lifespan)
    host_app.router.routes.extend(mcp_app.routes)

    token = jwt.encode(
        {"iss": issuer, "aud": audience, "sub": "tester", "iat": int(time.time()), "exp": int(time.time()) + 3600},
        secret,
        algorithm="HS256",
    )
    headers = {"accept": "application/json, text/event-stream"}
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    with TestClient(host_app) as client:
        assert client.post("/mcp", headers=headers, json=body).status_code == 401  # no token
        authed = client.post("/mcp", headers={**headers, "Authorization": f"Bearer {token}"}, json=body)
        assert authed.status_code != 401, "a valid bearer token must pass auth (not be rejected)"


def test_resource_server_prm_and_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    with auth enabled, serve RFC 9728 Protected Resource Metadata at the host-root path
    and return 401 + WWW-Authenticate on /mcp.
    """
    from fastapi import FastAPI

    from app.mcp_server import attach_mcp

    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("MCP_AUTH0_ISSUER_BASE_URL", "https://auth.hochfrequenz.de/")
    # audience host must line up with the TestClient host so resource == audience
    monkeypatch.setenv("MCP_AUTH0_AUDIENCE", "http://testserver/mcp")

    host_app = FastAPI()
    attach_mcp(host_app)  # adds /mcp + the .well-known PRM route at root
    client = TestClient(host_app)  # no lifespan needed: PRM + auth reject happen before the session manager

    prm = client.get("/.well-known/oauth-protected-resource/mcp")
    assert prm.status_code == 200
    body = prm.json()
    assert body["resource"] == "http://testserver/mcp"
    assert body["authorization_servers"] == ["https://auth.hochfrequenz.de/"]

    unauth = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert unauth.status_code == 401
    assert "resource_metadata=" in unauth.headers.get("www-authenticate", "")

    # a cross-origin client must not be blocked by the Host/Origin guard: it should reach
    # auth (401 for the missing token), NOT be rejected 403 on Origin. Guards the allowed_origins fix.
    cross_origin = client.post(
        "/mcp", headers={"origin": "https://claude.ai"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )
    assert cross_origin.status_code == 401


# ---------------------------------------------------------------------------
# End-to-end: exercise a wrapped tool over a real MCP session
# ---------------------------------------------------------------------------

_MCP_HEADERS = {"accept": "application/json, text/event-stream", "content-type": "application/json"}


def _mcp_session(client: TestClient) -> str:
    """Open a new MCP session and return its session ID."""
    resp = client.post(
        "/mcp",
        headers=_MCP_HEADERS,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1.0"},
            },
        },
    )
    assert resp.status_code == 200, f"MCP initialize failed: {resp.text}"
    session_id: str = resp.headers["mcp-session-id"]
    # Send the required `notifications/initialized` handshake
    client.post(
        "/mcp",
        headers={**_MCP_HEADERS, "mcp-session-id": session_id},
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
    )
    return session_id


def _mcp_call(client: TestClient, session_id: str, call_id: int, tool: str, arguments: dict) -> dict:
    """Invoke an MCP tool and return the parsed JSON-RPC result dict."""
    import json

    resp = client.post(
        "/mcp",
        headers={**_MCP_HEADERS, "mcp-session-id": session_id},
        json={
            "jsonrpc": "2.0",
            "id": call_id,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        },
    )
    assert resp.status_code == 200, f"MCP tools/call HTTP error: {resp.status_code} {resp.text}"
    for line in resp.text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    raise AssertionError(f"No SSE data line found in response: {resp.text!r}")


def test_is_working_day_tool_works_over_mcp_session(tester_client: TestClient) -> None:
    """
    A wrapped tool must be callable end-to-end over an MCP session and return the same
    answer as the REST endpoint. 2024-01-01 (New Year) is not a BDEW working day.
    """
    session_id = _mcp_session(tester_client)
    result = _mcp_call(
        tester_client,
        session_id,
        call_id=2,
        tool="is_working_day",
        arguments={"check_date": "2024-01-01"},
    )
    assert result["result"].get("isError") is not True, f"tool call errored: {result}"
    structured = result["result"]["structuredContent"]
    assert structured["is_working_day"] is False
