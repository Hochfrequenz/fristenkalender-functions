"""FastAPI application for Fristenkalender."""

from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.mcp_server import attach_mcp
from app.routers import calendar, fristen

# assigned by attach_mcp() at the bottom of this module; referenced (late-bound) inside the
# lifespan below. stays None only when the MCP is disabled via MCP_ENABLE=false.
_mcp_app = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, Any]:
    """
    Runs the MCP sub-app's lifespan (required for its session manager to initialise)
    when the MCP is mounted; a no-op otherwise.
    """
    async with AsyncExitStack() as stack:
        if _mcp_app is not None:
            await stack.enter_async_context(_mcp_app.lifespan(_app))
        yield


class VersionInfo(BaseModel):
    """Version information for the application."""

    commit_hash: str
    build_date: str
    tag: str


_VERSION_FILE_PATH = Path(__file__).parent / "version.json"
# the version file is overwritten in the CI/CD pipeline
# such that it contains the actual values instead of just placeholders
assert _VERSION_FILE_PATH.exists() and _VERSION_FILE_PATH.is_file()
_version: VersionInfo
with open(_VERSION_FILE_PATH, encoding="utf-8", mode="r") as _version_file:
    _version = VersionInfo.model_validate_json(_version_file.read())

app = FastAPI(
    title="Fristenkalender API",
    description="API for generating BDEW Fristenkalender deadlines",
    # surface the real deployed version (from version.json, written by the CD pipeline) in the
    # OpenAPI spec instead of FastAPI's default "0.1.0"; drop the leading "v" of the git tag.
    version=_version.tag.removeprefix("v"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fristen.router)
app.include_router(calendar.router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/version")
async def version() -> VersionInfo:
    """Returns the version of the server."""
    return _version


# Serve the read-only MCP server (wraps the routes above) at /mcp, built after the routes and
# endpoints are registered so the OpenAPI spec -- and thus the tool set -- is complete.
# attach_mcp returns None only if disabled via MCP_ENABLE=false; a misconfiguration (e.g. only
# one of the MCP_AUTH0_* pair) raises and aborts startup on purpose (see app.mcp_server.settings)
# rather than silently leaving /mcp unauthenticated.
_mcp_app = attach_mcp(app)


__all__ = ["app"]
