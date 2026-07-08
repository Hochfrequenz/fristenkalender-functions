"""
Read-only MCP server that wraps the existing FastAPI REST API.

The whole point of this package is to add **no logic**: it re-exposes the very
same endpoints as MCP tools via ``FastMCP.from_fastapi``, so the OpenAPI spec
(and therefore the tool set) always stays in sync with the REST API.

Design decisions (mirroring ``Hochfrequenz/ahbicht-functions`` and
``Hochfrequenz/ahb-tabellen``):
  * same image / same process -- the MCP is served on the existing app at ``/mcp``
  * read-only -- only the explicitly allowlisted operationIds become tools
    (:data:`_MCP_NAMES`); everything else is excluded, so a future write endpoint
    can never silently become a callable tool
  * auth -- Auth0 OAuth 2.1 *resource server* (validate bearer JWTs; advertise the
    tenant via RFC 9728); optional in dev (see :mod:`app.mcp_server.settings`)
"""

import logging
from typing import Any, Callable
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.server.auth import AuthProvider, JWTVerifier, RemoteAuthProvider
from fastmcp.server.http import HostOriginGuardMiddleware, RequestContextMiddleware, StarletteWithLifespan
from fastmcp.server.providers.openapi import MCPType
from fastmcp.tools import Tool
from mcp.types import ToolAnnotations
from pydantic import AnyHttpUrl
from starlette.routing import Route

from .settings import McpSettings

_logger = logging.getLogger(__name__)

# key = the operationId FastAPI generates for a route; value = the MCP tool name we expose.
#
# We remap here (MCP only) rather than setting ``operation_id=`` on the routes to give the
# LLM-facing tools clean, stable names without churning the REST operationIds (which feed the
# OpenAPI spec / any generated clients). Keys must match app.openapi()["paths"][...]["operationId"]
# (a test guards this); unmapped operations keep their auto-generated name, so a rename here is
# cosmetic, never fatal.
#
# Allowlist = the JSON data endpoints only. The two ICS-export endpoints
# (GenerateAndExport*) are intentionally left out: they return binary text/calendar file
# downloads, which are not useful as MCP tools. They stay REST-only.
_MCP_NAMES = {
    "check_is_working_day_api_IsWorkingDay__check_date__get": "is_working_day",
    "get_next_working_day_endpoint_api_NextWorkingDay__start_date__get": "next_working_day",
    "get_previous_working_day_endpoint_api_PreviousWorkingDay__start_date__get": "previous_working_day",
    "add_working_days_endpoint_api_AddWorkingDays__start_date___number_of_days__get": "add_working_days",
    "add_calendar_days_endpoint_api_AddCalendarDays__start_date___number_of_days__get": "add_calendar_days",
    "generate_all_fristen_api_GenerateAllFristen__year__get": "generate_all_fristen",
    "generate_fristen_for_type_api_GenerateFristenForType__year___fristen_type__get": "generate_fristen_for_type",
}


def _build_route_map_fn() -> Callable[[Any, Any], MCPType]:
    """
    Return a route filter that enforces the read-only invariant *structurally*:
    an operation becomes a TOOL only if its operationId is in the allowlist
    (:data:`_MCP_NAMES`); anything else is EXCLUDED.

    This does not rely on HTTP-verb heuristics, so a future ``POST /CreateFoo`` (or
    any other write endpoint) can never silently turn into a callable tool -- it is
    excluded until someone deliberately adds it to the allowlist.
    """

    def route_map_fn(route: Any, _route_type: Any) -> MCPType:  # (HTTPRoute, MCPType) -> MCPType
        if route.operation_id in _MCP_NAMES:
            return MCPType.TOOL
        return MCPType.EXCLUDE

    return route_map_fn


def _annotate_read_only(_route: Any, component: Any) -> None:
    """
    Tag every exposed operation as a read-only MCP tool (``readOnlyHint``).

    All our endpoints are non-mutating, and clients/LLMs use this hint to know a tool is
    safe to call without side effects. FastMCP does not set it automatically for
    OpenAPI-derived tools, so we set it here (called once per created component).
    """
    if isinstance(component, Tool):
        base = component.annotations or ToolAnnotations()
        component.annotations = base.model_copy(update={"readOnlyHint": True})


