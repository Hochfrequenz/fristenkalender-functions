from http import HTTPStatus
from typing import Optional
import datetime
import json

import azure.functions as func
import pytest  # type:ignore[import]
from _pytest.logging import LogCaptureFixture  # type:ignore[import]

from GenerateFristenForType import main


class TestGenerateFristenForType:
    @pytest.mark.parametrize(
        "ok_request, expected_log_message",
        [
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params={"fristen_type": "GPKE"},
                    body=bytes(),
                ),
                "Generating a list of fristen for the type GPKE ",
            ),
        ],
    )
    def test_ok_get(
        self,
        caplog: LogCaptureFixture,
        ok_request: func.HttpRequest,
        expected_log_message: Optional[str],
    ):
        actual_response = main(ok_request)
        assert actual_response.status_code == HTTPStatus.OK
        actual_fristen_list = json.loads(actual_response.get_body().decode("utf-8"))
        actual_frist = actual_fristen_list[0]
        expected = "FristWithAttributesAndType(date=datetime.date(2022, 12, 28), label='3LWT', type=<FristenType.GPKE: 'GPKE'>)"
        assert actual_frist == expected

    @pytest.mark.parametrize(
        "bad_request, expected_log_message",
        [
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params={"fristen_type": "hhhhhh"},
                    body=bytes(),
                ),
                "Request parameter is invalid: 'hhhhhh' is not a valid fristen_type",
                id="Wrong fristen type",
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params={"fristen_type": ""},
                    body=bytes(),
                ),
                "Request parameter must not be empty",
                id="Empty parameter",
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params=None,
                    body=bytes(),
                ),
                "Request parameter must not be none",
                id="none parameter",
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    route_params={},
                    body=bytes(),
                ),
                "Empty route params",
                id="Empty route params",
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateFristenForType",
                    body=bytes(),
                ),
                "No route params",
                id="No route params",
            ),
        ],
    )
    def test_bad_request(
        self,
        caplog: LogCaptureFixture,
        bad_request: func.HttpRequest,
        expected_log_message: Optional[str],
    ):
        actual_response = main(bad_request)
        assert actual_response.status_code == HTTPStatus.BAD_REQUEST
