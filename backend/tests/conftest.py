"""
Meeting Agent - Pytest Configuration and Fixtures
==================================================

This module contains pytest fixtures used across all test modules.
Fixtures provide consistent test setup and teardown.

Packages Used:
    - pytest: Testing framework
        - @pytest.fixture: Decorator for defining fixtures
    - fastapi.testclient: Testing utilities for FastAPI
        - TestClient: HTTP client for testing API endpoints
    - sqlalchemy: SQL toolkit and ORM
        - create_engine: Creates database engine
    - sqlalchemy.orm: ORM components
        - sessionmaker: Creates session factory
    - sqlalchemy.pool: Connection pool implementations
        - StaticPool: Single connection pool for testing

Key Fixtures:
    - db_session: Provides isolated database session per test
    - client: Provides FastAPI TestClient with DB override

Test Database Strategy:
    Uses in-memory SQLite for:
    - Speed: No disk I/O
    - Isolation: Fresh database per test
    - Cleanup: Automatic with test completion

Usage:
    def test_something(client, db_session):
        # client and db_session are automatically injected
        response = client.get("/api/health")
        assert response.status_code == 200
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db


# -----------------------------------------------------------------------------
# Test Database Configuration
# -----------------------------------------------------------------------------
# Use in-memory SQLite for testing.
# :memory: creates a new database in RAM that exists only for the connection.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with specific configuration for SQLite + testing
# - check_same_thread=False: Required for SQLite with FastAPI (multi-threaded)
# - StaticPool: Uses a single connection for all operations (required for :memory:)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Keep same connection for in-memory DB
)

# Create session factory bound to test engine
# Sessions created from this factory use the test database
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# -----------------------------------------------------------------------------
# Database Session Fixture
# -----------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.

    This fixture:
    1. Creates all database tables before the test
    2. Provides a new session to the test
    3. Closes the session after the test
    4. Drops all tables for a clean slate

    Scope:
        function - Creates new session for each test function

    Yields:
        Session: SQLAlchemy session connected to test database

    Example:
        def test_create_recording(db_session):
            recording = Recording(title="Test")
            db_session.add(recording)
            db_session.commit()

            result = db_session.query(Recording).first()
            assert result.title == "Test"
    """
    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)

    # Create a new session for this test
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        # Cleanup: close session and drop all tables
        session.close()
        Base.metadata.drop_all(bind=engine)


# -----------------------------------------------------------------------------
# Test Client Fixture
# -----------------------------------------------------------------------------
@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a FastAPI TestClient with database override.

    This fixture:
    1. Overrides the get_db dependency to use test database
    2. Creates a TestClient for making HTTP requests
    3. Cleans up the override after the test

    Args:
        db_session: The database session fixture (automatically injected)

    Yields:
        TestClient: HTTP client for testing API endpoints

    Example:
        def test_health_check(client):
            response = client.get("/api/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    Note:
        The dependency override ensures all database operations
        in the tested endpoints use the test database.
    """

    # Define override function that returns test session
    def override_get_db():
        """Dependency override to use test database session."""
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture

    # Override the get_db dependency with our test version
    app.dependency_overrides[get_db] = override_get_db

    # Create TestClient and yield it for the test
    with TestClient(app) as test_client:
        yield test_client

    # Cleanup: remove the dependency override
    app.dependency_overrides.clear()
