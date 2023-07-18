# we ignore the invalid module name because in this case it's ok that the module/dir has the name of the relative path
# pylint:disable=invalid-name
"""Contains function generating all fristen for the given year"""
import json
import logging
from http import HTTPStatus

import azure.functions as func
from fristenkalender_generator.bdew_calendar_generator import FristenkalenderGenerator


def main(req: func.HttpRequest) -> func.HttpResponse:
    """function generating all fristen for the given year"""
    try:
        year_params = req.route_params.get("year")
        if not year_params:
            raise ValueError("Year should not be empty")
        year = int(year_params)
        if not year_params.isnumeric():
            raise ValueError(f"Parametr '{year_params}' is not numeric")

    except ValueError as value_error:
        # parsing the strings to their enum value may raise a value error
        logging.warning("Request param was invalid: %s", str(value_error))
        return func.HttpResponse(
            body=json.dumps({"error": str(value_error), "code": HTTPStatus.BAD_REQUEST}),
            status_code=HTTPStatus.BAD_REQUEST,
            mimetype="application/json",
        )

    logging.info(
        "Generating all fristen for a given year='%s'",
        year,
    )

    try:
        all_fristen = FristenkalenderGenerator().generate_all_fristen(year)
        all_fristen_json = json.dumps(all_fristen, indent=4, sort_keys=True, default=str)
        return func.HttpResponse(
            body=all_fristen_json,
            status_code=HTTPStatus.OK,
            mimetype="application/json",
        )
    except TypeError as type_error:
        logging.warning("Request param is invalid: %s", str(type_error))
        return func.HttpResponse(
            body=json.dumps({"error": str(type_error), "code": HTTPStatus.BAD_REQUEST}),
            status_code=HTTPStatus.BAD_REQUEST,
            mimetype="application/json",
        )
    except ValueError as value_error:
        logging.warning("Param is out of range: %s", str(value_error))
        return func.HttpResponse(
            body=json.dumps({"error": str(value_error), "code": HTTPStatus.BAD_REQUEST}),
            status_code=HTTPStatus.BAD_REQUEST,
            mimetype="application/json",
        )
