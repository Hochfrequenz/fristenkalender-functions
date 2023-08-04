# we ignore the invalid module name because in this case it's ok that the module/dir has the name of the relative path
# pylint:disable=invalid-name
"""Contains function generating an isc-file for the given year with the given filename and a given attendee"""
import json
import logging
import tempfile
from http import HTTPStatus
from pathlib import Path

import azure.functions as func
from fristenkalender_generator.bdew_calendar_generator import FristenkalenderGenerator


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Function generating an isc-file"""
    try:
        filename = req.route_params.get("filename")
        attendee = req.route_params.get("attendee")
        year_params = req.route_params.get("year")
        if not filename:
            raise ValueError("Filename should not be empty")
        if not attendee:
            raise ValueError("Attendee should not be empty")
        if not year_params:
            raise TypeError("Year should not be empty")
        year = int(year_params)
    except TypeError as type_err:
        logging.warning("Request parameter is invalid: %s", str(type_err))
        return func.HttpResponse(
            body=json.dumps({"error": str(type_err), "code": HTTPStatus.BAD_REQUEST}),
            status_code=HTTPStatus.BAD_REQUEST,
            mimetype="application/json",
        )
    except ValueError as val_error:
        logging.warning("Request parameter is invalid: %s", str(val_error))
        return func.HttpResponse(
            body=json.dumps({"error": str(val_error), "code": HTTPStatus.BAD_REQUEST}),
            status_code=HTTPStatus.BAD_REQUEST,
            mimetype="application/json",
        )
    logging.info(
        "Generating an ics-calendar with this parameters path='%s', attendee='%s' year='%s'",
        filename,
        attendee,
        year,
    )

    try:
        local_ics_file_path: Path
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".ics", delete=False) as tmp_file:
            local_ics_file_path = Path(tmp_file.name)
            FristenkalenderGenerator().generate_and_export_whole_calendar(local_ics_file_path, attendee, year)
        with open(local_ics_file_path, "rb") as ics_file:
            file_body = ics_file.read()
        return func.HttpResponse(
            body=file_body,
            status_code=HTTPStatus.OK,
            mimetype="text/calendar",
        )
    except TypeError as type_error:
        logging.warning("Request parameter was invalid: %s", str(type_error))
        return func.HttpResponse(
            body=json.dumps({"error": str(type_error), "code": HTTPStatus.BAD_REQUEST}),
            status_code=HTTPStatus.BAD_REQUEST,
            mimetype="application/json",
        )
