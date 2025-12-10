# fristenkalender-functions

This repository provides an HTTP API that exposes the features of [fristenkalender_generator](https://github.com/Hochfrequenz/fristenkalender_generator) and [bdew-datetimes](https://github.com/mj0nez/bdew-datetimes) as a REST API.
It's used by the [fristenkalender-frontend](https://github.com/Hochfrequenz/fristenkalender-frontend) which is deployed to [fristenkalender.hochfrequenz.de](https://fristenkalender.hochfrequenz.de/).

The actual business logic for BDEW calendar calculations (working days, holidays, deadlines) is implemented in the upstream packages: [fristenkalender_generator](https://github.com/Hochfrequenz/fristenkalender_generator) by [Hochfrequenz](https://github.com/Hochfrequenz) and [bdew-datetimes](https://github.com/mj0nez/bdew-datetimes) by [mj0nez](https://github.com/mj0nez).

## Docker Image

A pre-built Docker image is publicly available on the [GitHub Container Registry](https://github.com/Hochfrequenz/fristenkalender-functions/pkgs/container/fristenkalender-functions):

```bash
docker pull ghcr.io/hochfrequenz/fristenkalender-functions:latest
docker run -p 8000:80 ghcr.io/hochfrequenz/fristenkalender-functions:latest
```

## API Documentation

The API documentation is available at the [`/docs` endpoint (OpenAPI/Swagger UI)](https://fristenkalender-api.happyfield-64ecc075.westeurope.azurecontainerapps.io/docs).

## Local Setup

Install the dependencies and run the application:

```bash
pip install .
fastapi dev src/app/main.py
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs) to view the API documentation.

## CI/CD

When you publish a [new release in GitHub](https://github.com/Hochfrequenz/fristenkalender-functions/releases/new), the [`deploy-azure.yml`](.github/workflows/deploy-azure.yml) workflow automatically:
1. Builds the Docker image
2. Pushes it to Azure Container Registry
3. Deploys to Azure Container Apps

[Another workflow](.github/workflows/publish-ghcr.yml) automatically builds a Docker image and pushes it to GHCR.
This image on GHCR is used e.g. by the [frontend](https://github.com/Hochfrequenz/fristenkalender-frontend) for its integration tests.

### Azure Resources

We only run 1 instance, the production environment: [Azure Portal fristenkalender-api Container App](https://portal.azure.com/#@hochfrequenz.de/resource/subscriptions/2384dcc1-2c97-4c32-932d-44215b137f7a/resourceGroups/rg-fristenkalender-prod/providers/Microsoft.App/containerApps/fristenkalender-api/containerapp) (in the `hochfrequenz.de` tenant).
