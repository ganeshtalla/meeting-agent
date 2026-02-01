# Database Package (`db/`)

## Overview

This package contains all database-related code including connection management, session handling, and the SQLAlchemy base class for models.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports for easy imports |
| `database.py` | SQLAlchemy engine, session factory, and base class |

## Packages Used

| Package | Component | Purpose |
|---------|-----------|---------|
| `sqlalchemy` | `create_engine` | Creates database connection engine |
| `sqlalchemy.orm` | `sessionmaker` | Factory for creating database sessions |
| `sqlalchemy.orm` | `declarative_base` | Base class for ORM models |

## Key Components

### `database.py`

1. **`engine`** - SQLAlchemy engine connected to SQLite database
2. **`SessionLocal`** - Session factory for creating database sessions
3. **`Base`** - Declarative base class that all models inherit from
4. **`get_db()`** - Dependency function for FastAPI dependency injection

## Usage

```python
# Import the database session dependency
from app.db import get_db

# Use in FastAPI endpoint
@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()

# Import Base for model definition
from app.db import Base

class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(Integer, primary_key=True)
```

## Database Connection Flow

```
1. app/main.py imports engine and Base
2. Base.metadata.create_all(engine) creates tables
3. API endpoints use get_db() to get sessions
4. Sessions are automatically closed after request
```

## Configuration

The database URL is configured in `app/config.py`:
- Default: `sqlite:///./meeting_agent.db`
- Override via `DATABASE_URL` environment variable
