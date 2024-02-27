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
    year = 2024
    attendee = "test@attandee.de"
    local_ics_file_path: Path
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".ics", delete=False) as tmp_file:
        local_ics_file_path = Path(tmp_file.name)
        FristenkalenderGenerator().generate_and_export_whole_calendar(local_ics_file_path, attendee, year)
        tmp_file.seek(0)  # Go back to the beginning of the file to read the content
        file_body = ics_file.read()
    return func.HttpResponse(
        body=file_body,
        status_code=HTTPStatus.OK,
        mimetype="text/calendar",
    )
