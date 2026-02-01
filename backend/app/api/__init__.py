"""
Meeting Agent - API Package
===========================

This package contains FastAPI route handlers (endpoints) for the Meeting Agent.
Routes are organized into separate modules by resource or functionality.

Package Structure:
    - health.py: Health check endpoint for monitoring
    - recordings.py: Recording upload, listing, and management
    - websocket.py: WebSocket endpoint for real-time status updates

Exports:
    - health_router: Router for health check endpoints
    - recordings_router: Router for recording operations
    - websocket_router: Router for WebSocket connections

Usage:
    # In main.py
    from app.api import health_router, recordings_router, websocket_router

    app.include_router(health_router, prefix="/api")
    app.include_router(recordings_router, prefix="/api")
    app.include_router(websocket_router)  # No prefix for WebSocket

Route Prefixes:
    After including in main.py with prefix="/api":
    - /api/health - Health check
    - /api/recordings - Recording operations
    - /api/recordings/upload - File upload
    - /api/recordings/{id} - Single recording operations
    - /api/recordings/{id}/process - Start processing
    - /ws/recordings/{id} - WebSocket for status updates

Endpoints Summary:
    Health:
        GET  /api/health - Check API and database status

    Recordings:
        POST   /api/recordings/upload      - Upload new recording
        GET    /api/recordings             - List all recordings
        GET    /api/recordings/{id}        - Get recording by ID
        GET    /api/recordings/{id}/details - Get recording with transcript/analysis
        POST   /api/recordings/{id}/process - Start processing
        DELETE /api/recordings/{id}        - Delete recording

    WebSocket:
        WS  /ws/recordings/{id} - Real-time status updates
"""

from .health import router as health_router
from .recordings import router as recordings_router
from .websocket import router as websocket_router

__all__ = ["health_router", "recordings_router", "websocket_router"]
