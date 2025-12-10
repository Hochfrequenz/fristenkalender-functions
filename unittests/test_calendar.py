"""Tests for calendar endpoints."""

from datetime import date
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.calendar import (
    AddDaysResponse,
    IsWorkingDayResponse,
    NextWorkingDayResponse,
    PreviousWorkingDayResponse,
)

client = TestClient(app)


class TestIsWorkingDay:
    @pytest.mark.parametrize(
        "date_str,expected_is_working_day",
        [
            pytest.param("2024-01-02", True, id="tuesday"),
            pytest.param("2024-01-06", False, id="saturday"),
            pytest.param("2024-01-07", False, id="sunday"),
            pytest.param("2024-12-25", False, id="christmas"),
        ],
    )
    def test_is_working_day(self, date_str: str, expected_is_working_day: bool):
        response = client.get(f"/api/IsWorkingDay/{date_str}")
        assert response.status_code == HTTPStatus.OK
        result = IsWorkingDayResponse.model_validate(response.json())
        assert result.date == date.fromisoformat(date_str)
        assert result.is_working_day == expected_is_working_day

    def test_invalid_date(self):
        response = client.get("/api/IsWorkingDay/invalid")
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


class TestNextWorkingDay:
    @pytest.mark.parametrize(
        "date_str,expected_next",
        [
            pytest.param("2024-01-05", "2024-01-08", id="friday_to_monday"),
            pytest.param("2024-01-02", "2024-01-03", id="tuesday_to_wednesday"),
        ],
    )
    def test_next_working_day(self, date_str: str, expected_next: str):
        response = client.get(f"/api/NextWorkingDay/{date_str}")
        assert response.status_code == HTTPStatus.OK
        result = NextWorkingDayResponse.model_validate(response.json())
        assert result.start_date == date.fromisoformat(date_str)
        assert result.next_working_day == date.fromisoformat(expected_next)


class TestPreviousWorkingDay:
    @pytest.mark.parametrize(
        "date_str,expected_prev",
        [
            pytest.param("2024-01-08", "2024-01-05", id="monday_to_friday"),
            pytest.param("2024-01-03", "2024-01-02", id="wednesday_to_tuesday"),
        ],
    )
    def test_previous_working_day(self, date_str: str, expected_prev: str):
        response = client.get(f"/api/PreviousWorkingDay/{date_str}")
        assert response.status_code == HTTPStatus.OK
        result = PreviousWorkingDayResponse.model_validate(response.json())
        assert result.start_date == date.fromisoformat(date_str)
        assert result.previous_working_day == date.fromisoformat(expected_prev)


class TestAddWorkingDays:
    def test_add_working_days(self):
        response = client.get("/api/AddWorkingDays/2024-01-02/5")
        assert response.status_code == HTTPStatus.OK
        result = AddDaysResponse.model_validate(response.json())
        assert result.start_date == date(2024, 1, 2)
        assert result.number_of_days == 5
        assert result.day_type == "working_day"
        assert result.end_date_type == "exclusive"

    def test_add_working_days_inclusive(self):
        response = client.get("/api/AddWorkingDays/2024-01-02/5?end_date_type=inclusive")
        assert response.status_code == HTTPStatus.OK
        result = AddDaysResponse.model_validate(response.json())
        assert result.end_date_type == "inclusive"


class TestAddCalendarDays:
    def test_add_calendar_days(self):
        response = client.get("/api/AddCalendarDays/2024-01-02/10")
        assert response.status_code == HTTPStatus.OK
        result = AddDaysResponse.model_validate(response.json())
        assert result.start_date == date(2024, 1, 2)
        assert result.number_of_days == 10
        assert result.day_type == "calendar_day"
        assert result.result_date == date(2024, 1, 13)

    def test_add_calendar_days_inclusive(self):
        response = client.get("/api/AddCalendarDays/2024-01-02/10?end_date_type=inclusive")
        assert response.status_code == HTTPStatus.OK
        result = AddDaysResponse.model_validate(response.json())
        assert result.end_date_type == "inclusive"
