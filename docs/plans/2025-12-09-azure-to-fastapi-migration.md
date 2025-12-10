# Azure Functions to FastAPI Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate from Azure Functions to a FastAPI application with Docker deployment to GHCR.

**Architecture:** Single FastAPI app with one router for all fristen endpoints. Health endpoint at root level. Docker container runs behind reverse proxy with forwarded headers enabled.

**Tech Stack:** FastAPI, Uvicorn, Python 3.14, Docker, fristenkalender-generator

---

## Task 1: Create FastAPI App Structure

**Files:**
- Create: `src/app/__init__.py`
- Create: `src/app/main.py`
- Create: `src/app/routers/__init__.py`
- Create: `src/app/routers/fristen.py`

**Step 1: Create empty `__init__.py` files**

```python
# src/app/__init__.py
# empty file
```

```python
# src/app/routers/__init__.py
# empty file
```

**Step 2: Create `src/app/main.py` with health endpoint**

```python
"""FastAPI application for Fristenkalender."""
from fastapi import FastAPI

from app.routers import fristen

app = FastAPI(
    title="Fristenkalender API",
    description="API for generating BDEW Fristenkalender deadlines",
)

app.include_router(fristen.router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}
```

**Step 3: Create `src/app/routers/fristen.py` with placeholder**

```python
"""Router for fristen endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/api")
```

**Step 4: Verify structure exists**

Run: `ls src/app/ && ls src/app/routers/`
Expected: Shows `__init__.py`, `main.py`, and `routers/` with `__init__.py`, `fristen.py`

**Step 5: Commit**

```bash
git add src/app/
git commit -m "feat: add FastAPI app structure with health endpoint"
```

---

## Task 2: Implement GenerateAllFristen Endpoint

**Files:**
- Modify: `src/app/routers/fristen.py`

**Step 1: Add GenerateAllFristen endpoint**

Replace `src/app/routers/fristen.py` with:

```python
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
```

**Step 2: Commit**

```bash
git add src/app/routers/fristen.py
git commit -m "feat: add GenerateAllFristen endpoint"
```

---

## Task 3: Implement GenerateFristenForType Endpoint

**Files:**
- Modify: `src/app/routers/fristen.py`

**Step 1: Add imports and endpoint**

Add to imports at top of `src/app/routers/fristen.py`:

```python
from fristenkalender_generator.bdew_calendar_generator import FristenkalenderGenerator, FristenType
```

(Update the existing import line to include `FristenType`)

Add endpoint after `generate_all_fristen`:

```python
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
```

**Step 2: Commit**

```bash
git add src/app/routers/fristen.py
git commit -m "feat: add GenerateFristenForType endpoint"
```

---

## Task 4: Implement GenerateAndExportWholeCalendar Endpoint

**Files:**
- Modify: `src/app/routers/fristen.py`

**Step 1: Add imports**

Add to imports at top of `src/app/routers/fristen.py`:

```python
import tempfile
from pathlib import Path as FilePath

from fastapi.responses import FileResponse
```

**Step 2: Add endpoint**

Add endpoint after `generate_fristen_for_type`:

```python
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
        )
    except TypeError as error:
        logging.warning("Request parameter was invalid: %s", str(error))
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(error))
```

**Step 3: Commit**

```bash
git add src/app/routers/fristen.py
git commit -m "feat: add GenerateAndExportWholeCalendar endpoint"
```

---

## Task 5: Implement GenerateAndExportFristenForType Endpoint

**Files:**
- Modify: `src/app/routers/fristen.py`

**Step 1: Add endpoint**

Add endpoint after `generate_and_export_whole_calendar`:

