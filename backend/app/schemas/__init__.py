"""
Meeting Agent - Schemas Package
===============================

This package contains Pydantic schema definitions for API request/response
validation and serialization.

Schemas serve as the contract between the API and its clients, defining:
- What data clients must send (request schemas)
- What data the API returns (response schemas)
- Validation rules for all fields

Exports:
    Recording Schemas (Phase 2):
    - RecordingCreate: Schema for creating recordings (request)
    - RecordingResponse: Schema for recording details (response)
    - RecordingList: Schema for list of recordings with count

    Transcript Schemas (Phase 3):
    - TranscriptSegment: Single segment with timing
    - TranscriptCreate: Schema for creating transcripts
    - TranscriptResponse: Schema for transcript API responses
    - TranscriptSummary: Minimal transcript info for listings

Usage:
    # In FastAPI endpoints
    from app.schemas import RecordingResponse, TranscriptResponse

    @app.get("/recordings/{id}", response_model=RecordingResponse)
    def get_recording(id: int):
        return db.query(Recording).get(id)

    @app.get("/recordings/{id}/transcript", response_model=TranscriptResponse)
    def get_transcript(id: int):
        recording = db.query(Recording).get(id)
        return recording.transcript
"""

from .recording import RecordingCreate, RecordingResponse, RecordingList
from .transcript import (
    TranscriptSegment,
    TranscriptCreate,
    TranscriptResponse,
    TranscriptSummary,
)
from .analysis import (
    ActionItem,
    AnalysisCreate,
    AnalysisResponse,
    AnalysisSummary,
)

__all__ = [
    # Recording schemas (Phase 2)
    "RecordingCreate",
    "RecordingResponse",
    "RecordingList",
    # Transcript schemas (Phase 3)
    "TranscriptSegment",
    "TranscriptCreate",
    "TranscriptResponse",
    "TranscriptSummary",
    # Analysis schemas (Phase 4)
    "ActionItem",
    "AnalysisCreate",
    "AnalysisResponse",
    "AnalysisSummary",
]
