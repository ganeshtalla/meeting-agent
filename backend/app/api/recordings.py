"""
Meeting Agent - Recordings API Endpoints
========================================

This module provides REST API endpoints for managing meeting recordings.
Includes file upload, listing, and retrieval operations.

Packages Used:
    - fastapi: Web framework
        - APIRouter: Groups related endpoints
        - Depends: Dependency injection
        - UploadFile: Handle file uploads
        - File: File parameter declaration
        - HTTPException: Raise HTTP errors
        - status: HTTP status code constants
    - sqlalchemy.orm: ORM session management
        - Session: Database session type

Key Components:
    - router: FastAPI router for recording endpoints
    - upload_recording: POST endpoint for file uploads
    - list_recordings: GET endpoint for listing recordings
    - get_recording: GET endpoint for single recording

Endpoints:
    POST /api/recordings/upload - Upload a new recording
    GET  /api/recordings        - List all recordings
    GET  /api/recordings/{id}   - Get recording by ID

Usage:
    # Upload via curl
    curl -X POST http://localhost:8000/api/recordings/upload \
        -F "file=@meeting.wav"

    # List recordings
    curl http://localhost:8000/api/recordings

    # Get specific recording
    curl http://localhost:8000/api/recordings/1
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

from app.db.database import get_db
from app.models.recording import Recording
from app.schemas.recording import RecordingResponse, RecordingList
from app.services.storage import StorageService, ALLOWED_EXTENSIONS
from app.config import settings


# -----------------------------------------------------------------------------
# Router Configuration
# -----------------------------------------------------------------------------
# Create router with prefix and tags for API documentation grouping
router = APIRouter(prefix="/recordings", tags=["recordings"])

# -----------------------------------------------------------------------------
# Dependency: Storage Service
# -----------------------------------------------------------------------------
def get_storage_service() -> StorageService:
    """
    Dependency that provides a StorageService instance.

    Returns:
        StorageService: Configured storage service

    Note:
        This could be extended to support different storage backends
        (e.g., S3, GCS) by returning different implementations.
    """
    return StorageService()


# -----------------------------------------------------------------------------
# Upload Endpoint
# -----------------------------------------------------------------------------
@router.post(
    "/upload",
    response_model=RecordingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a recording",
    description="Upload an audio or video file for transcription and analysis."
)
async def upload_recording(
    file: UploadFile = File(..., description="Audio or video file to upload"),
    title: Optional[str] = Form(None, description="Optional title for the recording"),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
) -> Recording:
    """
    Upload a new recording file.

    This endpoint:
    1. Validates the file type (must be audio or video)
    2. Validates the file size (must be under limit)
    3. Creates a database record
    4. Saves the file to disk
    5. Returns the recording details

    Args:
        file: The uploaded file (multipart/form-data)
        title: Optional title (defaults to filename without extension)
        db: Database session (injected)
        storage: Storage service (injected)

    Returns:
        Recording: The created recording with ID and status

    Raises:
        HTTPException 400: Invalid file type
        HTTPException 413: File too large
        HTTPException 500: Storage error

    Example Response:
        {
            "id": 1,
            "title": "Team Meeting",
            "original_filename": "meeting.wav",
            "file_size": 5242880,
            "mime_type": "audio/wav",
            "status": "pending",
            "created_at": "2024-01-15T10:00:00Z"
        }
    """
    # -------------------------------------------------------------------------
    # Validate File Type
    # -------------------------------------------------------------------------
    # Check MIME type from upload
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine file type"
        )

    # Check if MIME type is allowed
    if not storage.is_valid_mime_type(file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. "
                   f"Allowed types: audio/wav, audio/mpeg, video/mp4, etc."
        )

    # Also validate file extension as backup check
    if file.filename and not storage.is_valid_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # -------------------------------------------------------------------------
    # Validate File Size
    # -------------------------------------------------------------------------
    # Read file to get size (also needed for saving)
    # Note: For very large files, consider streaming validation
    file_content = await file.read()
    file_size = len(file_content)

    # Check against max size
    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {file_size / (1024*1024):.1f}MB. "
                   f"Maximum allowed: {settings.max_file_size_mb}MB"
        )

    # Check for empty file
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded"
        )

    # -------------------------------------------------------------------------
    # Create Database Record
    # -------------------------------------------------------------------------
    # Generate title from filename if not provided
    if not title:
        # Remove extension and use filename as title
        title = os.path.splitext(file.filename or "Untitled")[0]

    # Create recording model instance
    recording = Recording(
        title=title,
        original_filename=file.filename or "unknown",
        file_path="",  # Will be updated after saving
        file_size=file_size,
        mime_type=file.content_type,
        status="pending"
    )

    # Add to database and flush to get ID
    db.add(recording)
    db.flush()  # Assigns ID without committing transaction

    # -------------------------------------------------------------------------
    # Save File to Disk
    # -------------------------------------------------------------------------
    try:
        # Reset file position after reading for size check
        await file.seek(0)

        # Save file using storage service
        # We need to write from the content we already read
        from io import BytesIO
        file_buffer = BytesIO(file_content)

        file_path = storage.save_file(
            file_obj=file_buffer,
            recording_id=recording.id,
            original_filename=file.filename or "unknown"
        )

        # Update recording with file path (relative to upload dir)
        recording.file_path = str(file_path)

        # Commit the transaction
        db.commit()
        db.refresh(recording)

    except Exception as e:
        # Rollback database changes on storage error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    return recording


# -----------------------------------------------------------------------------
# List Recordings Endpoint
# -----------------------------------------------------------------------------
@router.get(
    "",
    response_model=RecordingList,
    summary="List all recordings",
    description="Get a list of all recordings, ordered by creation date (newest first)."
)
def list_recordings(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
) -> dict:
    """
    List all recordings with optional filtering.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        status_filter: Optional filter by status (pending, processing, completed, failed)
        db: Database session (injected)

    Returns:
        dict: Object with recordings list and total count

    Example Response:
        {
            "recordings": [
                {"id": 2, "title": "Planning", "status": "completed", ...},
                {"id": 1, "title": "Standup", "status": "pending", ...}
            ],
            "total": 2
        }
    """
    # Build query
    query = db.query(Recording)

    # Apply status filter if provided
    if status_filter:
        query = query.filter(Recording.status == status_filter)

    # Get total count before pagination
    total = query.count()

    # Apply ordering and pagination
    # Order by created_at DESC, then by ID DESC for stable ordering
    # when multiple records have the same timestamp
    recordings = (
        query
        .order_by(Recording.created_at.desc(), Recording.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {"recordings": recordings, "total": total}


# -----------------------------------------------------------------------------
# Get Single Recording Endpoint
# -----------------------------------------------------------------------------
@router.get(
    "/{recording_id}",
    response_model=RecordingResponse,
    summary="Get recording by ID",
    description="Get details of a specific recording."
)
def get_recording(
    recording_id: int,
    db: Session = Depends(get_db)
) -> Recording:
    """
    Get a single recording by ID.

    Args:
        recording_id: The database ID of the recording
        db: Database session (injected)

    Returns:
        Recording: The recording details

    Raises:
        HTTPException 404: Recording not found

    Example:
        GET /api/recordings/1

        Response:
        {
            "id": 1,
            "title": "Team Meeting",
            "status": "completed",
            ...
        }
    """
    # Query for the recording
    recording = db.query(Recording).filter(Recording.id == recording_id).first()

    # Raise 404 if not found
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording with ID {recording_id} not found"
        )

    return recording


# -----------------------------------------------------------------------------
# Delete Recording Endpoint
# -----------------------------------------------------------------------------
@router.delete(
    "/{recording_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a recording",
    description="Delete a recording and its associated file."
)
def delete_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
) -> None:
    """
    Delete a recording and its file.

    Args:
        recording_id: The database ID of the recording
        db: Database session (injected)
        storage: Storage service (injected)

    Raises:
        HTTPException 404: Recording not found

    Note:
        This permanently deletes the recording and file.
        The operation cannot be undone.
    """
    # Query for the recording
    recording = db.query(Recording).filter(Recording.id == recording_id).first()

    # Raise 404 if not found
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording with ID {recording_id} not found"
        )

    # Delete the file from storage
    from pathlib import Path
    file_path = Path(recording.file_path)
    storage.delete_file(file_path)

    # Delete from database
    db.delete(recording)
    db.commit()


# -----------------------------------------------------------------------------
# Process Recording Endpoint
# -----------------------------------------------------------------------------
@router.post(
    "/{recording_id}/process",
    summary="Process a recording",
    description="Start processing a recording (audio extraction, transcription, analysis)."
)
async def process_recording(
    recording_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """
    Start processing a recording in the background.

    This endpoint triggers the processing pipeline which:
    1. Extracts audio from the recording (if video)
    2. Transcribes the audio using Whisper
    3. Analyzes the transcript using LLM

    Processing runs in the background - use the WebSocket endpoint
    or poll the recording status to track progress.

    Args:
        recording_id: ID of the recording to process
        background_tasks: FastAPI background tasks handler
        db: Database session (injected)

    Returns:
        dict: Confirmation message with recording ID

    Raises:
        HTTPException 404: Recording not found
        HTTPException 400: Recording already processed/processing

    Example:
        POST /api/recordings/1/process

        Response:
        {
            "message": "Processing started",
            "recording_id": 1,
            "status": "processing"
        }
    """
    # Query for the recording
    recording = db.query(Recording).filter(Recording.id == recording_id).first()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording with ID {recording_id} not found"
        )

    # Check if already processing or completed
    if recording.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording is already being processed"
        )

    if recording.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording has already been processed. Delete and re-upload to reprocess."
        )

    # Add processing task to background
    background_tasks.add_task(run_pipeline, recording_id)

    return {
        "message": "Processing started",
        "recording_id": recording_id,
        "status": "processing"
    }


def run_pipeline(recording_id: int) -> None:
    """
    Run the processing pipeline in background.

    This function is executed as a background task. It creates its own
    database session since the original request session may be closed.

    Args:
        recording_id: ID of recording to process
    """
    import asyncio
    from app.db.database import SessionLocal
    from app.services.pipeline import ProcessingPipeline
    from app.api.websocket import broadcast_status, manager

    # Create new database session for background task
    db = SessionLocal()

    try:
        pipeline = ProcessingPipeline(db)

        # Create callback to broadcast status updates via WebSocket
        def status_callback(status):
            # Check if there are any WebSocket connections
            if manager.has_connections(recording_id):
                # Run async broadcast in sync context
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                loop.run_until_complete(broadcast_status(recording_id, status))

        # Run pipeline with callback
        result = pipeline.process(recording_id, callback=status_callback)

        if result.success:
            logger.info(f"Pipeline completed for recording {recording_id}")
        else:
            logger.error(f"Pipeline failed for recording {recording_id}: {result.error_message}")

    except Exception as e:
        logger.error(f"Pipeline error for recording {recording_id}: {e}")
        # Update recording status to failed
        recording = db.query(Recording).filter(Recording.id == recording_id).first()
        if recording:
            recording.status = "failed"
            recording.error_message = str(e)
            db.commit()
    finally:
        db.close()


# -----------------------------------------------------------------------------
# Get Recording with Details Endpoint
# -----------------------------------------------------------------------------
@router.get(
    "/{recording_id}/details",
    summary="Get recording with full details",
    description="Get recording with transcript and analysis details."
)
def get_recording_details(
    recording_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get a recording with its transcript and analysis.

    Args:
        recording_id: ID of the recording
        db: Database session (injected)

    Returns:
        dict: Recording with transcript and analysis

    Raises:
        HTTPException 404: Recording not found
    """
    recording = db.query(Recording).filter(Recording.id == recording_id).first()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording with ID {recording_id} not found"
        )

    result = {
        "id": recording.id,
        "title": recording.title,
        "original_filename": recording.original_filename,
        "file_size": recording.file_size,
        "mime_type": recording.mime_type,
        "duration_seconds": recording.duration_seconds,
        "status": recording.status,
        "error_message": recording.error_message,
        "created_at": recording.created_at,
        "processed_at": recording.processed_at,
        "transcript": None,
        "analysis": None
    }

    # Add transcript if exists
    if recording.transcript:
        result["transcript"] = {
            "id": recording.transcript.id,
            "full_text": recording.transcript.full_text,
            "segments": recording.transcript.segments,
            "language": recording.transcript.language,
            "duration_seconds": recording.transcript.duration_seconds
        }

    # Add analysis if exists
    if recording.analysis:
        result["analysis"] = {
            "id": recording.analysis.id,
            "summary": recording.analysis.summary,
            "action_items": recording.analysis.action_items,
            "decisions": recording.analysis.decisions,
            "key_topics": recording.analysis.key_topics,
            "model_used": recording.analysis.model_used
        }

    return result


