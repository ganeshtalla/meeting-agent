"""
Meeting Agent - WebSocket API for Real-time Updates
====================================================

This module provides WebSocket endpoints for real-time status updates
during recording processing.

Packages Used:
    - fastapi: WebSocket support
        - WebSocket: WebSocket connection handling
        - WebSocketDisconnect: Exception for disconnections
    - asyncio: Async support for background tasks
    - json: JSON serialization

Key Components:
    - ConnectionManager: Manages active WebSocket connections
    - websocket_endpoint: WebSocket route for status updates

Protocol:
    1. Client connects to /ws/recordings/{recording_id}
    2. Server sends status updates as JSON:
       {
           "recording_id": 1,
           "stage": "transcribing",
           "progress": 45,
           "message": "Transcribing audio..."
       }
    3. Client receives updates until processing completes/fails
    4. Connection closes automatically when done

Usage:
    # JavaScript client
    const ws = new WebSocket('ws://localhost:8000/ws/recordings/1');
    ws.onmessage = (event) => {
        const status = JSON.parse(event.data);
        console.log(`Stage: ${status.stage}, Progress: ${status.progress}%`);
    };
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import asyncio
import json
import logging

from app.services.pipeline import PipelineStatus


# Configure logging
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Router Configuration
# -----------------------------------------------------------------------------
router = APIRouter(tags=["websocket"])


# -----------------------------------------------------------------------------
# Connection Manager
# -----------------------------------------------------------------------------

class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Tracks active connections per recording and broadcasts status updates
    to all connected clients watching a specific recording.

    Attributes:
        active_connections: Dict mapping recording_id to set of WebSocket connections

    Example:
        manager = ConnectionManager()

        # Connect
        await manager.connect(websocket, recording_id=1)

        # Broadcast status
        await manager.broadcast(recording_id=1, status)

        # Disconnect
        manager.disconnect(websocket, recording_id=1)
    """

    def __init__(self):
        """Initialize with empty connection tracking."""
        # Map recording_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, recording_id: int) -> None:
        """
        Accept and track a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            recording_id: ID of recording to watch
        """
        await websocket.accept()

        if recording_id not in self.active_connections:
            self.active_connections[recording_id] = set()

        self.active_connections[recording_id].add(websocket)
        logger.info(f"WebSocket connected for recording {recording_id}")

    def disconnect(self, websocket: WebSocket, recording_id: int) -> None:
        """
        Remove a WebSocket connection from tracking.

        Args:
            websocket: The WebSocket connection
            recording_id: ID of recording that was being watched
        """
        if recording_id in self.active_connections:
            self.active_connections[recording_id].discard(websocket)

            # Clean up empty sets
            if not self.active_connections[recording_id]:
                del self.active_connections[recording_id]

        logger.info(f"WebSocket disconnected for recording {recording_id}")

    async def broadcast(self, recording_id: int, status: PipelineStatus) -> None:
        """
        Broadcast status update to all connections watching a recording.

        Args:
            recording_id: ID of recording
            status: PipelineStatus to broadcast
        """
        if recording_id not in self.active_connections:
            return

        message = json.dumps(status.to_dict())
        disconnected = set()

        for websocket in self.active_connections[recording_id]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.active_connections[recording_id].discard(ws)

    async def send_personal(self, websocket: WebSocket, data: dict) -> None:
        """
        Send a message to a specific WebSocket.

        Args:
            websocket: Target WebSocket connection
            data: Data to send (will be JSON serialized)
        """
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")

    def get_connection_count(self, recording_id: int) -> int:
        """
        Get number of active connections for a recording.

        Args:
            recording_id: ID of recording

        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections.get(recording_id, set()))

    def has_connections(self, recording_id: int) -> bool:
        """
        Check if any clients are watching a recording.

        Args:
            recording_id: ID of recording

        Returns:
            True if there are active connections
        """
        return self.get_connection_count(recording_id) > 0


# Global connection manager instance
manager = ConnectionManager()


# -----------------------------------------------------------------------------
# WebSocket Endpoints
# -----------------------------------------------------------------------------

@router.websocket("/ws/recordings/{recording_id}")
async def websocket_endpoint(websocket: WebSocket, recording_id: int):
    """
    WebSocket endpoint for real-time recording status updates.

    Clients connect to this endpoint to receive status updates while
    a recording is being processed. Updates are sent as JSON objects.

    Args:
        websocket: The WebSocket connection
        recording_id: ID of the recording to watch

    Message Format (server → client):
        {
            "recording_id": 1,
            "stage": "transcribing",  // pending, extracting, transcribing, analyzing, completed, failed
            "progress": 45,           // 0-100
            "message": "Transcribing audio...",
            "error": null,            // Error message if failed
            "started_at": "2024-01-15T10:00:00",
            "updated_at": "2024-01-15T10:01:30"
        }

    Example JavaScript Client:
        const ws = new WebSocket('ws://localhost:8000/ws/recordings/1');

        ws.onopen = () => {
            console.log('Connected');
        };

        ws.onmessage = (event) => {
            const status = JSON.parse(event.data);
            updateProgressBar(status.progress);
            updateStatusText(status.message);

            if (status.stage === 'completed' || status.stage === 'failed') {
                ws.close();
            }
        };

        ws.onclose = () => {
            console.log('Disconnected');
        };
    """
    await manager.connect(websocket, recording_id)

    try:
        # Send initial connection confirmation
        await manager.send_personal(websocket, {
            "type": "connected",
            "recording_id": recording_id,
            "message": "Connected to status updates"
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong, commands, etc.)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout for keepalive
                )

                # Handle client messages
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await manager.send_personal(websocket, {"type": "pong"})
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await manager.send_personal(websocket, {"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from recording {recording_id}")
    except Exception as e:
        logger.error(f"WebSocket error for recording {recording_id}: {e}")
    finally:
        manager.disconnect(websocket, recording_id)


# -----------------------------------------------------------------------------
# Utility Functions for Broadcasting
# -----------------------------------------------------------------------------

async def broadcast_status(recording_id: int, status: PipelineStatus) -> None:
    """
    Broadcast a status update to all connected clients.

    This function is called by the processing pipeline to notify
    connected clients of status changes.

    Args:
        recording_id: ID of the recording
        status: Current pipeline status
    """
    await manager.broadcast(recording_id, status)


def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.

    Returns:
        ConnectionManager: The global connection manager
    """
    return manager
