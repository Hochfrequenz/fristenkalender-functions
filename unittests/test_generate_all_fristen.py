import json
from http import HTTPStatus

import azure.functions as func
import pytest  # type:ignore[import]

from GenerateAllFristen import main  # type:ignore[import]


class TestGenerateAllFristen:
    @pytest.mark.parametrize(
        "ok_request",
        [
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateAllFristen",
                    route_params={"year": "2023"},
                    body=bytes(),
                )
            ),
        ],
    )
    def test_ok_get(self, ok_request: func.HttpRequest):
        actual_response = main(ok_request)
        assert actual_response.status_code == HTTPStatus.OK
        body = actual_response.get_body()
        assert body is not None
        deserialized_body = json.loads(body)
        assert isinstance(deserialized_body, list)
        assert not isinstance(
            deserialized_body[0], str
        )  # should not be the python object __str__ "FristWithAttributes(date=datetime.date(2022, 12, 1), label='21WT', ref_not_in_the_same_month=10, description='NKP (VNB ⟶ MGV)')"
        assert all(
            isinstance(x, dict) for x in deserialized_body
        )  # should not be the python object __str__ "FristWithAttributes(date=datetime.date(2022, 12, 1), label='21WT', ref_not_in_the_same_month=10, description='NKP (VNB ⟶ MGV)')"

    @pytest.mark.parametrize(
        "bad_request",
        [
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateAllFristen",
                    route_params={"year": "hhhh"},
                    body=bytes(),
                )
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateAllFristen",
                    route_params={"year": "0"},
                    body=bytes(),
                )
            ),
            pytest.param(
                func.HttpRequest(
                    "GET",
                    "testhost/GenerateAllFristen",
                    route_params={},
                    body=bytes(),
                )
            ),
        ],
    )
    def test_bad_request(self, bad_request: func.HttpRequest):
        actual_response = main(bad_request)
        assert actual_response.status_code == HTTPStatus.BAD_REQUEST