# -----------------------------------------------------------------------------
# Export Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/{recording_id}/export",
    summary="Export recording",
    description="Export recording data in various formats (markdown, json, text)."
)
def export_recording(
    recording_id: int,
    format: str = "markdown",
    db: Session = Depends(get_db)
):
    """
    Export a recording in the specified format.

    Supported formats:
    - markdown: Formatted document with summary, action items, transcript
    - json: Complete data export for integrations
    - text: Plain text transcript only

    Args:
        recording_id: ID of the recording to export
        format: Export format (markdown, json, text)
        db: Database session (injected)

    Returns:
        Response with exported content and appropriate headers

    Raises:
        HTTPException 404: Recording not found
        HTTPException 400: Invalid format
    """
    from fastapi.responses import Response
    from app.services.export import ExportService

    logger.info(f"Export request: recording={recording_id}, format={format}")

    # Validate format
    valid_formats = ["markdown", "json", "text"]
    if format not in valid_formats:
        logger.warning(f"Invalid export format: {format}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format '{format}'. Valid formats: {', '.join(valid_formats)}"
        )

    # Get recording
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording with ID {recording_id} not found"
        )

    logger.info(f"Exporting recording: {recording.title}")

    # Get related data
    transcript = recording.transcript
    analysis = recording.analysis

    # Export
    export_service = ExportService()

    if format == "markdown":
        result = export_service.to_markdown(recording, transcript, analysis)
        content_type = "text/markdown; charset=utf-8"
    elif format == "json":
        result = export_service.to_json(recording, transcript, analysis)
        content_type = "application/json; charset=utf-8"
    else:  # text
        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript available for text export"
            )
        result = export_service.transcript_to_text(transcript)
        content_type = "text/plain; charset=utf-8"

    if not result.success:
        logger.error(f"Export failed: {result.error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {result.error_message}"
        )

    logger.info(f"Export successful: {result.filename}")

    return Response(
        content=result.content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"'
        }
    )


@router.get(
    "/{recording_id}/export/action-items",
    summary="Export action items",
    description="Export only the action items as a Markdown checklist."
)
def export_action_items(
    recording_id: int,
    db: Session = Depends(get_db)
):
    """
    Export only action items from a recording's analysis.

    Args:
        recording_id: ID of the recording
        db: Database session (injected)

    Returns:
        Markdown formatted action items checklist

    Raises:
        HTTPException 404: Recording or analysis not found
    """
    from fastapi.responses import Response
    from app.services.export import ExportService

    logger.info(f"Export action items request: recording={recording_id}")

    # Get recording
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording with ID {recording_id} not found"
        )

    if not recording.analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis available for this recording"
        )

    export_service = ExportService()
    result = export_service.action_items_to_markdown(recording.analysis)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {result.error_message}"
        )

    return Response(
        content=result.content,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"'
        }
    )
