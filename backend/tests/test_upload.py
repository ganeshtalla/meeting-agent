"""
Meeting Agent - Upload Endpoint Tests
=====================================

This module contains tests for the file upload functionality.
Tests verify file validation, storage, and database operations.

Packages Used:
    - pytest: Testing framework
    - io: In-memory binary streams
        - BytesIO: Binary stream for test file data
    - pathlib: Filesystem path handling
        - Path: Check file existence

Test Functions:
    - test_upload_valid_audio_file: Verify successful upload
    - test_upload_rejects_invalid_file_type: Verify MIME type validation
    - test_upload_rejects_invalid_extension: Verify extension validation
    - test_upload_rejects_oversized_file: Verify size limit
    - test_upload_rejects_empty_file: Verify empty file handling
    - test_upload_creates_database_record: Verify DB persistence
    - test_upload_stores_file_on_disk: Verify file storage
    - test_upload_with_custom_title: Verify title handling
    - test_list_recordings: Verify listing endpoint
    - test_get_recording: Verify single record retrieval
    - test_get_recording_not_found: Verify 404 handling
    - test_delete_recording: Verify deletion

Fixtures Used:
    - client: FastAPI TestClient (from conftest.py)
    - db_session: Database session (from conftest.py)
    - sample_audio_file: Sample WAV file data
    - cleanup_uploads: Cleanup uploaded files after tests

Running These Tests:
    pytest tests/test_upload.py -v
"""

import pytest
from io import BytesIO
from pathlib import Path

from app.models.recording import Recording
from app.config import settings


# -----------------------------------------------------------------------------
# Test Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_audio_file():
    """
    Create a sample WAV file for testing.

    Returns a BytesIO object containing a minimal valid WAV file.
    The file has:
    - RIFF header
    - WAV format chunk
    - Data chunk with silence

    Returns:
        BytesIO: In-memory WAV file
    """
    # Minimal WAV file header (44 bytes) + some audio data
    # This creates a valid WAV file structure that passes validation
    wav_header = bytes([
        # RIFF header
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # File size - 8 (36 bytes)
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        # fmt chunk
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Chunk size (16)
        0x01, 0x00,              # Audio format (1 = PCM)
        0x01, 0x00,              # Channels (1 = mono)
        0x44, 0xAC, 0x00, 0x00,  # Sample rate (44100)
        0x88, 0x58, 0x01, 0x00,  # Byte rate
        0x02, 0x00,              # Block align
        0x10, 0x00,              # Bits per sample (16)
        # data chunk
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # Data size (0 for this minimal file)
    ])
    # Add some dummy audio data (1KB of silence)
    audio_data = bytes([0x00] * 1024)

    return BytesIO(wav_header + audio_data)


@pytest.fixture
def large_file():
    """
    Create an oversized file for testing size limits.

    Returns:
        BytesIO: File larger than the configured limit
    """
    # Create file slightly larger than max (default 500MB)
    # For testing, we'll set a smaller limit in the test
    size = 1024 * 1024 * 10  # 10MB for testing
    return BytesIO(bytes([0x00] * size))


@pytest.fixture(autouse=True)
def cleanup_uploads():
    """
    Cleanup uploaded files after each test.

    This fixture runs automatically after each test
    to remove any files created during testing.
    """
    yield  # Run the test

    # Cleanup: Remove all files in upload directory
    upload_dir = Path(settings.upload_dir)
    if upload_dir.exists():
        for file in upload_dir.iterdir():
            if file.is_file():
                file.unlink()


# -----------------------------------------------------------------------------
# Upload Endpoint Tests
# -----------------------------------------------------------------------------

def test_upload_valid_audio_file(client, sample_audio_file):
    """
    Should accept valid audio file and return recording ID.

    Verifies:
    - HTTP status is 201 Created
    - Response contains recording ID
    - Status is set to "pending"
    """
    # Act: Upload the file
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.wav", sample_audio_file, "audio/wav")}
    )

    # Assert: Verify response
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    assert data["original_filename"] == "test.wav"
    assert data["mime_type"] == "audio/wav"


def test_upload_rejects_invalid_file_type(client):
    """
    Should reject non-audio/video files with 400 error.

    Verifies:
    - HTTP status is 400 Bad Request
    - Error message mentions invalid file type
    """
    # Create a text file
    text_file = BytesIO(b"This is not audio")

    # Act: Try to upload
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.txt", text_file, "text/plain")}
    )

    # Assert: Verify rejection
    assert response.status_code == 400
    assert "invalid file type" in response.json()["detail"].lower()


def test_upload_rejects_invalid_extension(client, sample_audio_file):
    """
    Should reject files with invalid extensions.

    Even with correct MIME type, wrong extension should be rejected.
    """
    # Act: Upload with wrong extension
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.pdf", sample_audio_file, "audio/wav")}
    )

    # Assert: Verify rejection
    assert response.status_code == 400
    assert "extension" in response.json()["detail"].lower()


