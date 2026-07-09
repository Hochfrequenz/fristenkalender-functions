from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def tester_client() -> Generator[TestClient, Any, None]:
    """
    A FastAPI TestClient created as a context manager so the app lifespan runs -- required
    for the mounted MCP server's session manager to initialise (see app.main.lifespan).
    """
    with TestClient(app=app) as client:
        yield client
