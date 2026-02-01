"""
Meeting Agent - Export Service
==============================

This module provides export functionality for meeting recordings,
transcripts, and analysis results in various formats.

Packages Used:
    - json: JSON serialization
    - datetime: Date formatting
    - pathlib: File path handling
    - typing: Type hints
    - logging: Export logging

Supported Formats:
    - Markdown: Human-readable format for documentation
    - JSON: Machine-readable format for integrations
    - Text: Plain text transcript

Usage:
    from app.services.export import ExportService

    export = ExportService()

    # Export to Markdown
    markdown = export.to_markdown(recording, transcript, analysis)

    # Export to JSON
    json_data = export.to_json(recording, transcript, analysis)

    # Export transcript only
    text = export.transcript_to_text(transcript)
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.analysis import Analysis


# Configure logging
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------

@dataclass
class ExportResult:
    """
    Result of an export operation.

    Attributes:
        success: Whether export was successful
        content: The exported content (string)
        format: Export format (markdown, json, text)
        filename: Suggested filename for download
        error_message: Error details if failed
    """
    success: bool
    content: str = ""
    format: str = ""
    filename: str = ""
    error_message: Optional[str] = None


# -----------------------------------------------------------------------------
# Export Service
# -----------------------------------------------------------------------------

class ExportService:
    """
    Service for exporting meeting data to various formats.

    Supports:
    - Markdown: Formatted document with summary, action items, transcript
    - JSON: Complete data export for integrations
    - Text: Plain text transcript with timestamps

    Example:
        export = ExportService()

        # Export complete meeting data
        result = export.to_markdown(recording, transcript, analysis)
        if result.success:
            with open(result.filename, 'w') as f:
                f.write(result.content)
    """

    def __init__(self):
        """Initialize the export service."""
        logger.info("Initializing ExportService")

    def to_markdown(
        self,
        recording: Recording,
        transcript: Optional[Transcript] = None,
        analysis: Optional[Analysis] = None
    ) -> ExportResult:
        """
        Export meeting data to Markdown format.

        Args:
            recording: Recording model instance
            transcript: Optional transcript model
            analysis: Optional analysis model

        Returns:
            ExportResult with Markdown content
        """
        logger.info(f"Exporting recording {recording.id} to Markdown")

        try:
            lines = []

            # Header
            lines.append(f"# {recording.title}")
            lines.append("")

            # Metadata
            lines.append("## Meeting Details")
            lines.append("")
            lines.append(f"- **Date**: {self._format_datetime(recording.created_at)}")
            if recording.duration_seconds:
                lines.append(f"- **Duration**: {self._format_duration(recording.duration_seconds)}")
            lines.append(f"- **Original File**: {recording.original_filename}")
            lines.append(f"- **Status**: {recording.status}")
            lines.append("")

            # Analysis section
            if analysis:
                lines.append("---")
                lines.append("")

                # Summary
                if analysis.summary:
                    lines.append("## Summary")
                    lines.append("")
                    lines.append(analysis.summary)
                    lines.append("")

                # Action Items
                if analysis.action_items:
                    lines.append("## Action Items")
                    lines.append("")
                    for item in analysis.action_items:
                        speaker = item.get('speaker', 'Unknown')
                        task = item.get('task', 'N/A')
                        due_date = item.get('due_date')
                        priority = item.get('priority')

                        line = f"- [ ] **{speaker}**: {task}"
                        if due_date:
                            line += f" *(Due: {due_date})*"
                        if priority:
                            line += f" `{priority}`"
                        lines.append(line)
                    lines.append("")

                # Decisions
                if analysis.decisions:
                    lines.append("## Decisions Made")
                    lines.append("")
                    for decision in analysis.decisions:
                        lines.append(f"- {decision}")
                    lines.append("")

                # Key Topics
                if analysis.key_topics:
                    lines.append("## Key Topics")
                    lines.append("")
                    lines.append(", ".join(f"`{topic}`" for topic in analysis.key_topics))
                    lines.append("")

            # Transcript section
            if transcript and transcript.full_text:
                lines.append("---")
                lines.append("")
                lines.append("## Transcript")
                lines.append("")
                lines.append(f"*Language: {transcript.language}*")
                lines.append("")

                if transcript.segments:
                    # Format with timestamps
                    for segment in transcript.segments:
                        start = segment.get('start', 0)
                        text = segment.get('text', '').strip()
                        timestamp = self._format_timestamp(start)
                        lines.append(f"**[{timestamp}]** {text}")
                        lines.append("")
                else:
                    # Plain text
                    lines.append(transcript.full_text)
                    lines.append("")

            # Footer
            lines.append("---")
            lines.append("")
            lines.append(f"*Generated by Meeting Agent on {self._format_datetime(datetime.utcnow())}*")

            content = "\n".join(lines)
            filename = self._generate_filename(recording.title, "md")

            logger.info(f"✓ Markdown export complete: {len(content)} characters")

            return ExportResult(
                success=True,
                content=content,
                format="markdown",
                filename=filename
            )

        except Exception as e:
            logger.error(f"✗ Markdown export failed: {e}")
            return ExportResult(
                success=False,
                error_message=str(e)
            )

    def to_json(
        self,
        recording: Recording,
        transcript: Optional[Transcript] = None,
        analysis: Optional[Analysis] = None,
        pretty: bool = True
    ) -> ExportResult:
        """
        Export meeting data to JSON format.

        Args:
            recording: Recording model instance
            transcript: Optional transcript model
            analysis: Optional analysis model
            pretty: Whether to format JSON with indentation

        Returns:
            ExportResult with JSON content
        """
        logger.info(f"Exporting recording {recording.id} to JSON")

        try:
            data = {
                "recording": {
                    "id": recording.id,
                    "title": recording.title,
                    "original_filename": recording.original_filename,
                    "file_size": recording.file_size,
                    "mime_type": recording.mime_type,
                    "duration_seconds": recording.duration_seconds,
                    "status": recording.status,
                    "created_at": self._format_datetime_iso(recording.created_at),
                    "processed_at": self._format_datetime_iso(recording.processed_at),
                },
                "transcript": None,
                "analysis": None,
                "metadata": {
                    "exported_at": self._format_datetime_iso(datetime.utcnow()),
                    "export_version": "1.0"
                }
            }

            if transcript:
                data["transcript"] = {
                    "id": transcript.id,
                    "full_text": transcript.full_text,
                    "segments": transcript.segments,
                    "language": transcript.language,
                    "duration_seconds": transcript.duration_seconds
                }

            if analysis:
                data["analysis"] = {
                    "id": analysis.id,
                    "summary": analysis.summary,
                    "action_items": analysis.action_items,
                    "decisions": analysis.decisions,
                    "key_topics": analysis.key_topics,
                    "model_used": analysis.model_used
                }

            indent = 2 if pretty else None
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            filename = self._generate_filename(recording.title, "json")

            logger.info(f"✓ JSON export complete: {len(content)} characters")

            return ExportResult(
                success=True,
                content=content,
                format="json",
                filename=filename
            )

        except Exception as e:
            logger.error(f"✗ JSON export failed: {e}")
            return ExportResult(
                success=False,
                error_message=str(e)
            )

    def transcript_to_text(
        self,
        transcript: Transcript,
        include_timestamps: bool = True
    ) -> ExportResult:
        """
        Export transcript to plain text format.

        Args:
            transcript: Transcript model instance
            include_timestamps: Whether to include timestamps

        Returns:
            ExportResult with plain text content
        """
        logger.info(f"Exporting transcript {transcript.id} to text")

        try:
            lines = []

            if include_timestamps and transcript.segments:
                for segment in transcript.segments:
                    start = segment.get('start', 0)
                    text = segment.get('text', '').strip()
                    timestamp = self._format_timestamp(start)
                    lines.append(f"[{timestamp}] {text}")
            else:
                lines.append(transcript.full_text)

            content = "\n".join(lines)
            filename = f"transcript_{transcript.id}.txt"

            logger.info(f"✓ Text export complete: {len(content)} characters")

            return ExportResult(
                success=True,
                content=content,
                format="text",
                filename=filename
            )

        except Exception as e:
            logger.error(f"✗ Text export failed: {e}")
            return ExportResult(
                success=False,
                error_message=str(e)
            )

    def action_items_to_markdown(self, analysis: Analysis) -> ExportResult:
        """
        Export only action items to Markdown checklist.

        Args:
            analysis: Analysis model instance

        Returns:
            ExportResult with Markdown checklist
        """
        logger.info(f"Exporting action items from analysis {analysis.id}")

        try:
            lines = ["# Action Items", ""]

            if not analysis.action_items:
                lines.append("*No action items found.*")
            else:
                for item in analysis.action_items:
                    speaker = item.get('speaker', 'Unknown')
                    task = item.get('task', 'N/A')
                    due_date = item.get('due_date')

                    line = f"- [ ] **{speaker}**: {task}"
                    if due_date:
                        line += f" *(Due: {due_date})*"
                    lines.append(line)

            content = "\n".join(lines)
            filename = f"action_items_{analysis.id}.md"

            logger.info(f"✓ Action items export complete: {len(analysis.action_items)} items")

            return ExportResult(
                success=True,
                content=content,
                format="markdown",
                filename=filename
            )

        except Exception as e:
            logger.error(f"✗ Action items export failed: {e}")
            return ExportResult(
                success=False,
                error_message=str(e)
            )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _format_datetime(self, dt: Optional[datetime]) -> str:
        """Format datetime for display."""
        if not dt:
            return "N/A"
        return dt.strftime("%B %d, %Y at %H:%M")

    def _format_datetime_iso(self, dt: Optional[datetime]) -> Optional[str]:
        """Format datetime as ISO 8601."""
        if not dt:
            return None
        return dt.isoformat()

    def _format_duration(self, seconds: int) -> str:
        """Format duration in human-readable format."""
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp as HH:MM:SS."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def _generate_filename(self, title: str, extension: str) -> str:
        """Generate a safe filename from title."""
        # Remove unsafe characters
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
        safe_title = safe_title.strip().replace(" ", "_")[:50]

        timestamp = datetime.utcnow().strftime("%Y%m%d")

        return f"{safe_title}_{timestamp}.{extension}"
