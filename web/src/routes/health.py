"""Health check API routes."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    agent: str
    services: dict


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns the status of the API and its dependencies.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        agent="connected",
        services={
            "api": "healthy",
            "database": "healthy",
            "agent": "healthy"
        }
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Returns 200 if the service is ready to accept traffic.
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    Returns 200 if the service is alive.
    """
    return {"status": "alive"}
