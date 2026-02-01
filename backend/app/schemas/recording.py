"""
Meeting Agent - Recording Schemas
=================================

This module defines Pydantic schemas for recording-related API operations.
Schemas handle request validation and response serialization.

Packages Used:
    - pydantic: Data validation using Python type annotations
        - BaseModel: Base class for all Pydantic models
    - datetime: Date and time types
        - datetime: Datetime type for timestamps
    - typing: Type hint support
        - Optional: Marks fields that can be None

Key Components:
    - RecordingBase: Shared fields for all recording schemas
    - RecordingCreate: Request schema for creating recordings
    - RecordingResponse: Response schema with all recording details
    - RecordingList: Response schema for listing recordings

Schema Inheritance:
    RecordingBase
        ├── RecordingCreate (for POST requests)
        └── RecordingResponse (for GET responses)

Usage:
    # Creating a recording (validates input)
    data = RecordingCreate(title="Sprint Review")

    # Returning a recording (serializes output)
    @app.get("/recordings/{id}", response_model=RecordingResponse)
    def get_recording(id: int, db: Session = Depends(get_db)):
        recording = db.query(Recording).get(id)
        return recording  # Auto-converted to RecordingResponse

    # Listing recordings
    @app.get("/recordings", response_model=RecordingList)
    def list_recordings(db: Session = Depends(get_db)):
        recordings = db.query(Recording).all()
        return {"recordings": recordings, "total": len(recordings)}
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class RecordingBase(BaseModel):
    """
    Base schema with fields common to all recording operations.

    This base class contains fields that are shared between create
    requests and response schemas. Other schemas inherit from this.

    Attributes:
        title (str): Title or name of the recording
    """
    title: str


class RecordingCreate(RecordingBase):
    """
    Schema for creating a new recording.

    Used for validating POST request bodies when uploading a new recording.
    Inherits all fields from RecordingBase.

    Note:
        Most fields (file_path, file_size, etc.) are set by the server
        after the file is uploaded, not provided by the client.

    Example:
        POST /api/recordings/upload
        Content-Type: multipart/form-data

        file: [binary data]
        title: "Team Standup 2024-01-15"
    """
    pass


class RecordingResponse(RecordingBase):
    """
    Schema for recording responses.

    Used for serializing Recording model instances into JSON responses.
    Includes all fields stored in the database.

    Attributes:
        id (int): Unique identifier (database primary key)
        original_filename (str): Name of uploaded file
        file_size (int): Size in bytes
        mime_type (str): MIME type (e.g., 'audio/wav')
        duration_seconds (Optional[int]): Audio duration, null if not processed
        status (str): Processing status ('pending', 'processing', 'completed', 'failed')
        error_message (Optional[str]): Error details if status is 'failed'
        created_at (datetime): When the recording was uploaded
        updated_at (Optional[datetime]): When the record was last modified
        processed_at (Optional[datetime]): When processing completed

    Configuration:
        from_attributes: Enables conversion from SQLAlchemy model instances

    Example Response:
        {
            "id": 1,
            "title": "Team Standup",
            "original_filename": "standup.mp3",
            "file_size": 5242880,
            "mime_type": "audio/mpeg",
            "duration_seconds": 1800,
            "status": "completed",
            "error_message": null,
            "created_at": "2024-01-15T09:00:00Z",
            "updated_at": "2024-01-15T09:05:00Z",
            "processed_at": "2024-01-15T09:05:00Z"
        }
    """
    # -------------------------------------------------------------------------
    # Database-generated fields
    # -------------------------------------------------------------------------
    id: int                                    # Primary key
    original_filename: str                     # Uploaded filename
    file_path: str                             # Path to stored file
    file_size: int                             # Size in bytes
    mime_type: str                             # Content type
    duration_seconds: Optional[int] = None     # Audio length (nullable)
    status: str                                # Processing status
    error_message: Optional[str] = None        # Error if failed

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    created_at: datetime                       # Upload time
    updated_at: Optional[datetime] = None      # Last modification
    processed_at: Optional[datetime] = None    # Processing completion

    # -------------------------------------------------------------------------
    # Pydantic Configuration
    # -------------------------------------------------------------------------
    # model_config replaces the deprecated class Config
    # from_attributes enables creating schema instances from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)


class RecordingList(BaseModel):
    """
    Schema for listing multiple recordings.

    Wraps a list of recordings with metadata like total count.
    Useful for pagination and frontend state management.

    Attributes:
        recordings (list[RecordingResponse]): List of recording objects
        total (int): Total number of recordings (for pagination)

    Example Response:
        {
            "recordings": [
                {"id": 1, "title": "Meeting 1", ...},
                {"id": 2, "title": "Meeting 2", ...}
            ],
            "total": 2
        }
    """
    recordings: list[RecordingResponse]  # List of recording objects
    total: int                           # Total count for pagination