def _build_auth(settings: McpSettings) -> AuthProvider | None:
    """
    Build an OAuth 2.1 resource-server auth provider, or ``None`` when auth is off.

    We only *validate* Auth0-issued bearer JWTs (JWKS/RS256, ``iss``/``aud``/``exp``)
    and advertise the tenant as the authorization server (RFC 9728). Clients self-register
    via Auth0 DCR and do PKCE themselves -- no confidential client / client_secret on our side.
    """
    if not settings.auth_enabled:
        _logger.warning("MCP auth is DISABLED (MCP_AUTH0_* not configured) -- do not do this in prod")
        return None

    verifier = JWTVerifier(
        jwks_uri=settings.jwks_uri,
        issuer=settings.issuer,
        audience=settings.mcp_auth0_audience,
    )
    return RemoteAuthProvider(
        token_verifier=verifier,
        authorization_servers=[AnyHttpUrl(settings.issuer)],
        # host root so the PRM lands at <root>/.well-known/oauth-protected-resource/mcp
        base_url=settings.base_url,
    )


def attach_mcp(app: FastAPI) -> StarletteWithLifespan | None:
    """
    Build the MCP server from ``app`` and serve it at ``/mcp`` on the same app.

    Returns the MCP ASGI sub-app (whose ``.lifespan`` the caller MUST chain into the
    parent app's lifespan, or the MCP session manager never initialises), or ``None``
    if the MCP is disabled.

    We add the MCP routes to the parent app's router at **root level** rather than
    ``app.mount("/mcp", ...)`` on purpose: RemoteAuthProvider serves the RFC 9728
    Protected Resource Metadata at ``/.well-known/oauth-protected-resource/mcp`` (host
    root, per RFC 9728 §3.1 path insertion). Mounting under ``/mcp`` would push that to
    ``/mcp/.well-known/...`` and break MCP client discovery. ``http_app(path="/mcp")``
    already serves the MCP endpoint at ``/mcp`` and the metadata at the correct root path.

    Copying *routes* (not the sub-app) drops the sub-app's app-level middleware -- the part
    that populates ``scope["user"]`` from the bearer token, the Host guard, and the request
    context. So we re-attach that stack, but **only around the ``/mcp`` route**, never onto
    the parent app. This is deliberate: the REST API must stay completely unauthenticated, so
    no auth middleware may run for its requests. Without the auth middleware the ``/mcp``
    route's ``RequireAuthMiddleware`` would reject even valid tokens with 401.

    Host/Origin note: we keep FastMCP's Host guard (allow the canonical MCP host) as
    defense-in-depth, but pass ``allowed_origins=["*"]`` -- the bearer token, not the Origin
    header, is the security boundary here, and a strict Origin allow-list would 403 legitimate
    cross-origin MCP clients (the failure would not show up in ``verify-mcp.sh``).
    """
    settings = McpSettings()
    if not settings.mcp_enable:
        _logger.info("MCP server disabled via MCP_ENABLE=false")
        return None

    auth = _build_auth(settings)
    mcp = FastMCP.from_fastapi(
        app=app,
        name=f"{app.title} (MCP)",  # derive from the REST app's title; tag as the MCP surface
        route_map_fn=_build_route_map_fn(),
        mcp_component_fn=_annotate_read_only,  # every tool is annotated read-only
        mcp_names=_MCP_NAMES,
        auth=auth,  # forwarded to FastMCP.__init__; None means unauthenticated (dev)
    )

    mcp_app = mcp.http_app(path="/mcp")
    # re-attach FastMCP's app-level middleware around ONLY the /mcp route so the REST API
    # remains untouched (see docstring). Order inner->outer: RequireAuth (already on route.app)
    # -> auth middleware -> Host guard -> request context (matches FastMCP's native stack).
    for route in mcp_app.routes:
        if isinstance(route, Route) and route.path == "/mcp":
            wrapped = route.app
            if auth is not None:
                for middleware in reversed(auth.get_middleware()):
                    wrapped = middleware.cls(wrapped, *middleware.args, **middleware.kwargs)
                wrapped = HostOriginGuardMiddleware(
                    wrapped,
                    allowed_hosts=[urlsplit(settings.resource_uri).netloc],
                    allowed_origins=["*"],
                )
            # populate get_http_request() for /mcp (fastmcp's own __init__ is untyped)
            wrapped = RequestContextMiddleware(wrapped)  # type: ignore[no-untyped-call]
            route.app = wrapped
    # add /mcp and the /.well-known metadata route to the parent app at root (see docstring)
    app.router.routes.extend(mcp_app.routes)
    _logger.info("MCP server available at /mcp (auth=%s)", "on" if settings.auth_enabled else "OFF")
    return mcp_app
