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

## MCP Server

The same app also exposes a **read-only [MCP](https://modelcontextprotocol.io/) server** at
`/mcp`, so agents (Claude, opencode, …) can call the Fristenkalender calculations as tools.
It wraps the REST API 1:1 via `FastMCP.from_fastapi`, so the tool set always matches the
OpenAPI spec. Only an explicit allowlist of the non-mutating JSON endpoints becomes tools
(the two ICS-export endpoints are excluded); every tool is annotated `readOnlyHint`.

Mirroring the sibling repos [`ahbicht-functions`](https://github.com/Hochfrequenz/ahbicht-functions)
and [`ahb-tabellen`](https://github.com/Hochfrequenz/ahb-tabellen), `/mcp` is protected by
**Auth0 as an OAuth 2.1 resource server**: it validates Auth0-issued bearer JWTs (RS256/JWKS)
and advertises the tenant via [RFC 9728](https://www.rfc-editor.org/rfc/rfc9728) Protected
Resource Metadata. There is no client secret — MCP clients self-register via Auth0 Dynamic
Client Registration and do PKCE against `auth.hochfrequenz.de`.

### Configuration

Auth is controlled by two environment variables (see [`.env.example`](.env.example)); set
**both** to enable it, or **neither** to run `/mcp` unauthenticated (local dev). Setting
exactly one fails startup on purpose.

| Variable | Value |
| --- | --- |
| `MCP_AUTH0_ISSUER_BASE_URL` | `https://auth.hochfrequenz.de/` |
| `MCP_AUTH0_AUDIENCE` | the canonical `/mcp` URL of the deployment (prod: `https://fristenkalender-api.happyfield-64ecc075.westeurope.azurecontainerapps.io/mcp`) |

On Azure these are set from the Bicep container-app template
([`infra/bicep/modules/container-app.bicep`](infra/bicep/modules/container-app.bicep)) and
applied automatically on the next release deploy — not via the Azure Portal. The matching
Auth0 API (resource server) must be created once by hand.

### Verifying a deployment

```bash
EXPECT_AUTH=1 scripts/verify-mcp.sh https://fristenkalender-api.happyfield-64ecc075.westeurope.azurecontainerapps.io
```

`EXPECT_AUTH=1` makes the script *require* auth to be on: it expects a `401` plus the RFC 9728
metadata pointing at the Hochfrequenz Auth0 tenant, and fails if `/mcp` answers unauthenticated.
Omit it for a local dev server running without auth.

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
