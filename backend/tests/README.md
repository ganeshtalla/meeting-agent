# Tests Package (`tests/`)

## Overview

This package contains pytest test suites for the Meeting Agent backend. Tests are organized by module and use fixtures for consistent test setup.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `conftest.py` | Shared pytest fixtures |
| `test_health.py` | Health endpoint tests |
| `test_upload.py` | Upload endpoint tests (Phase 2+) |
| `test_transcription.py` | Transcription service tests (Phase 3+) |
| `test_analyzer.py` | Analyzer service tests (Phase 4+) |
| `test_pipeline.py` | Pipeline integration tests (Phase 5+) |

## Packages Used

| Package | Component | Purpose |
|---------|-----------|---------|
| `pytest` | `@pytest.fixture` | Test fixture definitions |
| `fastapi.testclient` | `TestClient` | HTTP client for API testing |
| `sqlalchemy` | `create_engine` | In-memory test database |
| `sqlalchemy.orm` | `sessionmaker` | Test session factory |
| `sqlalchemy.pool` | `StaticPool` | Connection pooling for tests |

## Key Components

### `conftest.py`

Provides shared fixtures:

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `db_session` | function | Fresh database session per test |
| `client` | function | FastAPI TestClient with DB override |

### Test Database

Tests use an in-memory SQLite database (`sqlite:///:memory:`) that:
- Is created fresh for each test function
- Is isolated from the production database
- Is automatically cleaned up after tests

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_health.py

# Run specific test function
pytest tests/test_health.py::test_health_check_returns_ok

# Run with coverage report
pytest --cov=app --cov-report=html

# Run tests matching a pattern
pytest -k "health"
```

## Test Fixtures

### `db_session`

Provides a clean database session for each test:

```python
def test_something(db_session):
    # db_session is a fresh SQLAlchemy Session
    recording = Recording(title="Test")
    db_session.add(recording)
    db_session.commit()
    # Database is cleaned up after test
```

### `client`

Provides a TestClient with database override:

```python
def test_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
```

## Writing Tests

### Test Structure

```python
def test_descriptive_name(client):
    """Docstring explaining what is being tested."""
    # Arrange - Set up test data
    data = {"title": "Test"}

    # Act - Perform the action
    response = client.post("/api/endpoint", json=data)

    # Assert - Verify the result
    assert response.status_code == 201
```

### Naming Conventions

- Test files: `test_<module>.py`
- Test functions: `test_<action>_<expected_result>`
- Examples:
  - `test_health_check_returns_ok`
  - `test_upload_rejects_invalid_file_type`

## Fixtures Directory

The `fixtures/` directory contains test data files:

```
fixtures/
├── sample.wav       # Sample audio file
├── sample.mp4       # Sample video file (Phase 3+)
└── transcript.json  # Sample transcript (Phase 4+)
```
