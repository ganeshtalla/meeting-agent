"""
Meeting Agent - WebSocket Tests
===============================

Tests for the WebSocket endpoint that provides real-time status updates
during recording processing.

Packages Used:
    - pytest: Test framework
    - pytest-asyncio: Async test support
    - fastapi.testclient: WebSocket testing

Test Categories:
    1. Connection Manager: Connection tracking
    2. WebSocket Endpoint: Connection lifecycle
    3. Broadcasting: Message distribution

Running These Tests:
    pytest tests/test_websocket.py -v
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from app.main import app
from app.api.websocket import ConnectionManager, manager
from app.services.pipeline import PipelineStatus, PipelineStage


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def connection_manager():
    """Create a fresh connection manager for testing."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock(spec=WebSocket)
    return ws


# -----------------------------------------------------------------------------
# Connection Manager Tests
# -----------------------------------------------------------------------------

class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, connection_manager, mock_websocket):
        """Manager should accept WebSocket connection."""
        await connection_manager.connect(mock_websocket, recording_id=1)

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_tracks_connection(self, connection_manager, mock_websocket):
        """Manager should track connected WebSockets."""
        await connection_manager.connect(mock_websocket, recording_id=1)

        assert connection_manager.has_connections(1)
        assert connection_manager.get_connection_count(1) == 1

    @pytest.mark.asyncio
    async def test_connect_multiple_clients(self, connection_manager):
        """Manager should track multiple connections per recording."""
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(ws1, recording_id=1)
        await connection_manager.connect(ws2, recording_id=1)

        assert connection_manager.get_connection_count(1) == 2

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, connection_manager, mock_websocket):
        """Manager should remove disconnected WebSockets."""
        await connection_manager.connect(mock_websocket, recording_id=1)
        connection_manager.disconnect(mock_websocket, recording_id=1)

        assert not connection_manager.has_connections(1)

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up_empty_sets(self, connection_manager, mock_websocket):
        """Manager should clean up empty connection sets."""
        await connection_manager.connect(mock_websocket, recording_id=1)
        connection_manager.disconnect(mock_websocket, recording_id=1)

        assert 1 not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self, connection_manager):
        """Manager should broadcast to all connections for a recording."""
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(ws1, recording_id=1)
        await connection_manager.connect(ws2, recording_id=1)

        status = PipelineStatus(
            recording_id=1,
            stage=PipelineStage.TRANSCRIBING,
            progress=50,
            message="Processing..."
        )

        await connection_manager.broadcast(1, status)

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_does_nothing_for_no_connections(self, connection_manager):
        """Manager should handle broadcast with no connections."""
        status = PipelineStatus(
            recording_id=999,
            stage=PipelineStage.COMPLETED,
            progress=100,
            message="Done"
        )

        # Should not raise
        await connection_manager.broadcast(999, status)

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_failures(self, connection_manager):
        """Manager should handle WebSocket send failures gracefully."""
        ws1 = AsyncMock(spec=WebSocket)
        ws1.send_text.side_effect = Exception("Connection closed")

        await connection_manager.connect(ws1, recording_id=1)

        status = PipelineStatus(
            recording_id=1,
            stage=PipelineStage.COMPLETED,
            progress=100,
            message="Done"
        )

        # Should not raise
        await connection_manager.broadcast(1, status)

    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """Manager should send personal messages."""
        await connection_manager.connect(mock_websocket, recording_id=1)

        await connection_manager.send_personal(
            mock_websocket,
            {"type": "ping"}
        )

        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        assert json.loads(call_args) == {"type": "ping"}

    def test_has_connections_returns_false_for_no_connections(self, connection_manager):
        """has_connections should return False when no clients connected."""
        assert not connection_manager.has_connections(999)

    def test_get_connection_count_returns_zero_for_no_connections(self, connection_manager):
        """get_connection_count should return 0 when no clients connected."""
        assert connection_manager.get_connection_count(999) == 0


# -----------------------------------------------------------------------------
# WebSocket Endpoint Tests
# -----------------------------------------------------------------------------

class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint behavior."""

    def test_websocket_connection(self, client):
        """WebSocket should accept connections."""
        with client.websocket_connect("/ws/recordings/1") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["recording_id"] == 1

    def test_websocket_ping_pong(self, client):
        """WebSocket should respond to ping with pong."""
        with client.websocket_connect("/ws/recordings/1") as websocket:
            # Consume connection message
            websocket.receive_json()

            # Send ping
            websocket.send_json({"type": "ping"})

            # Should receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_websocket_handles_invalid_json(self, client):
        """WebSocket should handle invalid JSON gracefully."""
        with client.websocket_connect("/ws/recordings/1") as websocket:
            # Consume connection message
            websocket.receive_json()

            # Send invalid JSON - should not crash
            websocket.send_text("not valid json")

            # Connection should still work
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"


# -----------------------------------------------------------------------------
# Status Broadcast Tests
# -----------------------------------------------------------------------------

class TestStatusBroadcast:
    """Tests for status broadcasting functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_status_format(self, connection_manager, mock_websocket):
        """Broadcast should send correctly formatted status."""
        await connection_manager.connect(mock_websocket, recording_id=1)

        status = PipelineStatus(
            recording_id=1,
            stage=PipelineStage.TRANSCRIBING,
            progress=50,
            message="Transcribing audio..."
        )

        await connection_manager.broadcast(1, status)

        # Verify message format
        call_args = mock_websocket.send_text.call_args[0][0]
        data = json.loads(call_args)

        assert data["recording_id"] == 1
        assert data["stage"] == "transcribing"
        assert data["progress"] == 50
        assert data["message"] == "Transcribing audio..."

    @pytest.mark.asyncio
    async def test_broadcast_only_to_specific_recording(self, connection_manager):
        """Broadcast should only send to clients watching that recording."""
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(ws1, recording_id=1)
        await connection_manager.connect(ws2, recording_id=2)

        status = PipelineStatus(
            recording_id=1,
            stage=PipelineStage.COMPLETED,
            progress=100,
            message="Done"
        )

        await connection_manager.broadcast(1, status)

        # Only ws1 should receive the message
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_not_called()


# -----------------------------------------------------------------------------
# Integration with Pipeline Tests
# -----------------------------------------------------------------------------

class TestWebSocketPipelineIntegration:
    """Tests for WebSocket integration with processing pipeline."""

    def test_global_manager_instance(self):
        """Global manager instance should be available."""
        from app.api.websocket import get_connection_manager

        mgr = get_connection_manager()
        assert mgr is manager
        assert isinstance(mgr, ConnectionManager)
