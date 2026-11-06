"""LedgerLine FastAPI application entry point."""

from fastapi import FastAPI

from app.api import api_router

app = FastAPI(
    title="LedgerLine",
    description="Money movement with a ledger you can prove.",
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness/health probe for the API."""
    return {"status": "ok"}
