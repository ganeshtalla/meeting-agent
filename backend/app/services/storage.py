"""
Meeting Agent - File Storage Service
=====================================

This module handles file storage operations for uploaded recordings.
It manages saving files to disk and generating unique filenames.

Packages Used:
    - pathlib: Object-oriented filesystem paths
        - Path: Cross-platform path handling
    - uuid: Universally unique identifier generation
        - uuid4: Generate random UUID
    - shutil: High-level file operations
        - copyfileobj: Efficiently copy file data
    - os: Operating system interfaces
        - makedirs: Create directories recursively

Key Components:
    - StorageService: Class for handling file storage operations
    - ALLOWED_MIME_TYPES: Set of accepted audio/video MIME types
    - ALLOWED_EXTENSIONS: Set of accepted file extensions

Usage:
    from app.services.storage import StorageService

    storage = StorageService()

    # Save uploaded file
    file_path = storage.save_file(upload_file, recording_id=123)

    # Delete file
    storage.delete_file(file_path)

    # Validate file type
    is_valid = storage.is_valid_file_type("audio/wav")
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

from app.config import settings


# -----------------------------------------------------------------------------
# Allowed File Types
# -----------------------------------------------------------------------------
# Set of MIME types accepted for upload.
# Includes common audio and video formats that can be processed.
ALLOWED_MIME_TYPES = {
    # Audio formats
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",       # MP3
    "audio/mp3",
    "audio/mp4",        # M4A
    "audio/x-m4a",
    "audio/aac",
    "audio/ogg",
    "audio/flac",
    "audio/webm",
    # Video formats (audio will be extracted)
    "video/mp4",
    "video/mpeg",
    "video/webm",
    "video/quicktime",  # MOV
    "video/x-msvideo",  # AVI
    "video/x-matroska", # MKV
}

# Set of allowed file extensions (lowercase, without dot)
ALLOWED_EXTENSIONS = {
    # Audio
    "wav", "mp3", "m4a", "aac", "ogg", "flac", "webm",
    # Video
    "mp4", "mpeg", "mpg", "mov", "avi", "mkv",
}


class StorageService:
    """
    Service for handling file storage operations.

    This service manages:
    - Saving uploaded files to disk
    - Generating unique filenames
    - Validating file types
    - Deleting files

    Attributes:
        upload_dir (Path): Directory for storing uploaded files
        max_file_size (int): Maximum file size in bytes

    Example:
        storage = StorageService()

        # Save a file
        path = storage.save_file(file_obj, recording_id=1)
        print(path)  # "/uploads/1_abc123.wav"

        # Check if file type is valid
        if storage.is_valid_file_type("audio/wav"):
            print("Valid!")
    """

    def __init__(self, upload_dir: Optional[Path] = None):
        """
        Initialize the storage service.

        Args:
            upload_dir: Custom upload directory. Defaults to settings.upload_dir

        Creates the upload directory if it doesn't exist.
        """
        # Use provided directory or fall back to settings
        self.upload_dir = upload_dir or settings.upload_dir

        # Convert to absolute path if relative
        if not self.upload_dir.is_absolute():
            self.upload_dir = Path.cwd() / self.upload_dir

        # Calculate max file size in bytes (from MB in settings)
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024

        # Ensure upload directory exists
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """
        Create the upload directory if it doesn't exist.

        Uses os.makedirs with exist_ok=True to handle concurrent creation
        and avoid race conditions.
        """
        os.makedirs(self.upload_dir, exist_ok=True)

    def generate_filename(self, recording_id: int, original_filename: str) -> str:
        """
        Generate a unique filename for storage.

        Format: {recording_id}_{uuid}.{extension}
        Example: 123_a1b2c3d4.wav

        Args:
            recording_id: Database ID of the recording
            original_filename: Original filename from upload

        Returns:
            Unique filename string

        Note:
            Using UUID ensures uniqueness even if same file is uploaded twice.
            Including recording_id makes it easy to associate files with records.
        """
        # Extract extension from original filename (lowercase)
        extension = Path(original_filename).suffix.lower()

        # Generate unique identifier
        unique_id = uuid.uuid4().hex[:8]  # First 8 chars of UUID

        # Combine into final filename
        return f"{recording_id}_{unique_id}{extension}"

    def save_file(
        self,
        file_obj: BinaryIO,
        recording_id: int,
        original_filename: str
    ) -> Path:
        """
        Save an uploaded file to disk.

        Args:
            file_obj: File-like object with read() method
            recording_id: Database ID for the recording
            original_filename: Original filename from upload

        Returns:
            Path: Full path to the saved file

        Raises:
            IOError: If file cannot be written

        Example:
            with open("upload.wav", "rb") as f:
                path = storage.save_file(f, recording_id=1, original_filename="meeting.wav")
        """
        # Generate unique filename
        filename = self.generate_filename(recording_id, original_filename)

        # Create full path
        file_path = self.upload_dir / filename

        # Write file to disk
        # Using shutil.copyfileobj for efficient streaming copy
        with open(file_path, "wb") as dest:
            shutil.copyfileobj(file_obj, dest)

        return file_path

    def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path to the file to delete

        Returns:
            bool: True if deleted, False if file didn't exist

        Note:
            This method is safe to call even if the file doesn't exist.
            It will simply return False in that case.
        """
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except OSError:
            return False

    def get_file_path(self, filename: str) -> Path:
        """
        Get the full path for a filename.

        Args:
            filename: Name of the file (not full path)

        Returns:
            Path: Full path to the file in upload directory
        """
        return self.upload_dir / filename

    @staticmethod
    def is_valid_mime_type(mime_type: str) -> bool:
        """
        Check if a MIME type is allowed for upload.

        Args:
            mime_type: MIME type string (e.g., "audio/wav")

        Returns:
            bool: True if MIME type is allowed

        Example:
            StorageService.is_valid_mime_type("audio/wav")  # True
            StorageService.is_valid_mime_type("text/plain")  # False
        """
        return mime_type.lower() in ALLOWED_MIME_TYPES

    @staticmethod
    def is_valid_extension(filename: str) -> bool:
        """
        Check if a file extension is allowed.

        Args:
            filename: Filename or path to check

        Returns:
            bool: True if extension is allowed

        Example:
            StorageService.is_valid_extension("meeting.wav")  # True
            StorageService.is_valid_extension("document.pdf")  # False
        """
        extension = Path(filename).suffix.lower().lstrip(".")
        return extension in ALLOWED_EXTENSIONS

    @staticmethod
    def get_extension(filename: str) -> str:
        """
        Extract the file extension from a filename.

        Args:
            filename: Filename or path

        Returns:
            str: Lowercase extension without dot

        Example:
            StorageService.get_extension("Meeting.WAV")  # "wav"
        """
        return Path(filename).suffix.lower().lstrip(".")
