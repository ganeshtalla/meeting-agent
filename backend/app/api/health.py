"""
Meeting Agent - Health Check Endpoint
=====================================

This module provides a health check endpoint for monitoring the API
and its dependencies (database, etc.).

Packages Used:
    - fastapi: Web framework
        - APIRouter: Groups related endpoints
        - Depends: Dependency injection for request handlers
    - sqlalchemy.orm: ORM session management
        - Session: Database session type hint
    - sqlalchemy: SQL toolkit
        - text: Creates a literal SQL expression
    - pydantic: Data validation
        - BaseModel: Base class for response schemas

Key Components:
    - router: FastAPI router for health endpoints
    - HealthResponse: Pydantic schema for health response
    - health_check: Endpoint handler function

Endpoint:
    GET /api/health
        Returns the health status of the API and database.

Response Format:
    {
        "status": "ok",
        "database": "ok"
    }

Usage:
    # Via curl
    curl http://localhost:8000/api/health

    # Via httpx/requests
    response = requests.get("http://localhost:8000/api/health")
    print(response.json())  # {"status": "ok", "database": "ok"}
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.db.database import get_db

# -----------------------------------------------------------------------------
# Router Configuration
# -----------------------------------------------------------------------------
# Create a router for health-related endpoints.
# - prefix: All routes in this router will be prefixed with /health
# - tags: Groups endpoints in API documentation (Swagger UI)
router = APIRouter(prefix="/health", tags=["health"])


# -----------------------------------------------------------------------------
# Response Schema
# -----------------------------------------------------------------------------
class HealthResponse(BaseModel):
    """
    Health check response schema.

    Defines the structure of the health check response for
    API documentation and type safety.

    Attributes:
        status (str): Overall API status ('ok')
        database (str): Database connection status ('ok' or 'error')
    """
    status: str
    database: str


# -----------------------------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------------------------
@router.get("", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.

    Verifies that the API is running and can connect to the database.
    Used by monitoring systems, load balancers, and container orchestrators
    to determine if the service is healthy.

    Args:
        db (Session): Database session injected by FastAPI's dependency system.
                     The Depends(get_db) automatically provides a session.

    Returns:
        HealthResponse: JSON object with status fields

    Response Fields:
        - status: Always "ok" if the endpoint responds
        - database: "ok" if database query succeeds, "error" otherwise

    Example:
        GET /api/health

        Response 200 OK:
        {
            "status": "ok",
            "database": "ok"
        }

    HTTP Status Codes:
        - 200: API is healthy (even if database is unhealthy)
        - 500: Unexpected error (API is unhealthy)

    Note:
        The endpoint returns 200 even if the database is unhealthy.
        This is intentional - it allows monitoring systems to distinguish
        between API issues and database issues.
    """
    # -------------------------------------------------------------------------
    # Database Health Check
    # -------------------------------------------------------------------------
    # Execute a simple query to verify database connectivity.
    # Using text() for raw SQL - "SELECT 1" is universal across databases.
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        # Database is unreachable or query failed
        db_status = "error"

    # -------------------------------------------------------------------------
    # Return Health Status
    # -------------------------------------------------------------------------
    return HealthResponse(
        status="ok",      # API is responding
        database=db_status  # Database connectivity status
    )
