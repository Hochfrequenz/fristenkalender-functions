import json
import logging
from http import HTTPStatus

import azure.functions as func
from fristenkalender_generator.bdew_calendar_generator import (
    FristenkalenderGenerator,
    FristenType,
    FristWithAttributes,
    FristWithAttributesAndType,
)


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        fristen_type_url = req.route_params.get("fristen_type")
        if type(fristen_type_url) == str and len(fristen_type_url) != 0:
            fristen_type = FristenType(fristen_type_url.upper())
        elif fristen_type_url is None:
            raise ValueError("Just don't")
        else:
            raise ValueError("Don't do this")

    except ValueError as value_error:
        logging.warning("Request parametr is invalid: %s", str(value_error))
        return func.HttpResponse(
            body=json.dumps({"error": str(value_error), "code": HTTPStatus.BAD_REQUEST}),
            status_code=HTTPStatus.BAD_REQUEST,
            mimetype="application/json",
        )

    # try:
    fristen_with_type = FristenkalenderGenerator().generate_fristen_for_type(2023, fristen_type)
    fristen_with_type_json = json.dumps(fristen_with_type, indent=4, sort_keys=True, default=str)
    return func.HttpResponse(body=fristen_with_type_json, status_code=HTTPStatus.OK, mimetype="application/json")
    # except TypeError:
    #     logging.warning("Fristen type (%s) not found", fristen_type)
    #     return func.HttpResponse(
    #         body=json.dumps(
    #             {
    #                 "error": f"fristen type ({fristen_type}) not found",
    #                 "code": HTTPStatus.NOT_FOUND,
    #             }
    #         ),
    #         status_code=HTTPStatus.NOT_FOUND,
    #         mimetype="application/json"
    #     )
