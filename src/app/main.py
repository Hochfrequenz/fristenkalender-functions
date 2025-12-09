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
