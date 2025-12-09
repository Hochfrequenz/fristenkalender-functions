# Azure Functions to FastAPI Migration

## Overview

Migrate from Azure Functions to a FastAPI application for simpler deployment, better local development, portability, and improved OpenAPI documentation.

## Project Structure

```
fristenkalender-functions/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI app, health endpoint
│       └── routers/
│           ├── __init__.py
│           └── fristen.py       # All 4 frist endpoints
├── Dockerfile
├── unittests/
│   └── ...
├── tox.ini
├── pyproject.toml
└── src/requirements.txt         # Pinned dependencies (keep)
```

## API Endpoints

### Health endpoint
```
GET /health  →  {"status": "healthy"}
```

### Fristen endpoints (identical to current)

| Method | Path | Query Params | Response |
|--------|------|--------------|----------|
| GET | `/api/GenerateAllFristen/{year}` | `?concise=True` (optional) | JSON list |
| GET | `/api/GenerateFristenForType/{year}/{type}` | - | JSON list |
| GET | `/api/GenerateAndExportWholeCalendar/{filename}/{email}/{year}` | - | ICS file |
| GET | `/api/GenerateAndExportFristenForType/{filename}/{email}/{year}/{type}` | - | ICS file |

### OpenAPI docs (FastAPI built-in)
- `/docs` - Swagger UI
- `/redoc` - ReDoc

## Dockerfile

```dockerfile
FROM python:3.14-slim

WORKDIR /code

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/

EXPOSE 80

CMD ["fastapi", "run", "src/app/main.py", "--port", "80", "--forwarded-allow-ips", "*"]
```

## Files to Remove

- `src/GenerateAllFristen/` (folder)
- `src/GenerateFristenForType/` (folder)
- `src/GenerateAndExportWholeCalendar/` (folder)
- `src/GenerateAndExportFristenForType/` (folder)
- `src/host.json`
- `src/local.settings.json`
- `setup.py`
- `.github/workflows/main_fristenkalender.yml`

## Files to Keep

- `src/requirements.txt` (pinned dependencies)
- `unittests/` (update imports)
- `tox.ini`

## CI/CD - GHCR Publish

New file: `.github/workflows/publish-ghcr.yml`

Triggers on release creation, builds Docker image, pushes to `ghcr.io/hochfrequenz/fristenkalender-functions` with version tag and `latest`.

Requires `GHCR_PUSH_TOKEN` secret.

## Testing

- Update imports in `unittests/` to use new `src/app/` structure
- Use FastAPI's `TestClient` instead of Azure Functions test utilities
- Keep `tox.ini` for running tests, linting, type checking

## Local Development

```bash
# Run locally
fastapi dev src/app/main.py

# Run tests
tox
```
