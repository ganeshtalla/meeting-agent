"""
Meeting Agent - Audio Processing Service
=========================================

This module provides audio extraction and processing capabilities using FFmpeg
and pydub. It handles converting video files to audio and preparing audio
files for transcription (16kHz mono WAV format).

Packages Used:
    - subprocess: Execute FFmpeg commands
        - run(): Execute a command and wait for completion
        - CalledProcessError: Exception for failed commands
    - pydub: Audio manipulation library
        - AudioSegment: Main class for audio operations
    - pathlib: Object-oriented filesystem paths
        - Path: Cross-platform path handling
    - logging: Standard logging for error tracking
    - shutil: High-level file operations
        - which(): Find executable path

Key Components:
    - AudioService: Main service class for audio processing
    - AudioExtractionResult: Result dataclass for extraction operations

System Requirements:
    - FFmpeg must be installed and available in PATH
    - Install on Ubuntu: sudo apt install ffmpeg
    - Install on macOS: brew install ffmpeg

Whisper Audio Requirements:
    - Sample rate: 16kHz
    - Channels: Mono (1 channel)
    - Format: WAV (recommended for best quality)

Usage:
    from app.services.audio import AudioService

    audio_service = AudioService()

    # Check if FFmpeg is available
    if audio_service.is_ffmpeg_available():
        # Extract audio from video
        result = audio_service.extract_audio(
            input_path=Path("/uploads/video.mp4"),
            output_path=Path("/processed/audio.wav")
        )
        if result.success:
            print(f"Duration: {result.duration_seconds}s")
"""

import subprocess
import shutil
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from pydub import AudioSegment

from app.config import settings

# Configure logging for this module
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Result Data Classes
# -----------------------------------------------------------------------------

@dataclass
class AudioExtractionResult:
    """
    Result of an audio extraction operation.

    Attributes:
        success (bool): Whether extraction completed successfully
        output_path (Path): Path to the extracted audio file (if successful)
        duration_seconds (float): Duration of the audio in seconds
        sample_rate (int): Sample rate of the output audio (Hz)
        channels (int): Number of audio channels (1=mono, 2=stereo)
        error_message (str): Error description if extraction failed
    """
    success: bool
    output_path: Optional[Path] = None
    duration_seconds: float = 0.0
    sample_rate: int = 16000
    channels: int = 1
    error_message: Optional[str] = None


@dataclass
class AudioInfo:
    """
    Information about an audio file.

    Attributes:
        duration_seconds (float): Duration in seconds
        sample_rate (int): Sample rate in Hz
        channels (int): Number of channels
        format (str): Audio format (e.g., 'wav', 'mp3')
    """
    duration_seconds: float
    sample_rate: int
    channels: int
    format: str


# -----------------------------------------------------------------------------
# Audio Service Class
# -----------------------------------------------------------------------------

