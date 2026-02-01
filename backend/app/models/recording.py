"""
Meeting Agent - Recording Model
===============================

This module defines the SQLAlchemy ORM model for meeting recordings.
The Recording model represents uploaded audio/video files and tracks
their processing status through the transcription and analysis pipeline.

Packages Used:
    - sqlalchemy: SQL toolkit and ORM
        - Column: Defines a database column
        - Integer: Integer column type
        - String: Variable-length string column type
        - DateTime: Date and time column type
        - Text: Unlimited text column type
    - sqlalchemy.sql: SQL expression elements
        - func: SQL function constructs (e.g., func.now() for timestamps)

Key Components:
    - Recording: SQLAlchemy model representing the 'recordings' table

Table Schema:
    CREATE TABLE recordings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(255) NOT NULL,
        original_filename VARCHAR(255) NOT NULL,
        file_path VARCHAR(512) NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type VARCHAR(100) NOT NULL,
        duration_seconds INTEGER,
        status VARCHAR(50) NOT NULL DEFAULT 'pending',
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,
        processed_at DATETIME
    )

Usage:
    from app.models.recording import Recording

    # Create a recording
    recording = Recording(
        title="Sprint Planning",
        original_filename="planning.mp4",
        file_path="/uploads/abc123.mp4",
        file_size=52428800,
        mime_type="video/mp4"
    )

    # Update status
    recording.status = "processing"
    db.commit()
"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Recording(Base):
    """
    SQLAlchemy model for meeting recordings.

    This model stores metadata about uploaded meeting recordings and tracks
    their progress through the processing pipeline (transcription → analysis).

    Attributes:
        id (int): Primary key, auto-incremented
        title (str): User-provided or auto-generated title for the recording
        original_filename (str): Original name of the uploaded file
        file_path (str): Path where the file is stored on disk
        file_size (int): Size of the file in bytes
        mime_type (str): MIME type of the file (e.g., 'audio/wav', 'video/mp4')
        duration_seconds (int): Duration of the recording in seconds (nullable)
        status (str): Current processing status:
            - 'pending': Uploaded, waiting to be processed
            - 'processing': Currently being transcribed/analyzed
            - 'completed': Successfully processed
            - 'failed': Processing failed (see error_message)
        error_message (str): Error details if processing failed (nullable)
        created_at (datetime): Timestamp when record was created
        updated_at (datetime): Timestamp when record was last updated
        processed_at (datetime): Timestamp when processing completed (nullable)

    Table Name:
        'recordings'

    Indexes:
        - Primary key index on 'id'
    """

    # -------------------------------------------------------------------------
    # Table Configuration
    # -------------------------------------------------------------------------
    __tablename__ = "recordings"

    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------
    # Auto-incrementing integer primary key
    # index=True creates a database index for faster lookups
    id = Column(Integer, primary_key=True, index=True)

    # -------------------------------------------------------------------------
    # File Metadata
    # -------------------------------------------------------------------------
    # Title of the recording (can be user-provided or derived from filename)
    title = Column(String(255), nullable=False)

    # Original filename as uploaded by the user
    original_filename = Column(String(255), nullable=False)

    # Path to the stored file (relative to upload directory)
    file_path = Column(String(512), nullable=False)

    # File size in bytes (used for validation and display)
    file_size = Column(Integer, nullable=False)

    # MIME type for content type identification
    # Examples: 'audio/wav', 'audio/mpeg', 'video/mp4'
    mime_type = Column(String(100), nullable=False)

    # Duration in seconds (populated after audio extraction)
    duration_seconds = Column(Integer, nullable=True)

    # -------------------------------------------------------------------------
    # Processing Status
    # -------------------------------------------------------------------------
    # Current status in the processing pipeline
    # Values: 'pending', 'processing', 'completed', 'failed'
    status = Column(String(50), default="pending", nullable=False)

    # Error message if processing failed (NULL if successful)
    error_message = Column(Text, nullable=True)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    # When the record was created (auto-set by database)
    # server_default uses the database's CURRENT_TIMESTAMP function
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # When the record was last updated (auto-set on update)
    # onupdate automatically sets this when the row is modified
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # When processing completed (NULL until completed or failed)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    # One-to-one relationship with Transcript
    # uselist=False ensures a single transcript, not a list
    # cascade="all, delete-orphan" deletes transcript when recording is deleted
    transcript = relationship(
        "Transcript",
        back_populates="recording",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # One-to-one relationship with Analysis
    # Stores the LLM-generated analysis (summary, action items, decisions)
    analysis = relationship(
        "Analysis",
        back_populates="recording",
        uselist=False,
        cascade="all, delete-orphan"
    )
