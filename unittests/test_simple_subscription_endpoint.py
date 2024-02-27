from http import HTTPStatus

import azure.functions as func
import pytest  # type:ignore[import]

from SimpleCalenderEndpoint import main  # type:ignore[import]


class TestSimpleCalenderEndpoint:
    @pytest.mark.parametrize(
        "ok_request",
        [
            pytest.param(
                func.HttpRequest(
                    "GET", "testhost", body=bytes()
                )
            ),
        ],
    )
    def test_ok_get(self, ok_request: func.HttpRequest):
        actual_response = main(ok_request)
        assert actual_response.status_code == HTTPStatus.OK

        # Check for Content-Type header
        assert actual_response.headers.get("Content-Type") == "text/calendar; charset=utf-8"

        file_body = actual_response.get_body().decode("utf-8")
        assert file_body is not None

        # Basic iCalendar format validation
        assert file_body.startswith("BEGIN:VCALENDAR")
        assert "BEGIN:VEVENT" in file_body
        assert file_body.endswith("END:VCALENDAR\r\n")


