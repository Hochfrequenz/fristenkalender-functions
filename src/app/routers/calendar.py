"""Router for BDEW calendar/working day endpoints."""

from datetime import date
from typing import Annotated, Literal

from bdew_datetimes.enums import DayType, EndDateType
from bdew_datetimes.models import Period
from bdew_datetimes.periods import (
    add_frist,
    get_next_working_day,
    get_previous_working_day,
    is_bdew_working_day,
)
from fastapi import APIRouter, Path, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api")


class IsWorkingDayResponse(BaseModel):
    """Response model for IsWorkingDay endpoint."""

    date: date
    is_working_day: bool


class NextWorkingDayResponse(BaseModel):
    """Response model for NextWorkingDay endpoint."""

    start_date: date
    next_working_day: date


class PreviousWorkingDayResponse(BaseModel):
    """Response model for PreviousWorkingDay endpoint."""

    start_date: date
    previous_working_day: date


class AddDaysResponse(BaseModel):
    """Response model for AddWorkingDays and AddCalendarDays endpoints."""

    start_date: date
    number_of_days: int
    day_type: Literal["working_day", "calendar_day"]
    end_date_type: Literal["inclusive", "exclusive"]
    result_date: date


@router.get("/IsWorkingDay/{check_date}")
def check_is_working_day(
    check_date: Annotated[date, Path(..., description="Date to check")],
) -> IsWorkingDayResponse:
    """Check if a given date is a BDEW working day."""
    return IsWorkingDayResponse(date=check_date, is_working_day=is_bdew_working_day(check_date))


@router.get("/NextWorkingDay/{start_date}")
def get_next_working_day_endpoint(
    start_date: Annotated[date, Path(..., description="Start date")],
) -> NextWorkingDayResponse:
    """Get the next BDEW working day after the given date."""
    return NextWorkingDayResponse(start_date=start_date, next_working_day=get_next_working_day(start_date))


@router.get("/PreviousWorkingDay/{start_date}")
def get_previous_working_day_endpoint(
    start_date: Annotated[date, Path(..., description="Start date")],
) -> PreviousWorkingDayResponse:
    """Get the previous BDEW working day before the given date."""
    return PreviousWorkingDayResponse(start_date=start_date, previous_working_day=get_previous_working_day(start_date))


@router.get("/AddWorkingDays/{start_date}/{number_of_days}")
def add_working_days_endpoint(
    start_date: Annotated[date, Path(..., description="Start date")],
    number_of_days: Annotated[int, Path(..., description="Number of working days to add")],
    end_date_type: Annotated[
        Literal["inclusive", "exclusive"],
        Query(description="Whether the end date is inclusive or exclusive"),
    ] = "exclusive",
) -> AddDaysResponse:
    """Add a number of BDEW working days to a given date."""
    end_type = EndDateType.INCLUSIVE if end_date_type == "inclusive" else EndDateType.EXCLUSIVE
    period = Period(number_of_days=number_of_days, day_type=DayType.WORKING_DAY, end_date_type=end_type)
    result_date = add_frist(start_date, period)
    return AddDaysResponse(
        start_date=start_date,
        number_of_days=number_of_days,
        day_type="working_day",
        end_date_type=end_date_type,
        result_date=result_date,
    )


@router.get("/AddCalendarDays/{start_date}/{number_of_days}")
def add_calendar_days_endpoint(
    start_date: Annotated[date, Path(..., description="Start date")],
    number_of_days: Annotated[int, Path(..., description="Number of calendar days to add")],
    end_date_type: Annotated[
        Literal["inclusive", "exclusive"],
        Query(description="Whether the end date is inclusive or exclusive"),
    ] = "exclusive",
) -> AddDaysResponse:
    """Add a number of calendar days to a given date."""
    end_type = EndDateType.INCLUSIVE if end_date_type == "inclusive" else EndDateType.EXCLUSIVE
    period = Period(number_of_days=number_of_days, day_type=DayType.CALENDAR_DAY, end_date_type=end_type)
    result_date = add_frist(start_date, period)
    return AddDaysResponse(
        start_date=start_date,
        number_of_days=number_of_days,
        day_type="calendar_day",
        end_date_type=end_date_type,
        result_date=result_date,
    )
