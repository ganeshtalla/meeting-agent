"""
Meeting Agent - Export Service Tests
====================================

Tests for the ExportService class which handles exporting meeting data
to various formats (Markdown, JSON, Text).

Packages Used:
    - pytest: Test framework
    - json: JSON parsing for verification

Test Categories:
    1. Markdown Export: Test Markdown formatting
    2. JSON Export: Test JSON structure
    3. Text Export: Test plain text output
    4. Action Items Export: Test action items checklist
    5. Error Handling: Edge cases

Running These Tests:
    pytest tests/test_export.py -v
"""

import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock

from app.services.export import ExportService, ExportResult
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.analysis import Analysis


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def export_service():
    """Create an ExportService instance."""
    return ExportService()


@pytest.fixture
def mock_recording():
    """Create a mock recording."""
    recording = MagicMock(spec=Recording)
    recording.id = 1
    recording.title = "Sprint Planning Meeting"
    recording.original_filename = "meeting.mp4"
    recording.file_size = 52428800
    recording.mime_type = "video/mp4"
    recording.duration_seconds = 1800
    recording.status = "completed"
    recording.created_at = datetime(2024, 1, 15, 10, 0, 0)
    recording.processed_at = datetime(2024, 1, 15, 10, 5, 0)
    recording.transcript = None
    recording.analysis = None
    return recording


@pytest.fixture
def mock_transcript():
    """Create a mock transcript."""
    transcript = MagicMock(spec=Transcript)
    transcript.id = 10
    transcript.full_text = "Hello everyone. Let's discuss the project. We need to finish by Friday."
    transcript.segments = [
        {"start": 0.0, "end": 2.0, "text": "Hello everyone."},
        {"start": 2.0, "end": 5.0, "text": "Let's discuss the project."},
        {"start": 5.0, "end": 8.0, "text": "We need to finish by Friday."}
    ]
    transcript.language = "en"
    transcript.duration_seconds = 8.0
    return transcript


@pytest.fixture
def mock_analysis():
    """Create a mock analysis."""
    analysis = MagicMock(spec=Analysis)
    analysis.id = 20
    analysis.summary = "Team discussed project timeline and deliverables."
    analysis.action_items = [
        {"speaker": "John", "task": "Review the PR", "due_date": "Friday"},
        {"speaker": "Sarah", "task": "Send email to client", "due_date": "Today", "priority": "high"}
    ]
    analysis.decisions = ["Use PostgreSQL for the database", "Deploy on Friday"]
    analysis.key_topics = ["Project timeline", "Database", "Deployment"]
    analysis.model_used = "mistral"
    return analysis


# -----------------------------------------------------------------------------
# Markdown Export Tests
# -----------------------------------------------------------------------------

