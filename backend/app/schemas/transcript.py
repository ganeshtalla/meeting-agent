"""
Meeting Agent - Transcript Schemas
===================================

This module defines Pydantic schemas for transcript data validation and
serialization. Schemas handle API request/response data formatting.

Packages Used:
    - pydantic: Data validation and serialization
        - BaseModel: Base class for all schemas
        - ConfigDict: Configuration for schema behavior
        - Field: Field metadata and validation

Key Components:
    - TranscriptSegment: Schema for a single transcript segment
    - TranscriptBase: Base schema with common transcript fields
    - TranscriptCreate: Schema for creating a new transcript
    - TranscriptResponse: Schema for API responses

Usage:
    from app.schemas.transcript import TranscriptResponse, TranscriptSegment

    # In API endpoint
    @router.get("/recordings/{id}/transcript", response_model=TranscriptResponse)
    def get_transcript(id: int, db: Session = Depends(get_db)):
        transcript = db.query(Transcript).filter_by(recording_id=id).first()
        return transcript
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


# -----------------------------------------------------------------------------
# Segment Schemas
# -----------------------------------------------------------------------------

class TranscriptSegment(BaseModel):
    """
    Schema for a single transcript segment with timing.

    Segments represent time-aligned portions of the transcript,
    typically at sentence or phrase boundaries.

    Attributes:
        start (float): Start time in seconds from beginning of audio
        end (float): End time in seconds from beginning of audio
        text (str): Transcribed text for this segment
        speaker (str): Optional speaker identifier for diarization

    Example:
        {
            "start": 0.0,
            "end": 3.5,
            "text": "Hello everyone, let's start the meeting.",
            "speaker": "Speaker 1"
        }
    """
    start: float = Field(..., ge=0, description="Start time in seconds")
    end: float = Field(..., ge=0, description="End time in seconds")
    text: str = Field(..., description="Transcribed text")
    speaker: Optional[str] = Field(None, description="Speaker identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start": 0.0,
                "end": 3.5,
                "text": "Hello everyone, let's start the meeting.",
                "speaker": "Speaker 1"
            }
        }
    )


# -----------------------------------------------------------------------------
# Base Transcript Schema
# -----------------------------------------------------------------------------

class TranscriptBase(BaseModel):
    """
    Base schema with common transcript fields.

    Contains fields shared between create and response schemas.
    """
    full_text: str = Field(default="", description="Complete transcript text")
    segments: List[TranscriptSegment] = Field(
        default_factory=list,
        description="Segments with timing information"
    )
    language: str = Field(default="en", description="Language code (ISO 639-1)")
    duration_seconds: Optional[float] = Field(
        None,
        ge=0,
        description="Audio duration in seconds"
    )


# -----------------------------------------------------------------------------
# Create Schema
# -----------------------------------------------------------------------------

class TranscriptCreate(TranscriptBase):
    """
    Schema for creating a new transcript.

    Used when saving transcription results to the database.

    Attributes:
        recording_id (int): ID of the associated recording
        full_text (str): Complete transcript text
        segments (list): List of segments with timing
        language (str): Detected language code
        duration_seconds (float): Audio duration

    Example:
        transcript_data = TranscriptCreate(
            recording_id=1,
            full_text="Hello everyone.",
            segments=[
                TranscriptSegment(start=0.0, end=2.0, text="Hello everyone.")
            ],
            language="en",
            duration_seconds=2.0
        )
    """
    recording_id: int = Field(..., gt=0, description="Recording ID")


# -----------------------------------------------------------------------------
# Response Schema
# -----------------------------------------------------------------------------

class TranscriptResponse(TranscriptBase):
    """
    Schema for transcript API responses.

    Includes all transcript data plus metadata fields.

    Attributes:
        id (int): Transcript database ID
        recording_id (int): Associated recording ID
        full_text (str): Complete transcript text
        segments (list): List of segments with timing
        language (str): Language code
        duration_seconds (float): Audio duration
        word_count (int): Approximate word count
        created_at (datetime): When transcript was created

    Example Response:
        {
            "id": 1,
            "recording_id": 1,
            "full_text": "Hello everyone. Welcome to the meeting.",
            "segments": [...],
            "language": "en",
            "duration_seconds": 4.5,
            "word_count": 6,
            "created_at": "2024-01-15T10:30:00Z"
        }
    """
    id: int
    recording_id: int
    word_count: Optional[int] = None
    created_at: datetime

    # Enable ORM mode for SQLAlchemy model serialization
    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Summary Schema (for listing)
# -----------------------------------------------------------------------------

class TranscriptSummary(BaseModel):
    """
    Minimal transcript info for listing views.

    Used when including transcript info with recording lists
    without sending the full text and segments.

    Attributes:
        id (int): Transcript ID
        language (str): Language code
        duration_seconds (float): Audio duration
        word_count (int): Word count
        has_segments (bool): Whether segments are available
    """
    id: int
    language: str = "en"
    duration_seconds: Optional[float] = None
    word_count: Optional[int] = None
    has_segments: bool = False

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_transcript(cls, transcript) -> "TranscriptSummary":
        """
        Create summary from a Transcript model instance.

        Args:
            transcript: Transcript model instance

        Returns:
            TranscriptSummary: Summary of the transcript
        """
        return cls(
            id=transcript.id,
            language=transcript.language,
            duration_seconds=transcript.duration_seconds,
            word_count=transcript.word_count,
            has_segments=bool(transcript.segments)
        )
