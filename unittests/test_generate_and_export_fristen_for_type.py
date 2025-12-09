from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateAndExportFristenForType:
    @pytest.mark.parametrize(
        "filename,attendee,year,fristen_type",
        [
            pytest.param("foo", "bar", "2023", "invalid_type"),
        ],
    )
    def test_bad_request(self, filename: str, attendee: str, year: str, fristen_type: str):
        response = client.get(f"/api/GenerateAndExportFristenForType/{filename}/{attendee}/{year}/{fristen_type}")
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_ok_get(self):
        response = client.get("/api/GenerateAndExportFristenForType/foo/bar/2023/GPKE")
        assert response.status_code == HTTPStatus.OK
        file_body = response.content
        assert file_body is not None
        assert len(file_body) > 0