class TestMarkdownExport:
    """Tests for Markdown export functionality."""

    def test_markdown_export_basic(self, export_service, mock_recording):
        """Should export basic recording info to Markdown."""
        result = export_service.to_markdown(mock_recording)

        assert result.success is True
        assert result.format == "markdown"
        assert "# Sprint Planning Meeting" in result.content
        assert "## Meeting Details" in result.content

    def test_markdown_export_with_analysis(self, export_service, mock_recording, mock_analysis):
        """Should include analysis in Markdown export."""
        result = export_service.to_markdown(mock_recording, analysis=mock_analysis)

        assert result.success is True
        assert "## Summary" in result.content
        assert "Team discussed project timeline" in result.content
        assert "## Action Items" in result.content
        assert "- [ ] **John**: Review the PR" in result.content
        assert "## Decisions Made" in result.content
        assert "Use PostgreSQL" in result.content

    def test_markdown_export_with_transcript(self, export_service, mock_recording, mock_transcript):
        """Should include transcript in Markdown export."""
        result = export_service.to_markdown(mock_recording, transcript=mock_transcript)

        assert result.success is True
        assert "## Transcript" in result.content
        assert "Hello everyone" in result.content
        assert "[00:00]" in result.content  # Timestamp format

    def test_markdown_export_full(self, export_service, mock_recording, mock_transcript, mock_analysis):
        """Should export complete meeting data."""
        result = export_service.to_markdown(mock_recording, mock_transcript, mock_analysis)

        assert result.success is True
        # All sections present
        assert "## Meeting Details" in result.content
        assert "## Summary" in result.content
        assert "## Action Items" in result.content
        assert "## Transcript" in result.content
        assert "## Key Topics" in result.content

    def test_markdown_filename_generation(self, export_service, mock_recording):
        """Should generate appropriate filename."""
        result = export_service.to_markdown(mock_recording)

        assert result.success is True
        assert result.filename.endswith(".md")
        assert "Sprint_Planning_Meeting" in result.filename

    def test_markdown_action_items_with_due_date(self, export_service, mock_recording, mock_analysis):
        """Should include due dates in action items."""
        result = export_service.to_markdown(mock_recording, analysis=mock_analysis)

        assert "*(Due: Friday)*" in result.content

    def test_markdown_action_items_with_priority(self, export_service, mock_recording, mock_analysis):
        """Should include priority in action items."""
        result = export_service.to_markdown(mock_recording, analysis=mock_analysis)

        assert "`high`" in result.content


# -----------------------------------------------------------------------------
# JSON Export Tests
# -----------------------------------------------------------------------------

class TestJsonExport:
    """Tests for JSON export functionality."""

    def test_json_export_basic(self, export_service, mock_recording):
        """Should export basic recording info to JSON."""
        result = export_service.to_json(mock_recording)

        assert result.success is True
        assert result.format == "json"

        data = json.loads(result.content)
        assert data["recording"]["id"] == 1
        assert data["recording"]["title"] == "Sprint Planning Meeting"

    def test_json_export_with_transcript(self, export_service, mock_recording, mock_transcript):
        """Should include transcript in JSON export."""
        result = export_service.to_json(mock_recording, transcript=mock_transcript)

        data = json.loads(result.content)
        assert data["transcript"] is not None
        assert data["transcript"]["full_text"] == mock_transcript.full_text
        assert len(data["transcript"]["segments"]) == 3

    def test_json_export_with_analysis(self, export_service, mock_recording, mock_analysis):
        """Should include analysis in JSON export."""
        result = export_service.to_json(mock_recording, analysis=mock_analysis)

        data = json.loads(result.content)
        assert data["analysis"] is not None
        assert data["analysis"]["summary"] == mock_analysis.summary
        assert len(data["analysis"]["action_items"]) == 2

    def test_json_export_metadata(self, export_service, mock_recording):
        """Should include export metadata."""
        result = export_service.to_json(mock_recording)

        data = json.loads(result.content)
        assert "metadata" in data
        assert "exported_at" in data["metadata"]
        assert data["metadata"]["export_version"] == "1.0"

    def test_json_export_pretty_format(self, export_service, mock_recording):
        """Should format JSON with indentation by default."""
        result = export_service.to_json(mock_recording, pretty=True)

        # Pretty printed JSON has newlines
        assert "\n" in result.content

    def test_json_export_compact_format(self, export_service, mock_recording):
        """Should support compact JSON format."""
        result = export_service.to_json(mock_recording, pretty=False)

        # Compact JSON has no unnecessary newlines
        lines = result.content.strip().split("\n")
        assert len(lines) == 1

    def test_json_filename_generation(self, export_service, mock_recording):
        """Should generate appropriate filename."""
        result = export_service.to_json(mock_recording)

        assert result.filename.endswith(".json")


# -----------------------------------------------------------------------------
# Text Export Tests
# -----------------------------------------------------------------------------

