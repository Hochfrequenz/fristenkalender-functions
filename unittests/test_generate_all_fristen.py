import json
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateAllFristen:
    @pytest.mark.parametrize(
        "year",
        [
            pytest.param("2023"),
        ],
    )
    def test_ok_get(self, year: str):
        response = client.get(f"/api/GenerateAllFristen/{year}")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert isinstance(body, list)
        assert not isinstance(body[0], str)
        assert all(isinstance(x, dict) for x in body)

    @pytest.mark.parametrize(
        "year",
        [
            pytest.param("hhhh"),
            pytest.param("0"),
        ],
    )
    def test_bad_request(self, year: str):
        response = client.get(f"/api/GenerateAllFristen/{year}")
        assert response.status_code == HTTPStatus.BAD_REQUEST