```python
@router.get("/GenerateAndExportFristenForType/{filename}/{attendee}/{year}/{fristen_type}")
def generate_and_export_fristen_for_type(
    filename: str = Path(..., description="Filename for the ICS file (without extension)"),
    attendee: str = Path(..., description="Email address of the attendee"),
    year: int = Path(..., description="Year to generate calendar for"),
    fristen_type: str = Path(..., description="Type of fristen (e.g., GPKE)"),
):
    """Generate an ICS file for fristen of a given type for a given year."""
    try:
        if not fristen_type:
            raise ValueError("Fristen type should not be empty")
        fristen_type_enum = FristenType(fristen_type.upper())
    except ValueError as error:
        logging.warning("Request parameter is invalid: %s", str(error))
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(error))

    logging.info(
        "Generating an ics-calendar with parameters path='%s', attendee='%s' year='%s' fristen_type='%s'",
        filename,
        attendee,
        year,
        fristen_type_enum,
    )

    try:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".ics", delete=False) as tmp_file:
            local_ics_file_path = FilePath(tmp_file.name)
            FristenkalenderGenerator().generate_and_export_fristen_for_type(
                local_ics_file_path, attendee, year, fristen_type_enum
            )

        return FileResponse(
            path=local_ics_file_path,
            filename=f"{filename}.ics",
            media_type="text/calendar",
        )
    except TypeError as error:
        logging.warning("Request parameter was invalid: %s", str(error))
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(error))
```

**Step 2: Commit**

```bash
git add src/app/routers/fristen.py
git commit -m "feat: add GenerateAndExportFristenForType endpoint"
```

---

## Task 6: Update pyproject.toml with FastAPI Dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Update dependencies and Python version**

In `pyproject.toml`, update:

```toml
requires-python = ">=3.14"
```

Update classifiers to include Python 3.14:

```toml
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.14",
]
```

Add production dependencies:

```toml
dependencies = [
    "fastapi",
    "fristenkalender-generator",
]
```

Add to optional-dependencies:

```toml
[project.optional-dependencies]
tests = [
    "pytest==9.0.2",
    "httpx",
]
```

Update black/isort targets:

```toml
[tool.black]
line-length = 120
target_version = ["py314"]

[tool.isort]
line_length = 120
profile = "black"
```

Update hatch wheel config to include the app:

```toml
[tool.hatch.build.targets.wheel]
only-include = ["src/app"]
sources = ["src"]
```

**Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "build: update pyproject.toml for FastAPI"
```

---

## Task 7: Create Dockerfile

**Files:**
- Create: `Dockerfile`

**Step 1: Create Dockerfile**

```dockerfile
FROM python:3.14-slim

WORKDIR /code

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/

EXPOSE 80

CMD ["fastapi", "run", "src/app/main.py", "--port", "80", "--forwarded-allow-ips", "*"]
```

**Step 2: Commit**

```bash
git add Dockerfile
git commit -m "build: add Dockerfile for FastAPI app"
```

---

## Task 8: Create GHCR Publish Workflow

**Files:**
- Create: `.github/workflows/publish-ghcr.yml`

**Step 1: Create workflow file**

```yaml
name: Publish Docker image to Github Container Registry GHCR
on:
  release:
    types:
      - created

