"""
Configuration for the (read-only) MCP server that wraps the REST API.

The MCP endpoint is an OAuth 2.1 **resource server** (mirroring
``Hochfrequenz/ahbicht-functions`` and ``Hochfrequenz/ahb-tabellen``): it
*validates* Auth0-issued bearer JWTs and advertises the tenant as its
authorization server via RFC 9728 metadata. It does **not** run the OAuth flow
itself -- MCP clients (Claude etc.) self-register via Auth0's Dynamic Client
Registration and do PKCE against ``auth.hochfrequenz.de``.

Env vars mirror the sibling repos so cross-repo ops is uniform:
  * ``MCP_AUTH0_ISSUER_BASE_URL``  e.g. ``https://auth.hochfrequenz.de/``
  * ``MCP_AUTH0_AUDIENCE``         the Auth0 API identifier == canonical MCP URI,
                                   e.g. ``https://fristenkalender-api.../mcp``
  * ``MCP_RESOURCE``               RFC 9728 resource value; defaults to the audience
  * ``MCP_ENABLE``                 set false to skip the mount entirely

Auth is optional: set BOTH issuer and audience to enable it, NEITHER to run
``/mcp`` unauthenticated (local dev / spike). Setting exactly one raises -- a
partial config almost certainly means a misconfigured deployment, and silently
exposing the endpoint would be worse. fristenkalender is prod-only, so one Auth0
API is needed for prod (the canonical URI is the prod ``/mcp`` URL); on Azure
these env vars are set from the Bicep container-app template, not manually.
"""

from urllib.parse import urlsplit, urlunsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class McpSettings(BaseSettings):
    """env-driven settings for the MCP wrapper; the tenant choice is just config"""

    # No env_prefix: each field name IS its environment variable (case-insensitive), so
    # there is no hidden prefix to reason about -- `mcp_enable` <-> MCP_ENABLE, etc.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # feature toggle: set MCP_ENABLE=false to skip mounting /mcp without code changes
    mcp_enable: bool = True

    # Auth0 resource-server config (all optional; validated as a pair below)
    mcp_auth0_issuer_base_url: str | None = None
    mcp_auth0_audience: str | None = None
    mcp_resource: str | None = None  # defaults to the audience

    @model_validator(mode="after")
    def _check_auth_pair(self) -> "McpSettings":
        """both issuer+audience, or neither -- a half-configured deployment must fail loudly"""
        if bool(self.mcp_auth0_issuer_base_url) != bool(self.mcp_auth0_audience):
            raise ValueError(
                "MCP auth is partially configured: set BOTH MCP_AUTH0_ISSUER_BASE_URL and "
                "MCP_AUTH0_AUDIENCE (or neither, to run /mcp unauthenticated)."
            )
        if self.mcp_auth0_audience:
            # The advertised RFC 8707 resource is always <host>/mcp (see base_url), so the
            # audience/resource must have exactly that path -- otherwise it would differ from
            # the token `aud` and every real token would silently 401. Fail loudly instead.
            resource = self.mcp_resource or self.mcp_auth0_audience
            if urlsplit(resource).path != "/mcp":
                raise ValueError(
                    "MCP audience/resource must be the canonical MCP URI ending in exactly '/mcp' "
                    f"(e.g. https://<host>/mcp); got path {urlsplit(resource).path!r}."
                )
        return self

    @property
    def auth_enabled(self) -> bool:
        """True only when the Auth0 issuer+audience pair is present"""
        return bool(self.mcp_auth0_issuer_base_url and self.mcp_auth0_audience)

    @property
    def issuer(self) -> str:
        """normalised issuer with a single trailing slash (Auth0's ``iss`` form)"""
        assert self.mcp_auth0_issuer_base_url is not None
        return self.mcp_auth0_issuer_base_url.rstrip("/") + "/"

    @property
    def jwks_uri(self) -> str:
        """Auth0 JWKS endpoint derived from the issuer (RS256 signature validation)"""
        return self.issuer + ".well-known/jwks.json"

    @property
    def resource_uri(self) -> str:
        """RFC 9728 resource == canonical MCP URI (defaults to the audience)"""
        assert self.mcp_auth0_audience is not None
        return self.mcp_resource or self.mcp_auth0_audience

    @property
    def base_url(self) -> str:
        """
        Host root of the resource URI (scheme + host, no path).

        RemoteAuthProvider serves the PRM at ``<base_url>/.well-known/oauth-protected-resource<path>``
        and reports ``resource = <base_url> + http_app_path("/mcp")``. Passing the host
        root here keeps that equal to ``resource_uri`` when the audience is ``https://<host>/mcp``.
        """
        parts = urlsplit(self.resource_uri)
        return urlunsplit((parts.scheme, parts.netloc, "", "", ""))
