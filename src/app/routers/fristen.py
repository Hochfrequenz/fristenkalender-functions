"""Router for fristen endpoints."""
import dataclasses
import json
import logging
import tempfile
from http import HTTPStatus
from pathlib import Path as FilePath

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import FileResponse, JSONResponse
from fristenkalender_generator.bdew_calendar_generator import FristenkalenderGenerator, FristenType
from starlette.background import BackgroundTask

router = APIRouter(prefix="/api")


@router.get("/GenerateAllFristen/{year}")
def generate_all_fristen(year: int = Path(..., description="Year to generate fristen for")):
    """Generate all fristen for a given year."""
    logging.info("Generating all fristen for year='%s'", year)

    try:
        all_fristen = FristenkalenderGenerator().generate_all_fristen(year)
        all_fristen_serialized = [dataclasses.asdict(x) for x in all_fristen]
        return JSONResponse(
            content=json.loads(json.dumps(all_fristen_serialized, indent=4, sort_keys=True, default=str)),
            status_code=HTTPStatus.OK,
        )
    except (TypeError, ValueError) as error:
        logging.warning("Request parameter is invalid: %s", str(error))
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(error))


@router.get("/GenerateFristenForType/{year}/{fristen_type}")
def generate_fristen_for_type(
    year: int = Path(..., description="Year to generate fristen for"),
    fristen_type: str = Path(..., description="Type of fristen (e.g., GPKE)"),
):
    """Generate fristen for a given type and year."""
    try:
        if not fristen_type:
            raise ValueError("Fristen type should not be empty")
        fristen_type_enum = FristenType(fristen_type.upper())
    except ValueError as error:
        logging.warning("Request parameter is invalid: %s", str(error))
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(error))

    fristen_with_type = FristenkalenderGenerator().generate_fristen_for_type(year, fristen_type_enum)
    fristen_serialized = [dataclasses.asdict(x) for x in fristen_with_type]
    return JSONResponse(
        content=json.loads(json.dumps(fristen_serialized, indent=4, sort_keys=True, default=str)),
        status_code=HTTPStatus.OK,
    )


@router.get("/GenerateAndExportWholeCalendar/{filename}/{attendee}/{year}")
def generate_and_export_whole_calendar(
    filename: str = Path(..., description="Filename for the ICS file (without extension)"),
    attendee: str = Path(..., description="Email address of the attendee"),
    year: int = Path(..., description="Year to generate calendar for"),
):
    """Generate an ICS file for the whole calendar for a given year."""
    logging.info(
        "Generating an ics-calendar with parameters path='%s', attendee='%s' year='%s'",
        filename,
        attendee,
        year,
    )

    try:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".ics", delete=False) as tmp_file:
            local_ics_file_path = FilePath(tmp_file.name)
            FristenkalenderGenerator().generate_and_export_whole_calendar(local_ics_file_path, attendee, year)

        return FileResponse(
            path=local_ics_file_path,
            filename=f"{filename}.ics",
            media_type="text/calendar",
            background=BackgroundTask(lambda: local_ics_file_path.unlink()),
        )
    except TypeError as error:
        logging.warning("Request parameter was invalid: %s", str(error))
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(error))