jobs:
  push_to_registry:
    name: Push Docker image to GHCR
    runs-on: ubuntu-latest

    steps:
      - name: Check out the repo
        uses: actions/checkout@v6
      - name: get version tag
        run: |
          VERSION=$(echo ${GITHUB_REF#refs/tags/})
          echo "VERSION=$VERSION" >> $GITHUB_ENV
      - name: Log in to GHCR
        run: echo "${{ secrets.GHCR_PUSH_TOKEN }}" | docker login ghcr.io -u hf-kklein --password-stdin

      - name: Build and push
        run: |
          docker build -t fristenkalender-functions:$VERSION .
          docker tag fristenkalender-functions:$VERSION ghcr.io/hochfrequenz/fristenkalender-functions:$VERSION
          docker tag fristenkalender-functions:$VERSION ghcr.io/hochfrequenz/fristenkalender-functions:latest
          docker push ghcr.io/hochfrequenz/fristenkalender-functions:$VERSION
          docker push ghcr.io/hochfrequenz/fristenkalender-functions:latest
```

**Step 2: Commit**

```bash
git add .github/workflows/publish-ghcr.yml
git commit -m "ci: add GHCR publish workflow"
```

---

## Task 9: Update Unit Tests for FastAPI

**Files:**
- Modify: `unittests/test_generate_all_fristen.py`
- Modify: `unittests/test_generate_fristen_for_type.py`
- Modify: `unittests/test_generate_and_export_whole_calendar.py`
- Modify: `unittests/test_generate_and_export_fristen_for_type.py`

**Step 1: Update `unittests/test_generate_all_fristen.py`**

```python
import json
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateAllFristen:
    @pytest.mark.parametrize(
        "year",
        [
            pytest.param("2023"),
        ],
    )
    def test_ok_get(self, year: str):
        response = client.get(f"/api/GenerateAllFristen/{year}")
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert isinstance(body, list)
        assert not isinstance(body[0], str)
        assert all(isinstance(x, dict) for x in body)

    @pytest.mark.parametrize(
        "year",
        [
            pytest.param("hhhh"),
            pytest.param("0"),
        ],
    )
    def test_bad_request(self, year: str):
        response = client.get(f"/api/GenerateAllFristen/{year}")
        assert response.status_code == HTTPStatus.BAD_REQUEST
```

**Step 2: Update `unittests/test_generate_fristen_for_type.py`**

```python
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateFristenForType:
    def test_ok_get(self):
        response = client.get("/api/GenerateFristenForType/2023/GPKE")
        assert response.status_code == HTTPStatus.OK
        actual_fristen_list = response.json()
        actual_frist = actual_fristen_list[0]
        expected = {
            "date": "2022-12-28",
            "description": "Letzter Termin Anmeldung asynchrone Bilanzierung (Strom)",
            "fristen_type": "FristenType.GPKE",
            "label": "3LWT",
            "ref_not_in_the_same_month": None,
        }
        assert actual_frist == expected

    @pytest.mark.parametrize(
        "year,fristen_type,expected_length",
        [
            pytest.param("2025", "GPKE", 6, id="No GPKE 3LWT Fristen after 24h LFW (June 2025)"),
            pytest.param("2026", "GPKE", 0),
        ],
    )
    def test_non_empty_get(self, year: str, fristen_type: str, expected_length: int):
        response = client.get(f"/api/GenerateFristenForType/{year}/{fristen_type}")
        assert response.status_code == HTTPStatus.OK
        actual = response.json()
        assert len(actual) == expected_length

    @pytest.mark.parametrize(
        "year,fristen_type",
        [
            pytest.param("2023", "hhhhhh"),
        ],
    )
    def test_bad_request(self, year: str, fristen_type: str):
        response = client.get(f"/api/GenerateFristenForType/{year}/{fristen_type}")
        assert response.status_code == HTTPStatus.BAD_REQUEST
```

**Step 3: Update `unittests/test_generate_and_export_whole_calendar.py`**

```python
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateAndExportWholeCalendar:
    @pytest.mark.parametrize(
        "filename,attendee,year",
        [
            pytest.param("", "bar", "2023"),
            pytest.param("foo", "", "2023"),
            pytest.param("foo", "bar", "hghhkjhkj"),
        ],
    )
    def test_bad_request(self, filename: str, attendee: str, year: str):
        response = client.get(f"/api/GenerateAndExportWholeCalendar/{filename}/{attendee}/{year}")
        assert response.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND, HTTPStatus.UNPROCESSABLE_ENTITY)

    def test_ok_get(self):
        response = client.get("/api/GenerateAndExportWholeCalendar/foo/bar/2023")
        assert response.status_code == HTTPStatus.OK
        file_body = response.content
        assert file_body is not None
        assert len(file_body) > 0
```

**Step 4: Update `unittests/test_generate_and_export_fristen_for_type.py`**

```python
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGenerateAndExportFristenForType:
    @pytest.mark.parametrize(
        "filename,attendee,year,fristen_type",
        [
            pytest.param("foo", "bar", "2023", "invalid_type"),
        ],
    )
    def test_bad_request(self, filename: str, attendee: str, year: str, fristen_type: str):
        response = client.get(f"/api/GenerateAndExportFristenForType/{filename}/{attendee}/{year}/{fristen_type}")
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_ok_get(self):
        response = client.get("/api/GenerateAndExportFristenForType/foo/bar/2023/GPKE")
        assert response.status_code == HTTPStatus.OK
        file_body = response.content
        assert file_body is not None
        assert len(file_body) > 0
```

**Step 5: Commit**

```bash
git add unittests/
git commit -m "test: update unit tests for FastAPI TestClient"
```

---

## Task 10: Remove Azure Functions Files

**Files:**
- Delete: `src/GenerateAllFristen/` (entire folder)
- Delete: `src/GenerateFristenForType/` (entire folder)
- Delete: `src/GenerateAndExportWholeCalendar/` (entire folder)
- Delete: `src/GenerateAndExportFristenForType/` (entire folder)
- Delete: `src/host.json`
- Delete: `src/local.settings.json`
- Delete: `setup.py`
- Delete: `.github/workflows/main_fristenkalender.yml`

**Step 1: Delete Azure Functions folders and files**

```bash
rm -rf src/GenerateAllFristen/
rm -rf src/GenerateFristenForType/
rm -rf src/GenerateAndExportWholeCalendar/
rm -rf src/GenerateAndExportFristenForType/
rm -f src/host.json
rm -f src/local.settings.json
rm -f setup.py
rm -f .github/workflows/main_fristenkalender.yml
```

**Step 2: Commit**

```bash
git add -A
git commit -m "chore: remove Azure Functions structure"
```

---

## Task 11: Update tox.ini for FastAPI

**Files:**
- Modify: `tox.ini`

**Step 1: Update tox.ini**

Update the `PYTHONPATH` to include `src` so that `app` module can be imported:

In the `[testenv]` section, add or update:

```ini
setenv =
    PYTHONPATH = {toxinidir}/src
```

Ensure the deps include `httpx` for FastAPI TestClient:

```ini
deps =
    .[tests]
    httpx
```

**Step 2: Run tests to verify**

Run: `tox -e dev -- pytest unittests/ -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tox.ini
git commit -m "build: update tox.ini for FastAPI tests"
```

---

## Task 12: Final Verification

**Step 1: Run all tests**

Run: `tox`
Expected: All tests pass, linting passes

**Step 2: Test local FastAPI dev server**

Run: `fastapi dev src/app/main.py`
Expected: Server starts, accessible at http://localhost:8000

**Step 3: Test endpoints manually**

- http://localhost:8000/health → `{"status": "healthy"}`
- http://localhost:8000/docs → Swagger UI
- http://localhost:8000/api/GenerateAllFristen/2023 → JSON list

**Step 4: Test Docker build**

Run: `docker build -t fristenkalender-functions:test .`
Expected: Build succeeds

**Step 5: Final commit if any cleanup needed**

```bash
git add -A
git commit -m "chore: final cleanup for FastAPI migration"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Create FastAPI app structure |
| 2 | Implement GenerateAllFristen |
| 3 | Implement GenerateFristenForType |
| 4 | Implement GenerateAndExportWholeCalendar |
| 5 | Implement GenerateAndExportFristenForType |
| 6 | Update pyproject.toml |
| 7 | Create Dockerfile |
| 8 | Create GHCR workflow |
| 9 | Update unit tests |
| 10 | Remove Azure Functions files |
| 11 | Update tox.ini |
| 12 | Final verification |
