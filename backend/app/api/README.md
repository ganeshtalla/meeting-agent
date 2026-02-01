# API Package (`api/`)

## Overview

This package contains FastAPI route handlers (endpoints). Each module defines routes for a specific resource or functionality.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports and router aggregation |
| `health.py` | Health check endpoint |
| `recordings.py` | Recording CRUD operations (Phase 2+) |
| `websocket.py` | WebSocket for real-time updates (Phase 5+) |

## Packages Used

| Package | Component | Purpose |
|---------|-----------|---------|
| `fastapi` | `APIRouter` | Groups related endpoints |
| `fastapi` | `Depends` | Dependency injection |
| `sqlalchemy.orm` | `Session` | Database session type |
| `sqlalchemy` | `text` | Raw SQL queries |
| `pydantic` | `BaseModel` | Response schemas |

## Key Components

### `health.py`

**Endpoint:** `GET /api/health`

Returns the health status of the API and database connection.

| Field | Description |
|-------|-------------|
| `status` | API status ('ok') |
| `database` | Database connection status ('ok' or 'error') |

## Route Organization

Routes are organized into routers by resource:

```python
# health.py
router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
def health_check():
    ...
```

Routers are included in `main.py` with a prefix:
```python
app.include_router(health_router, prefix="/api")
# Result: GET /api/health
```

## Usage

```python
from app.api import health_router

# In main.py
app.include_router(health_router, prefix="/api")
```

## Adding New Endpoints

1. Create a new file (e.g., `recordings.py`)
2. Define a router with prefix and tags
3. Add route handlers with decorators
4. Export router in `__init__.py`
5. Include router in `main.py`

Example:
```python
# recordings.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db

router = APIRouter(prefix="/recordings", tags=["recordings"])

@router.get("")
def list_recordings(db: Session = Depends(get_db)):
    return {"recordings": []}
```

## API Documentation

FastAPI auto-generates documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
