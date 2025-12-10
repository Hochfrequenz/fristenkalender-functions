# fristenkalender-functions

This repository provides an HTTP API that exposes the features of [fristenkalender_generator](https://github.com/Hochfrequenz/fristenkalender_generator).
It's used by the [fristenkalender-frontend](https://github.com/Hochfrequenz/fristenkalender-frontend) which is deployed to [fristenkalender.hochfrequenz.de](https://fristenkalender.hochfrequenz.de/).

## API Documentation

The API documentation is available at the `/docs` endpoint (OpenAPI/Swagger UI).

## Local Setup

Install the dependencies and run the application:

```bash
pip install .
fastapi dev src/app/main.py
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs) to view the API documentation.
