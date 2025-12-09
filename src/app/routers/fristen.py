"""Router for fristen endpoints."""
import dataclasses
import json
import logging
from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse
from fristenkalender_generator.bdew_calendar_generator import FristenkalenderGenerator

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
