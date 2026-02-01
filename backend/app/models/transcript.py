"""
Meeting Agent - Transcript Model
=================================

This module defines the SQLAlchemy ORM model for storing transcription results.
The Transcript model stores the full transcribed text and individual segments
with timing information.

Packages Used:
    - sqlalchemy: SQL toolkit and ORM
        - Column: Defines a database column
        - Integer, String, Float, Text: Column types
        - DateTime: Date and time column type
        - ForeignKey: Defines foreign key relationship
        - JSON: JSON column type for storing segments
    - sqlalchemy.orm: ORM relationship management
        - relationship: Defines model relationships
    - sqlalchemy.sql: SQL expression elements
        - func: SQL function constructs

Key Components:
    - Transcript: SQLAlchemy model for transcription results

Table Schema:
    CREATE TABLE transcripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recording_id INTEGER NOT NULL REFERENCES recordings(id),
        full_text TEXT NOT NULL,
        segments JSON NOT NULL,
        language VARCHAR(10) NOT NULL DEFAULT 'en',
        duration_seconds FLOAT,
        word_count INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )

Segment JSON Structure:
    [
        {
            "start": 0.0,
            "end": 3.5,
            "text": "Hello everyone.",
            "speaker": null
        },
        ...
    ]

Usage:
    from app.models.transcript import Transcript

    # Create a transcript record
    transcript = Transcript(
        recording_id=1,
        full_text="Hello everyone. Welcome to the meeting.",
        segments=[
            {"start": 0.0, "end": 2.0, "text": "Hello everyone."},
            {"start": 2.0, "end": 4.5, "text": "Welcome to the meeting."}
        ],
        language="en",
        duration_seconds=4.5
    )
    db.add(transcript)
    db.commit()
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Transcript(Base):
    """
    SQLAlchemy model for storing transcription results.

    This model stores both the complete transcript text and individual
    segments with timing information for timestamp-based navigation.

    Attributes:
        id (int): Primary key, auto-incremented
        recording_id (int): Foreign key to the recordings table
        full_text (str): Complete transcript as a single text block
        segments (list): JSON array of segments with start, end, text, speaker
        language (str): Detected or specified language code (e.g., 'en', 'es')
        duration_seconds (float): Total audio duration in seconds
        word_count (int): Approximate word count for display
        created_at (datetime): Timestamp when transcript was created

    Relationships:
        recording: Many-to-one relationship with Recording model

    Table Name:
        'transcripts'

    Indexes:
        - Primary key index on 'id'
        - Foreign key index on 'recording_id'
    """

    # -------------------------------------------------------------------------
    # Table Configuration
    # -------------------------------------------------------------------------
    __tablename__ = "transcripts"

    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)

    # -------------------------------------------------------------------------
    # Foreign Key Relationship
    # -------------------------------------------------------------------------
    # Reference to the parent recording
    # ondelete="CASCADE" ensures transcript is deleted when recording is deleted
    recording_id = Column(
        Integer,
        ForeignKey("recordings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # -------------------------------------------------------------------------
    # Transcript Content
    # -------------------------------------------------------------------------
    # Complete transcript text (concatenated from all segments)
    # Using Text type for unlimited length
    full_text = Column(Text, nullable=False, default="")

    # Segments with timing information stored as JSON
    # Each segment: {"start": float, "end": float, "text": str, "speaker": str|null}
    # JSON type provides native JSON support in SQLite/PostgreSQL
    segments = Column(JSON, nullable=False, default=list)

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------
    # Detected or specified language code (ISO 639-1)
    # Examples: 'en' (English), 'es' (Spanish), 'fr' (French)
    language = Column(String(10), nullable=False, default="en")

    # Total duration of the audio in seconds
    # Useful for display and validation
    duration_seconds = Column(Float, nullable=True)

    # Approximate word count for quick stats
    # Calculated when transcript is created
    word_count = Column(Integer, nullable=True)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    # When the transcript was created
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    # back_populates creates a bidirectional relationship
    # The Recording model will have a 'transcript' attribute
    recording = relationship("Recording", back_populates="transcript")

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def calculate_word_count(self) -> int:
        """
        Calculate and set the word count from full_text.

        Returns:
            int: Number of words in the transcript
        """
        if self.full_text:
            self.word_count = len(self.full_text.split())
        else:
            self.word_count = 0
        return self.word_count

    def get_segment_at_time(self, time_seconds: float) -> dict | None:
        """
        Get the segment that contains the specified time.

        Args:
            time_seconds: Time position in seconds

        Returns:
            dict: Segment data or None if no segment at that time
        """
        for segment in self.segments:
            if segment["start"] <= time_seconds <= segment["end"]:
                return segment
        return None

    def get_text_between(self, start: float, end: float) -> str:
        """
        Get transcript text between two timestamps.

        Args:
            start: Start time in seconds
            end: End time in seconds

        Returns:
            str: Concatenated text from segments in the time range
        """
        texts = []
        for segment in self.segments:
            # Include segment if it overlaps with the time range
            if segment["start"] < end and segment["end"] > start:
                texts.append(segment["text"])
        return " ".join(texts)
