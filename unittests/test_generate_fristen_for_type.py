from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateFristenForType:
    def test_ok_get(self):
        response = client.get("/api/GenerateFristenForType/2023/GPKE")
        assert response.status_code == HTTPStatus.OK
        actual_fristen_list = response.json()
        actual_frist = actual_fristen_list[0]
        expected = {
            "date": "2022-12-28",
            "description": "Letzter Termin Anmeldung asynchrone Bilanzierung (Strom)",
            "fristen_type": "FristenType.GPKE",
            "label": "3LWT",
            "ref_not_in_the_same_month": None,
        }
        assert actual_frist == expected

    @pytest.mark.parametrize(
        "year,fristen_type,expected_length",
        [
            pytest.param("2025", "GPKE", 6, id="No GPKE 3LWT Fristen after 24h LFW (June 2025)"),
            pytest.param("2026", "GPKE", 0),
        ],
    )
    def test_non_empty_get(self, year: str, fristen_type: str, expected_length: int):
        response = client.get(f"/api/GenerateFristenForType/{year}/{fristen_type}")
        assert response.status_code == HTTPStatus.OK
        actual = response.json()
        assert len(actual) == expected_length

    @pytest.mark.parametrize(
        "year,fristen_type",
        [
            pytest.param("2023", "hhhhhh"),
        ],
    )
    def test_bad_request(self, year: str, fristen_type: str):
        response = client.get(f"/api/GenerateFristenForType/{year}/{fristen_type}")
        assert response.status_code == HTTPStatus.BAD_REQUEST
