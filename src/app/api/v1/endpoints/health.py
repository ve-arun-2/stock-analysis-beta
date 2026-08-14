"""Liveness/readiness endpoint used by load balancers and Docker healthchecks."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a simple OK payload to confirm the API process is up."""
    return {"status": "ok"}
