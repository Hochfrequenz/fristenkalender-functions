from http import HTTPStatus

import azure.functions as func
import pytest  # type:ignore[import]

from GenerateAndExportWholeCalendar import main  # type:ignore[import]


class TestGenerateAndExportWholeCalendar:
    @pytest.mark.parametrize(
        "bad_request",
        [
            pytest.param(func.HttpRequest("GET", "testhost", body=bytes())),  # no query param
            pytest.param(
                func.HttpRequest("GET", "testhost", body=bytes(), route_params={"filename": ""})
            ),  # empty param
            pytest.param(func.HttpRequest("GET", "testhost", body=bytes(), route_params={"filename": "foo"})),
            pytest.param(
                func.HttpRequest("GET", "testhost", body=bytes(), route_params={"filename": "foo", "attendee": "bar"})
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost",
                    body=bytes(),
                    route_params={"filename": "foo", "attendee": "bar", "year": "hghhkjhkj"},
                )
            ),
        ],
    )
    def test_bad_request(self, bad_request: func.HttpRequest):
        actual_response = main(bad_request)
        assert actual_response.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize(
        "ok_request",
        [
            pytest.param(
                func.HttpRequest(
                    "GET", "testhost", body=bytes(), route_params={"filename": "foo", "attendee": "bar", "year": "2023"}
                )
            ),
        ],
    )
    def test_ok_get(self, ok_request: func.HttpRequest):
        actual_response = main(ok_request)
        assert actual_response.status_code == HTTPStatus.OK
        file_body = actual_response.get_body()
        assert file_body is not None
