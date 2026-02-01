# Backend Application Package (`app/`)

## Overview

This is the main application package containing all FastAPI application code, organized into logical subpackages.

## Package Structure

| File/Directory | Purpose |
|----------------|---------|
| `__init__.py` | Package marker (empty) |
| `main.py` | FastAPI application instance and configuration |
| `config.py` | Application settings using pydantic-settings |
| `api/` | HTTP route handlers (endpoints) |
| `db/` | Database connection and session management |
| `models/` | SQLAlchemy ORM model definitions |
| `schemas/` | Pydantic request/response schemas |
| `services/` | Business logic layer (Phase 2+) |

## File Details

### `main.py`
**Purpose:** FastAPI application entry point

**Packages Used:**
- `fastapi.FastAPI` - Application instance
- `fastapi.middleware.cors.CORSMiddleware` - Cross-Origin Resource Sharing

**Key Components:**
- `app` - FastAPI application instance
- CORS middleware configuration for frontend access
- Router inclusion for API endpoints
- Database table creation on startup

### `config.py`
**Purpose:** Centralized configuration management

**Packages Used:**
- `pydantic_settings.BaseSettings` - Settings base class
- `pydantic_settings.SettingsConfigDict` - Configuration options
- `pathlib.Path` - File path handling

**Key Components:**
- `Settings` class - All application configuration
- `settings` singleton - Global settings instance
- Environment variable support via `.env` file

## Import Flow

```
main.py
├── config.py (settings)
├── db/ (database connection)
│   └── database.py
├── models/ (ORM models)
│   └── recording.py
└── api/ (route handlers)
    └── health.py
```

## Usage

```python
# Import the FastAPI app
from app.main import app

# Import settings
from app.config import settings

# Import database session
from app.db import get_db
```
