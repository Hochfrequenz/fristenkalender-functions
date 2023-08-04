# we ignore the invalid module name because in this case it's ok that the module/dir has the name of the relative path
# pylint:disable=invalid-name
"""Contains function generating all fristen for a given type and a given year"""
import json
import logging
from http import HTTPStatus

import azure.functions as func
from fristenkalender_generator.bdew_calendar_generator import FristenkalenderGenerator, FristenType


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Function generating all fristen for a given type and a given year"""
    try:
        fristen_type_params = req.route_params.get("fristen_type")
        year_params = req.route_params.get("year")

        if isinstance(fristen_type_params, str) and len(fristen_type_params) != 0:
            fristen_type = FristenType(fristen_type_params.upper())
        else:
            raise ValueError("Fristen type should not be empty")
        if not year_params:
            raise TypeError("Year should not be empty")
        year = int(year_params)

    except ValueError as value_error:
        logging.warning("Request parameter is invalid: %s", str(value_error))
        return func.HttpResponse(
            body=json.dumps({"error": str(value_error), "code": HTTPStatus.BAD_REQUEST}),
            status_code=HTTPStatus.BAD_REQUEST,
            mimetype="application/json",
        )
    except TypeError as type_error:
        logging.warning("Request parametr is invalid: %s", str(type_error))
        return func.HttpResponse(
            body=json.dumps({"error": str(type_error), "code": HTTPStatus.BAD_REQUEST}),
            status_code=HTTPStatus.BAD_REQUEST,
            mimetype="application/json",
        )

    fristen_with_type = FristenkalenderGenerator().generate_fristen_for_type(year, fristen_type)
    fristen_with_type_json = json.dumps(fristen_with_type, indent=4, sort_keys=True, default=str)
    return func.HttpResponse(body=fristen_with_type_json, status_code=HTTPStatus.OK, mimetype="application/json")
