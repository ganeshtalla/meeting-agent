"""
Meeting Agent - Models Package
==============================

This package contains SQLAlchemy ORM model definitions for the Meeting Agent.
Models define the database schema and provide an object-oriented interface
for database operations.

Exports:
    - Recording: Model for meeting recordings
    - Transcript: Model for transcription results
    - Analysis: Model for LLM analysis results

Model Relationships:
    Recording (1) <---> (1) Transcript
    Recording (1) <---> (1) Analysis
    - A recording has one optional transcript
    - A recording has one optional analysis
    - Both belong to one recording

Usage:
    from app.models import Recording, Transcript, Analysis

    # Create a new recording
    recording = Recording(
        title="Team Meeting",
        original_filename="meeting.mp3",
        file_path="/uploads/123.mp3",
        file_size=1024000,
        mime_type="audio/mpeg"
    )
    db.add(recording)
    db.commit()

    # Add a transcript to the recording
    transcript = Transcript(
        recording_id=recording.id,
        full_text="Hello everyone.",
        segments=[{"start": 0.0, "end": 2.0, "text": "Hello everyone."}]
    )
    db.add(transcript)
    db.commit()

    # Add analysis results
    analysis = Analysis(
        recording_id=recording.id,
        summary="Brief team sync meeting.",
        action_items=[{"speaker": "John", "task": "Send report"}],
        decisions=["Use PostgreSQL"]
    )
    db.add(analysis)
    db.commit()

    # Access via relationships
    print(recording.transcript.full_text)
    print(recording.analysis.summary)
"""

from .recording import Recording
from .transcript import Transcript
from .analysis import Analysis

__all__ = ["Recording", "Transcript", "Analysis"]