class AudioService:
    """
    Service for audio extraction and processing.

    This service handles:
    - Extracting audio tracks from video files
    - Converting audio to Whisper-compatible format (16kHz mono WAV)
    - Getting audio file information

    All operations use FFmpeg for reliable media handling.

    Attributes:
        output_dir (Path): Directory for processed audio files
        target_sample_rate (int): Target sample rate for output (16000 Hz)
        target_channels (int): Target channel count (1 for mono)

    Example:
        service = AudioService()
        result = service.extract_audio(video_path, output_path)
        if result.success:
            print(f"Extracted {result.duration_seconds}s of audio")
    """

    # Target format for Whisper transcription
    TARGET_SAMPLE_RATE = 16000  # 16kHz
    TARGET_CHANNELS = 1         # Mono
    TARGET_FORMAT = "wav"

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the audio service.

        Args:
            output_dir: Directory for processed files. Defaults to settings.processed_dir
        """
        self.output_dir = output_dir or settings.processed_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # FFmpeg Availability Check
    # -------------------------------------------------------------------------

    @staticmethod
    def is_ffmpeg_available() -> bool:
        """
        Check if FFmpeg is installed and available in PATH.

        Returns:
            bool: True if FFmpeg is available, False otherwise

        Example:
            if AudioService.is_ffmpeg_available():
                print("FFmpeg is ready")
            else:
                print("Please install FFmpeg")
        """
        return shutil.which("ffmpeg") is not None

    # -------------------------------------------------------------------------
    # Audio Extraction
    # -------------------------------------------------------------------------

    def extract_audio(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        target_sample_rate: int = TARGET_SAMPLE_RATE,
        target_channels: int = TARGET_CHANNELS
    ) -> AudioExtractionResult:
        """
        Extract and convert audio from a media file to Whisper-compatible format.

        This method:
        1. Validates the input file exists
        2. Extracts audio track (for video files) or converts (for audio files)
        3. Converts to 16kHz mono WAV format for optimal Whisper performance

        Args:
            input_path: Path to the input media file (video or audio)
            output_path: Path for output WAV file. If None, auto-generates in output_dir
            target_sample_rate: Output sample rate in Hz (default: 16000)
            target_channels: Output channel count (default: 1 for mono)

        Returns:
            AudioExtractionResult: Contains success status, output path, duration, etc.

        Raises:
            FileNotFoundError: If input file doesn't exist

        Example:
            result = service.extract_audio(
                Path("/uploads/meeting.mp4"),
                Path("/processed/meeting.wav")
            )
            if result.success:
                print(f"Audio saved to: {result.output_path}")
                print(f"Duration: {result.duration_seconds:.2f}s")

        FFmpeg Command Explanation:
            ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav
            -i: Input file
            -vn: No video (extract audio only)
            -acodec pcm_s16le: 16-bit PCM audio codec
            -ar 16000: Sample rate 16kHz
            -ac 1: 1 channel (mono)
        """
        # Validate input file exists
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Check FFmpeg availability
        if not self.is_ffmpeg_available():
            return AudioExtractionResult(
                success=False,
                error_message="FFmpeg is not installed or not in PATH"
            )

        # Generate output path if not provided
        if output_path is None:
            output_path = self.output_dir / f"{input_path.stem}.wav"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Build FFmpeg command
            # -y: Overwrite output file without asking
            # -i: Input file path
            # -vn: No video output (discard video stream)
            # -acodec pcm_s16le: Use 16-bit PCM codec (lossless)
            # -ar: Set audio sample rate
            # -ac: Set number of audio channels
            # -hide_banner: Suppress FFmpeg banner
            # -loglevel error: Only show errors
            cmd = [
                "ffmpeg",
                "-y",                           # Overwrite output
                "-hide_banner",                 # Clean output
                "-loglevel", "error",           # Only errors
                "-i", str(input_path),          # Input file
                "-vn",                          # No video
                "-acodec", "pcm_s16le",         # 16-bit PCM
                "-ar", str(target_sample_rate), # Sample rate
                "-ac", str(target_channels),    # Channels
                str(output_path)                # Output file
            ]

            logger.info(f"Extracting audio from {input_path} to {output_path}")

            # Execute FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown FFmpeg error"
                logger.error(f"FFmpeg failed: {error_msg}")
                return AudioExtractionResult(
                    success=False,
                    error_message=f"FFmpeg error: {error_msg}"
                )

            # Verify output file was created
            if not output_path.exists():
                return AudioExtractionResult(
                    success=False,
                    error_message="Output file was not created"
                )

            # Get duration using pydub
            audio = AudioSegment.from_wav(str(output_path))
            duration_seconds = len(audio) / 1000.0  # pydub uses milliseconds

            logger.info(f"Audio extraction successful: {duration_seconds:.2f}s")

            return AudioExtractionResult(
                success=True,
                output_path=output_path,
                duration_seconds=duration_seconds,
                sample_rate=target_sample_rate,
                channels=target_channels
            )

        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg timeout for file: {input_path}")
            return AudioExtractionResult(
                success=False,
                error_message="Audio extraction timed out (exceeded 10 minutes)"
            )
        except Exception as e:
            logger.error(f"Audio extraction failed: {str(e)}")
            return AudioExtractionResult(
                success=False,
                error_message=f"Extraction failed: {str(e)}"
            )

    # -------------------------------------------------------------------------
    # Audio Information
    # -------------------------------------------------------------------------

    def get_audio_info(self, file_path: Path) -> Optional[AudioInfo]:
        """
        Get information about an audio file.

        Args:
            file_path: Path to the audio file

        Returns:
            AudioInfo: Audio file metadata, or None if file can't be read

        Example:
            info = service.get_audio_info(Path("/audio/meeting.wav"))
            if info:
                print(f"Duration: {info.duration_seconds}s")
                print(f"Sample rate: {info.sample_rate}Hz")
        """
        try:
            if not file_path.exists():
                return None

            # Use pydub to read audio info
            audio = AudioSegment.from_file(str(file_path))

            return AudioInfo(
                duration_seconds=len(audio) / 1000.0,
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                format=file_path.suffix.lstrip(".")
            )
        except Exception as e:
            logger.error(f"Failed to get audio info for {file_path}: {e}")
            return None

    # -------------------------------------------------------------------------
    # Audio Validation
    # -------------------------------------------------------------------------

    def is_whisper_compatible(self, file_path: Path) -> bool:
        """
        Check if an audio file is compatible with Whisper (16kHz mono WAV).

        Args:
            file_path: Path to the audio file

        Returns:
            bool: True if file is Whisper-compatible, False otherwise
        """
        info = self.get_audio_info(file_path)
        if info is None:
            return False

        return (
            info.sample_rate == self.TARGET_SAMPLE_RATE and
            info.channels == self.TARGET_CHANNELS and
            info.format == "wav"
        )

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def delete_processed_file(self, file_path: Path) -> bool:
        """
        Delete a processed audio file.

        Args:
            file_path: Path to the file to delete

        Returns:
            bool: True if file was deleted, False otherwise
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted processed file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
            return False
