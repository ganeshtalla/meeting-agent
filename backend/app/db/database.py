"""
Meeting Agent - Database Connection and Session Management
==========================================================

This module configures the SQLAlchemy database connection for the Meeting Agent.
It provides the engine, session factory, and base class for ORM models.

Packages Used:
    - sqlalchemy: SQL toolkit and ORM
        - create_engine: Creates the database engine
    - sqlalchemy.orm: Object-Relational Mapping components
        - sessionmaker: Factory for creating Session instances
        - declarative_base: Factory for creating base classes for models

Key Components:
    - engine: SQLAlchemy Engine connected to the database
    - SessionLocal: Session factory (not a session itself)
    - Base: Declarative base class for all ORM models
    - get_db(): FastAPI dependency for database sessions

Database:
    Uses SQLite by default for simplicity. The connection string is
    configured in app/config.py and can be overridden via environment
    variables for production use (e.g., PostgreSQL).

Usage:
    # As FastAPI dependency
    from fastapi import Depends
    from sqlalchemy.orm import Session
    from app.db.database import get_db

    @app.get("/items")
    def read_items(db: Session = Depends(get_db)):
        return db.query(Item).all()
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

from app.config import settings

# -----------------------------------------------------------------------------
# Database Engine
# -----------------------------------------------------------------------------
# The engine is the starting point for any SQLAlchemy application.
# It maintains a pool of connections and handles communication with the database.
#
# Arguments:
#   - settings.database_url: Connection string from configuration
#   - connect_args: SQLite-specific setting to allow multi-threaded access
#     (SQLite by default only allows one thread per connection)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # Required for SQLite with FastAPI
)

# -----------------------------------------------------------------------------
# Session Factory
# -----------------------------------------------------------------------------
# SessionLocal is a factory that produces new Session objects when called.
# Each Session represents a "holding zone" for all objects loaded or associated
# with it during its lifespan.
#
# Configuration:
#   - autocommit=False: Transactions must be explicitly committed
#   - autoflush=False: Changes are not automatically flushed to the database
#   - bind=engine: Associates sessions with our database engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -----------------------------------------------------------------------------
# Declarative Base
# -----------------------------------------------------------------------------
# Base is the base class for all ORM model classes.
# Models inherit from Base to gain SQLAlchemy ORM functionality.
# The metadata attribute holds all Table objects for creating/dropping tables.
Base = declarative_base()


# -----------------------------------------------------------------------------
# Database Session Dependency
# -----------------------------------------------------------------------------
def get_db() -> Generator:
    """
    FastAPI dependency that provides a database session.

    This function is used with FastAPI's Depends() to inject a database
    session into route handlers. The session is automatically closed
    after the request completes, even if an exception occurs.

    Yields:
        Session: A SQLAlchemy database session

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()

    Note:
        The try/finally pattern ensures the session is always closed,
        preventing connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