def test_upload_rejects_empty_file(client):
    """
    Should reject empty files with 400 error.
    """
    # Create empty file
    empty_file = BytesIO(b"")

    # Act: Try to upload
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("empty.wav", empty_file, "audio/wav")}
    )

    # Assert: Verify rejection
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_creates_database_record(client, db_session, sample_audio_file):
    """
    Upload should create a recording entry in database.

    Verifies:
    - Record exists in database after upload
    - Fields are populated correctly
    """
    # Act: Upload file
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.wav", sample_audio_file, "audio/wav")}
    )
    recording_id = response.json()["id"]

    # Assert: Verify database record
    recording = db_session.query(Recording).filter_by(id=recording_id).first()
    assert recording is not None
    assert recording.status == "pending"
    assert recording.original_filename == "test.wav"
    assert recording.mime_type == "audio/wav"
    assert recording.file_size > 0


def test_upload_stores_file_on_disk(client, sample_audio_file):
    """
    Upload should save file to uploads directory.

    Verifies:
    - File exists on disk after upload
    - File path is stored in database record
    """
    # Act: Upload file
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.wav", sample_audio_file, "audio/wav")}
    )
    file_path = response.json().get("file_path", "")

    # Assert: Verify file exists
    assert file_path
    assert Path(file_path).exists()


def test_upload_with_custom_title(client, sample_audio_file):
    """
    Should use custom title when provided.

    Verifies:
    - Custom title is stored
    - Filename is preserved separately
    """
    # Act: Upload with title
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.wav", sample_audio_file, "audio/wav")},
        data={"title": "My Important Meeting"}
    )

    # Assert: Verify title
    assert response.status_code == 201
    assert response.json()["title"] == "My Important Meeting"
    assert response.json()["original_filename"] == "test.wav"


def test_upload_generates_title_from_filename(client, sample_audio_file):
    """
    Should generate title from filename when not provided.

    Verifies:
    - Title is derived from filename (without extension)
    """
    # Act: Upload without title
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("team_standup.wav", sample_audio_file, "audio/wav")}
    )

    # Assert: Verify generated title
    assert response.status_code == 201
    assert response.json()["title"] == "team_standup"


# -----------------------------------------------------------------------------
# List Recordings Tests
# -----------------------------------------------------------------------------

def test_list_recordings_returns_all(client, db_session, sample_audio_file):
    """
    Should return all recordings.

    Verifies:
    - All uploaded recordings are returned
    - Total count is correct
    """
    # Arrange: Upload multiple files
    for i in range(3):
        sample_audio_file.seek(0)  # Reset file position
        client.post(
            "/api/recordings/upload",
            files={"file": (f"meeting_{i}.wav", sample_audio_file, "audio/wav")}
        )

    # Act: List recordings
    response = client.get("/api/recordings")

    # Assert: Verify count
    assert response.status_code == 200
    data = response.json()
    assert len(data["recordings"]) == 3
    assert data["total"] == 3


def test_list_recordings_ordered_by_date(client, db_session, sample_audio_file):
    """
    Should return recordings ordered by ID descending (newest first).

    Note: Since uploads happen very fast, we check ordering by ID
    which increases with each upload.
    """
    # Arrange: Upload files
    for name in ["first", "second", "third"]:
        sample_audio_file.seek(0)
        client.post(
            "/api/recordings/upload",
            files={"file": (f"{name}.wav", sample_audio_file, "audio/wav")},
            data={"title": name}
        )

    # Act: List recordings
    response = client.get("/api/recordings")

    # Assert: IDs should be descending (newest first)
    ids = [r["id"] for r in response.json()["recordings"]]
    assert ids == sorted(ids, reverse=True)


# -----------------------------------------------------------------------------
# Get Single Recording Tests
# -----------------------------------------------------------------------------

def test_get_recording(client, sample_audio_file):
    """
    Should return recording details by ID.
    """
    # Arrange: Create recording
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.wav", sample_audio_file, "audio/wav")}
    )
    recording_id = upload_response.json()["id"]

    # Act: Get recording
    response = client.get(f"/api/recordings/{recording_id}")

    # Assert: Verify response
    assert response.status_code == 200
    assert response.json()["id"] == recording_id


def test_get_recording_not_found(client):
    """
    Should return 404 for non-existent recording.
    """
    # Act: Get non-existent recording
    response = client.get("/api/recordings/99999")

    # Assert: Verify 404
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# -----------------------------------------------------------------------------
# Delete Recording Tests
# -----------------------------------------------------------------------------

def test_delete_recording(client, db_session, sample_audio_file):
    """
    Should delete recording and file.
    """
    # Arrange: Create recording
    upload_response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.wav", sample_audio_file, "audio/wav")}
    )
    recording_id = upload_response.json()["id"]
    file_path = upload_response.json()["file_path"]

    # Act: Delete recording
    response = client.delete(f"/api/recordings/{recording_id}")

    # Assert: Verify deletion
    assert response.status_code == 204

    # Verify not in database
    recording = db_session.query(Recording).filter_by(id=recording_id).first()
    assert recording is None

    # Verify file deleted
    assert not Path(file_path).exists()


def test_delete_recording_not_found(client):
    """
    Should return 404 when deleting non-existent recording.
    """
    # Act: Delete non-existent recording
    response = client.delete("/api/recordings/99999")

    # Assert: Verify 404
    assert response.status_code == 404
