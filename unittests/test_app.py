from http import HTTPStatus

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_healthy(self):
        response = client.get("/health")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"status": "healthy"}


class TestOpenApiDocs:
    def test_docs_endpoint_available(self):
        response = client.get("/docs")
        assert response.status_code == HTTPStatus.OK
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_available(self):
        response = client.get("/redoc")
        assert response.status_code == HTTPStatus.OK
        assert "text/html" in response.headers["content-type"]

    def test_openapi_json_available(self):
        response = client.get("/openapi.json")
        assert response.status_code == HTTPStatus.OK
        openapi = response.json()
        assert openapi["info"]["title"] == "Fristenkalender API"
        assert "/health" in openapi["paths"]
        assert "/api/GenerateAllFristen/{year}" in openapi["paths"]


class TestVersionEndpoint:
    def test_version_returns_version_info(self):
        response = client.get("/version")
        assert response.status_code == HTTPStatus.OK
        version_info = response.json()
        assert "commit_hash" in version_info
        assert "build_date" in version_info
        assert "tag" in version_info
