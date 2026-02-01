"""
Meeting Agent - Database Package
================================

This package provides database connectivity and session management
using SQLAlchemy ORM.

Exports:
    - Base: Declarative base class for SQLAlchemy models
    - engine: SQLAlchemy engine instance
    - get_db: Dependency function for FastAPI
    - SessionLocal: Session factory for creating database sessions

Usage:
    # In FastAPI endpoints
    from app.db import get_db

    @app.get("/items")
    def get_items(db: Session = Depends(get_db)):
        return db.query(Item).all()

    # For model definitions
    from app.db import Base

    class MyModel(Base):
        __tablename__ = "my_table"
"""

from .database import Base, engine, get_db, SessionLocal

__all__ = ["Base", "engine", "get_db", "SessionLocal"]
