import json
from http import HTTPStatus

import azure.functions as func
import pytest  # type:ignore[import]

from GenerateFristenForType import main  # type:ignore[import]


class TestGenerateFristenForType:
    @pytest.mark.parametrize(
        "ok_request",
        [
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params={"year": "2023", "fristen_type": "GPKE"},
                    body=bytes(),
                )
            ),
        ],
    )
    def test_ok_get(self, ok_request: func.HttpRequest):
        actual_response = main(ok_request)
        assert actual_response.status_code == HTTPStatus.OK
        actual_fristen_list = json.loads(actual_response.get_body().decode("utf-8"))
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
        "bad_request",
        [
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params={"year": "2023", "fristen_type": "hhhhhh"},
                    body=bytes(),
                )
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params={"year": "2023", "fristen_type": ""},
                    body=bytes(),
                )
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params=None,
                    body=bytes(),
                )
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params={},
                    body=bytes(),
                )
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    body=bytes(),
                )
            ),
        ],
    )
    def test_bad_request(self, bad_request: func.HttpRequest):
        actual_response = main(bad_request)
        assert actual_response.status_code == HTTPStatus.BAD_REQUEST
