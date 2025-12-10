"""FastAPI application for Fristenkalender."""

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from app.routers import calendar, fristen


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


__all__ = ["app"]
