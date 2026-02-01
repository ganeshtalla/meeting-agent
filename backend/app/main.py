"""
Meeting Agent - FastAPI Application Entry Point
================================================

This module initializes and configures the FastAPI application for the Meeting Agent.
It serves as the main entry point for the backend API.

Packages Used:
    - fastapi: Web framework for building APIs
        - FastAPI: Main application class
    - fastapi.middleware.cors: CORS middleware for cross-origin requests
        - CORSMiddleware: Enables frontend to communicate with backend

Key Components:
    - app: The FastAPI application instance
    - CORS middleware: Configured to allow requests from frontend origins
    - Routers: health_router and recordings_router for API endpoints

Routes:
    - GET  /           - Root endpoint with API info
    - GET  /api/health - Health check endpoint
    - POST /api/recordings/upload - Upload recording
    - GET  /api/recordings        - List recordings
    - GET  /api/recordings/{id}   - Get recording
    - DELETE /api/recordings/{id} - Delete recording

Usage:
    Run with uvicorn:
    $ uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

    Or run directly:
    $ python -m uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import Base, engine
from app.api import health_router, recordings_router, websocket_router

# -----------------------------------------------------------------------------
# Database Initialization
# -----------------------------------------------------------------------------
# Create all database tables defined in SQLAlchemy models.
# This runs on application startup and creates tables if they don't exist.
# In production, consider using Alembic migrations instead.
Base.metadata.create_all(bind=engine)

# -----------------------------------------------------------------------------
# Ensure Upload Directories Exist
# -----------------------------------------------------------------------------
# Create upload and processed directories if they don't exist
import os
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.processed_dir, exist_ok=True)

# -----------------------------------------------------------------------------
# FastAPI Application Instance
# -----------------------------------------------------------------------------
# Initialize the FastAPI app with metadata for API documentation.
# The title, description, and version appear in the auto-generated docs.
app = FastAPI(
    title="Meeting Agent API",
    description="API for meeting transcription and analysis. "
                "Upload audio/video recordings to get transcripts and AI-powered analysis.",
    version="0.1.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc documentation
)

# -----------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) Configuration
# -----------------------------------------------------------------------------
# CORS middleware allows the frontend (running on a different port) to make
# requests to this backend API. Without this, browsers would block requests.
#
# Configuration:
#   - allow_origins: List of allowed frontend URLs (from settings)
#   - allow_credentials: Allow cookies and authentication headers
#   - allow_methods: Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
#   - allow_headers: Allow all headers in requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Frontend URLs from config
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# -----------------------------------------------------------------------------
# Router Registration
# -----------------------------------------------------------------------------
# Include API routers with the /api prefix.
# Each router handles a specific resource or functionality.

# Health check endpoints: /api/health
app.include_router(health_router, prefix="/api")

# Recording endpoints: /api/recordings/*
app.include_router(recordings_router, prefix="/api")

# WebSocket endpoints: /ws/*
# No prefix - WebSocket paths include /ws already
app.include_router(websocket_router)


# -----------------------------------------------------------------------------
# Root Endpoint
# -----------------------------------------------------------------------------
@app.get("/", tags=["root"])
def root():
    """
    Root endpoint providing API information.

    Returns:
        dict: API name, version, and documentation URLs

    Example Response:
        {
            "message": "Meeting Agent API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/api/health"
        }
    """
    return {
        "message": "Meeting Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health"
    }