class TestTextExport:
    """Tests for plain text transcript export."""

    def test_text_export_with_timestamps(self, export_service, mock_transcript):
        """Should export transcript with timestamps."""
        result = export_service.transcript_to_text(mock_transcript, include_timestamps=True)

        assert result.success is True
        assert result.format == "text"
        assert "[00:00]" in result.content
        assert "Hello everyone" in result.content

    def test_text_export_without_timestamps(self, export_service, mock_transcript):
        """Should export transcript without timestamps when requested."""
        result = export_service.transcript_to_text(mock_transcript, include_timestamps=False)

        assert result.success is True
        assert "[00:" not in result.content
        assert mock_transcript.full_text in result.content

    def test_text_filename_generation(self, export_service, mock_transcript):
        """Should generate appropriate filename."""
        result = export_service.transcript_to_text(mock_transcript)

        assert result.filename.endswith(".txt")
        assert "transcript_" in result.filename


# -----------------------------------------------------------------------------
# Action Items Export Tests
# -----------------------------------------------------------------------------

class TestActionItemsExport:
    """Tests for action items only export."""

    def test_action_items_export(self, export_service, mock_analysis):
        """Should export action items as checklist."""
        result = export_service.action_items_to_markdown(mock_analysis)

        assert result.success is True
        assert "# Action Items" in result.content
        assert "- [ ] **John**: Review the PR" in result.content
        assert "- [ ] **Sarah**: Send email to client" in result.content

    def test_action_items_export_empty(self, export_service):
        """Should handle empty action items."""
        analysis = MagicMock(spec=Analysis)
        analysis.id = 1
        analysis.action_items = []

        result = export_service.action_items_to_markdown(analysis)

        assert result.success is True
        assert "No action items found" in result.content


# -----------------------------------------------------------------------------
# Helper Method Tests
# -----------------------------------------------------------------------------

class TestHelperMethods:
    """Tests for helper methods."""

    def test_format_duration_hours(self, export_service):
        """Should format duration with hours."""
        result = export_service._format_duration(3665)  # 1h 1m 5s
        assert "1h" in result
        assert "1m" in result

    def test_format_duration_minutes(self, export_service):
        """Should format duration with minutes."""
        result = export_service._format_duration(125)  # 2m 5s
        assert "2m" in result
        assert "5s" in result

    def test_format_duration_seconds_only(self, export_service):
        """Should format duration with seconds only."""
        result = export_service._format_duration(45)
        assert "45s" in result

    def test_format_timestamp_with_hours(self, export_service):
        """Should format timestamp with hours."""
        result = export_service._format_timestamp(3661)  # 1:01:01
        assert result == "01:01:01"

    def test_format_timestamp_without_hours(self, export_service):
        """Should format timestamp without hours."""
        result = export_service._format_timestamp(65)  # 1:05
        assert result == "01:05"

    def test_generate_safe_filename(self, export_service):
        """Should generate safe filename from title."""
        result = export_service._generate_filename("Test Meeting: Q1 Review!", "md")
        assert "/" not in result
        assert ":" not in result
        assert result.endswith(".md")


# -----------------------------------------------------------------------------
# Export Result Tests
# -----------------------------------------------------------------------------

class TestExportResult:
    """Tests for ExportResult data structure."""

    def test_success_result(self):
        """Should create successful result."""
        result = ExportResult(
            success=True,
            content="# Test",
            format="markdown",
            filename="test.md"
        )
        assert result.success is True
        assert result.error_message is None

    def test_failure_result(self):
        """Should create failure result."""
        result = ExportResult(
            success=False,
            error_message="Export failed"
        )
        assert result.success is False
        assert result.error_message == "Export failed"


# -----------------------------------------------------------------------------
# API Endpoint Tests
# -----------------------------------------------------------------------------

class TestExportEndpoints:
    """Tests for export API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_export_endpoint_invalid_format(self, client):
        """Should reject invalid export format."""
        response = client.get("/api/recordings/1/export?format=pdf")

        assert response.status_code == 400
        assert "Invalid format" in response.json()["detail"]

    def test_export_endpoint_recording_not_found(self, client):
        """Should return 404 for non-existent recording."""
        response = client.get("/api/recordings/99999/export?format=markdown")

        assert response.status_code == 404
