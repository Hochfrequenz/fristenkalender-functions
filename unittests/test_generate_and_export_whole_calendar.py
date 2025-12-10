from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateAndExportWholeCalendar:
    @pytest.mark.parametrize(
        "filename,attendee,year",
        [
            pytest.param("", "bar", "2023"),
            pytest.param("foo", "", "2023"),
            pytest.param("foo", "bar", "hghhkjhkj"),
        ],
    )
    def test_bad_request(self, filename: str, attendee: str, year: str):
        response = client.get(f"/api/GenerateAndExportWholeCalendar/{filename}/{attendee}/{year}")
        assert response.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND, HTTPStatus.UNPROCESSABLE_ENTITY)

    def test_ok_get(self):
        response = client.get("/api/GenerateAndExportWholeCalendar/foo/bar/2023")
        assert response.status_code == HTTPStatus.OK
        file_body = response.content
        assert file_body is not None
        assert len(file_body) > 0
