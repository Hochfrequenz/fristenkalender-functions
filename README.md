# fristenkalender-functions

This repository provides an HTTP API that exposes the features of [fristenkalender_generator](https://github.com/Hochfrequenz/fristenkalender_generator) and [bdew-datetimes](https://github.com/mj0nez/bdew-datetimes) as a REST API.
It's used by the [fristenkalender-frontend](https://github.com/Hochfrequenz/fristenkalender-frontend) which is deployed to [fristenkalender.hochfrequenz.de](https://fristenkalender.hochfrequenz.de/).

The actual business logic for BDEW calendar calculations (working days, holidays, deadlines) is implemented in the upstream packages: [fristenkalender_generator](https://github.com/Hochfrequenz/fristenkalender_generator) by [Hochfrequenz](https://github.com/Hochfrequenz) and [bdew-datetimes](https://github.com/mj0nez/bdew-datetimes) by [mj0nez](https://github.com/mj0nez).

## Docker Image

A pre-built Docker image is available on GitHub Container Registry:

```bash
docker pull ghcr.io/hochfrequenz/fristenkalender-functions:latest
docker run -p 8000:80 ghcr.io/hochfrequenz/fristenkalender-functions:latest
```

## API Documentation

The API documentation is available at the [`/docs` endpoint (OpenAPI/Swagger UI)](https://fristenkalender-backend.nicebeach-20da7391.germanywestcentral.azurecontainerapps.io/docs).

## Local Setup

Install the dependencies and run the application:

```bash
pip install .
fastapi dev src/app/main.py
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs) to view the API documentation.

## CI/CD
Currently there is no automatic deployment to Azure.
We maintain only 1 environment (prod) in Azure: [Azure Portal fristenkalender-backend Container App](https://portal.azure.com/#@hochfrequenz.net/resource/subscriptions/1cdc65f0-62d2-4770-be11-9ec1da950c81/resourceGroups/fristenkalender/providers/Microsoft.App/containerApps/fristenkalender-backend/containerapp).
