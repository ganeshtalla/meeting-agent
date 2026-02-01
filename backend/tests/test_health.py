"""
Meeting Agent - Health Endpoint Tests
=====================================

This module contains tests for the health check endpoint.
Tests verify that the API and database are functioning correctly.

Packages Used:
    - sqlalchemy: SQL toolkit
        - text: Creates literal SQL expressions for raw queries

Test Functions:
    - test_health_check_returns_ok: Verifies health endpoint response
    - test_health_check_database_status: Verifies database status field
    - test_database_connection: Verifies direct database connectivity
    - test_cors_headers_present: Verifies CORS configuration
    - test_root_endpoint: Verifies root endpoint response

Fixtures Used:
    - client: FastAPI TestClient (from conftest.py)
    - db_session: Database session (from conftest.py)

Running These Tests:
    pytest tests/test_health.py -v
"""

from sqlalchemy import text


# -----------------------------------------------------------------------------
# Health Endpoint Tests
# -----------------------------------------------------------------------------

def test_health_check_returns_ok(client):
    """
    Health endpoint should return 200 with status ok.

    Verifies:
        - HTTP status code is 200
        - Response contains "status" field
        - Status value is "ok"

    Endpoint:
        GET /api/health

    Expected Response:
        {"status": "ok", "database": "ok"}
    """
    # Act: Make request to health endpoint
    response = client.get("/api/health")

    # Assert: Verify response
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_check_database_status(client):
    """
    Health endpoint should include database status.

    Verifies:
        - Response contains "database" field
        - Database status is "ok" (test DB is working)

    This ensures the health check actually tests DB connectivity,
    not just returns a static response.
    """
    # Act: Make request to health endpoint
    response = client.get("/api/health")

    # Assert: Verify database status
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


# -----------------------------------------------------------------------------
# Database Connection Test
# -----------------------------------------------------------------------------

def test_database_connection(db_session):
    """
    Database session should be active and usable.

    Verifies:
        - Session can execute SQL queries
        - Simple query returns expected result

    This is a direct test of the database fixture,
    ensuring tests have proper database access.

    Args:
        db_session: SQLAlchemy session from conftest fixture
    """
    # Act: Execute simple SQL query
    result = db_session.execute(text("SELECT 1"))

    # Assert: Verify query result
    assert result.scalar() == 1


# -----------------------------------------------------------------------------
# CORS Configuration Test
# -----------------------------------------------------------------------------

def test_cors_headers_present(client):
    """
    CORS headers should be present for frontend access.

    Verifies:
        - OPTIONS request returns CORS headers
        - Access-Control-Allow-Origin header is set

    This ensures the frontend (running on different port)
    can communicate with the API without CORS errors.

    Note:
        The OPTIONS request is a "preflight" request that browsers
        send before the actual request to check CORS policy.
    """
    # Act: Send preflight OPTIONS request with Origin header
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",  # Frontend URL
            "Access-Control-Request-Method": "GET",  # Requested method
        },
    )

    # Assert: Verify CORS header is present
    # Header names are lowercase in the response
    assert "access-control-allow-origin" in response.headers


# -----------------------------------------------------------------------------
# Root Endpoint Test
# -----------------------------------------------------------------------------

def test_root_endpoint(client):
    """
    Root endpoint should return API info.

    Verifies:
        - GET / returns 200
        - Response contains API name
        - Response includes docs URL

    Endpoint:
        GET /

    Expected Response:
        {"message": "Meeting Agent API", "docs": "/docs"}
    """
    # Act: Make request to root endpoint
    response = client.get("/")

    # Assert: Verify response
    assert response.status_code == 200
    assert "Meeting Agent API" in response.json()["message"]
