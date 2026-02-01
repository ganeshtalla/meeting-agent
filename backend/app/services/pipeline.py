"""
Meeting Agent - Processing Pipeline Service
============================================

This module provides the ProcessingPipeline service that orchestrates the
complete recording processing flow: audio extraction → transcription → analysis.

Packages Used:
    - pathlib: Cross-platform path handling
    - typing: Type hints
    - dataclasses: Result structures
    - datetime: Timestamps
    - logging: Pipeline logging

Key Components:
    - ProcessingPipeline: Main orchestration class
    - PipelineStatus: Status tracking dataclass
    - PipelineCallback: Protocol for status updates

Pipeline Stages:
    1. EXTRACTING: Extract audio from video (if needed)
    2. TRANSCRIBING: Convert speech to text using Whisper
    3. ANALYZING: Generate summary and action items using LLM
    4. COMPLETED/FAILED: Final status

Usage:
    from app.services.pipeline import ProcessingPipeline
    from app.db.database import SessionLocal

    db = SessionLocal()
    pipeline = ProcessingPipeline(db)

    # Process with callback for status updates
    def on_status(status):
        print(f"Stage: {status.stage}, Progress: {status.progress}%")

    result = pipeline.process(recording_id=1, callback=on_status)

    if result.success:
        print(f"Completed in {result.duration_seconds}s")
    else:
        print(f"Failed: {result.error_message}")
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Protocol, List
import logging
import time

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.config import settings
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.analysis import Analysis
from app.services.audio import AudioService
from app.services.transcription import TranscriptionService
from app.services.analyzer import AnalyzerService


# Configure logging
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Enums and Data Structures
# -----------------------------------------------------------------------------

class PipelineStage(str, Enum):
    """Stages in the processing pipeline."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStatus:
    """
    Current status of pipeline processing.

    Attributes:
        recording_id: ID of the recording being processed
        stage: Current pipeline stage
        progress: Progress percentage (0-100)
        message: Human-readable status message
        error: Error message if failed
        started_at: When processing started
        updated_at: When status was last updated
    """
    recording_id: int
    stage: PipelineStage
    progress: int = 0
    message: str = ""
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "recording_id": self.recording_id,
            "stage": self.stage.value,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class PipelineResult:
    """
    Result of pipeline processing.

    Attributes:
        success: Whether processing completed successfully
        recording_id: ID of the processed recording
        transcript_id: ID of created transcript (if successful)
        analysis_id: ID of created analysis (if successful)
        duration_seconds: Total processing time
        error_message: Error details (if failed)
    """
    success: bool
    recording_id: int
    transcript_id: Optional[int] = None
    analysis_id: Optional[int] = None
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


# Type alias for status callback function
StatusCallback = Callable[[PipelineStatus], None]


# -----------------------------------------------------------------------------
# Processing Pipeline
# -----------------------------------------------------------------------------

class ProcessingPipeline:
    """
    Orchestrates the complete recording processing flow.

    The pipeline processes recordings through these stages:
    1. Audio Extraction: Convert video to audio or validate audio format
    2. Transcription: Use Whisper to convert speech to text
    3. Analysis: Use LLM to extract summary, action items, decisions

    Attributes:
        db: Database session for persistence
        audio_service: Audio extraction service
        transcription_service: Whisper transcription service
        analyzer_service: LLM analysis service

    Example:
        pipeline = ProcessingPipeline(db_session)
        result = pipeline.process(recording_id=1)

        if result.success:
            print("Processing completed!")
        else:
            print(f"Failed: {result.error_message}")
    """

    def __init__(
        self,
        db: Session,
        audio_service: Optional[AudioService] = None,
        transcription_service: Optional[TranscriptionService] = None,
        analyzer_service: Optional[AnalyzerService] = None
    ):
        """
        Initialize the pipeline with services.

        Args:
            db: SQLAlchemy database session
            audio_service: Optional custom AudioService instance
            transcription_service: Optional custom TranscriptionService instance
            analyzer_service: Optional custom AnalyzerService instance
        """
        logger.info("Initializing ProcessingPipeline")
        self.db = db
        self.audio_service = audio_service or AudioService()
        self.transcription_service = transcription_service or TranscriptionService()
        self.analyzer_service = analyzer_service or AnalyzerService()

        logger.debug(f"  Audio service: {type(self.audio_service).__name__}")
        logger.debug(f"  Transcription service: {type(self.transcription_service).__name__}")
        logger.debug(f"  Analyzer service: {type(self.analyzer_service).__name__}")

        # Track active processing status
        self._current_status: Optional[PipelineStatus] = None
        self._callback: Optional[StatusCallback] = None

    def process(
        self,
        recording_id: int,
        callback: Optional[StatusCallback] = None
    ) -> PipelineResult:
        """
        Process a recording through the complete pipeline.

        Args:
            recording_id: ID of the recording to process
            callback: Optional function to receive status updates

        Returns:
            PipelineResult: Result with success status and IDs

        Raises:
            ValueError: If recording not found
        """
        self._callback = callback
        start_time = time.time()

        logger.info(f"{'='*60}")
        logger.info(f"PIPELINE START - Recording ID: {recording_id}")
        logger.info(f"{'='*60}")

        # Get recording from database
        logger.debug(f"Fetching recording {recording_id} from database...")
        recording = self.db.query(Recording).filter(
            Recording.id == recording_id
        ).first()

        if not recording:
            logger.error(f"Recording {recording_id} not found in database")
            raise ValueError(f"Recording with ID {recording_id} not found")

        logger.info(f"Recording found: '{recording.title}'")
        logger.info(f"  File: {recording.file_path}")
        try:
            size_mb = recording.file_size / 1024 / 1024
            logger.info(f"  Size: {size_mb:.2f} MB")
        except (TypeError, AttributeError):
            logger.info(f"  Size: {recording.file_size}")
        logger.info(f"  MIME: {recording.mime_type}")
        logger.info(f"  Status: {recording.status}")

        # Initialize status
        self._update_status(PipelineStatus(
            recording_id=recording_id,
            stage=PipelineStage.PENDING,
            progress=0,
            message="Starting processing...",
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ))

        try:
            # Update recording status to processing
            logger.info("Updating recording status to 'processing'")
            recording.status = "processing"
            self.db.commit()

            # Stage 1: Audio Extraction
            logger.info(f"\n{'─'*40}")
            logger.info("STAGE 1: AUDIO EXTRACTION")
            logger.info(f"{'─'*40}")
            audio_path = self._extract_audio(recording)
            logger.info(f"Audio extraction complete: {audio_path}")

            # Stage 2: Transcription
            logger.info(f"\n{'─'*40}")
            logger.info("STAGE 2: TRANSCRIPTION")
            logger.info(f"{'─'*40}")
            transcript = self._transcribe_audio(recording, audio_path)
            logger.info(f"Transcription complete: {len(transcript.full_text)} characters")

            # Stage 3: Analysis
            logger.info(f"\n{'─'*40}")
            logger.info("STAGE 3: LLM ANALYSIS")
            logger.info(f"{'─'*40}")
            analysis = self._analyze_transcript(recording, transcript)

            # Mark as completed
            logger.info(f"\n{'─'*40}")
            logger.info("PIPELINE COMPLETE")
            logger.info(f"{'─'*40}")
            recording.status = "completed"
            recording.processed_at = func.now()
            self.db.commit()

            self._update_status(PipelineStatus(
                recording_id=recording_id,
                stage=PipelineStage.COMPLETED,
                progress=100,
                message="Processing completed successfully",
                started_at=self._current_status.started_at if self._current_status else None,
                updated_at=datetime.utcnow()
            ))

            duration = time.time() - start_time
            logger.info(f"{'='*60}")
            logger.info(f"PIPELINE SUCCESS - Recording {recording_id}")
            logger.info(f"  Duration: {duration:.2f}s")
            logger.info(f"  Transcript ID: {transcript.id if transcript else 'N/A'}")
            logger.info(f"  Analysis ID: {analysis.id if analysis else 'N/A'}")
            logger.info(f"{'='*60}\n")

            return PipelineResult(
                success=True,
                recording_id=recording_id,
                transcript_id=transcript.id if transcript else None,
                analysis_id=analysis.id if analysis else None,
                duration_seconds=duration
            )

        except Exception as e:
            # Mark as failed
            error_message = str(e)
            logger.error(f"\n{'='*60}")
            logger.error(f"PIPELINE FAILED - Recording {recording_id}")
            logger.error(f"  Error: {error_message}")
            logger.error(f"{'='*60}\n")

            recording.status = "failed"
            recording.error_message = error_message
            recording.processed_at = func.now()
            self.db.commit()

            self._update_status(PipelineStatus(
                recording_id=recording_id,
                stage=PipelineStage.FAILED,
                progress=0,
                message="Processing failed",
                error=error_message,
                started_at=self._current_status.started_at if self._current_status else None,
                updated_at=datetime.utcnow()
            ))

            duration = time.time() - start_time
            logger.error(f"Recording {recording_id} failed after {duration:.2f}s: {e}")

            return PipelineResult(
                success=False,
                recording_id=recording_id,
                duration_seconds=duration,
                error_message=error_message
            )

    def _extract_audio(self, recording: Recording) -> Path:
        """
        Extract audio from recording file.

        Args:
            recording: Recording model instance

        Returns:
            Path to the extracted/validated audio file

        Raises:
            Exception: If audio extraction fails
        """
        logger.info("Starting audio extraction...")
        self._update_status(PipelineStatus(
            recording_id=recording.id,
            stage=PipelineStage.EXTRACTING,
            progress=10,
            message="Extracting audio...",
            started_at=self._current_status.started_at if self._current_status else None,
            updated_at=datetime.utcnow()
        ))

        input_path = Path(recording.file_path)
        logger.debug(f"  Input file: {input_path}")
        logger.debug(f"  File exists: {input_path.exists()}")

        # Check if already Whisper-compatible
        logger.debug("Checking if audio is already Whisper-compatible...")
        if self.audio_service.is_whisper_compatible(input_path):
            logger.info("✓ Audio already Whisper-compatible (16kHz mono WAV)")
            logger.info(f"  Using original file: {input_path}")
            return input_path

        # Extract/convert audio
        logger.info("Audio needs conversion to Whisper format")
        output_path = settings.processed_dir / f"{recording.id}_audio.wav"
        logger.debug(f"  Output path: {output_path}")

        logger.info("Running FFmpeg conversion...")
        extraction_start = time.time()
        result = self.audio_service.extract_audio(input_path, output_path)
        extraction_time = time.time() - extraction_start

        if not result.success:
            logger.error(f"✗ Audio extraction failed: {result.error_message}")
            raise Exception(f"Audio extraction failed: {result.error_message}")

        logger.info(f"✓ Audio extraction successful")
        logger.info(f"  Duration: {result.duration_seconds:.1f}s")
        logger.info(f"  Sample rate: {result.sample_rate}Hz")
        logger.info(f"  Channels: {result.channels}")
        logger.info(f"  Extraction time: {extraction_time:.2f}s")
        logger.info(f"  Output: {result.output_path}")

        # Update recording duration
        recording.duration_seconds = int(result.duration_seconds)
        self.db.commit()

        self._update_status(PipelineStatus(
            recording_id=recording.id,
            stage=PipelineStage.EXTRACTING,
            progress=25,
            message=f"Audio extracted ({result.duration_seconds:.1f}s)",
            started_at=self._current_status.started_at if self._current_status else None,
            updated_at=datetime.utcnow()
        ))

        return result.output_path

    def _transcribe_audio(self, recording: Recording, audio_path: Path) -> Transcript:
        """
        Transcribe audio to text.

        Args:
            recording: Recording model instance
            audio_path: Path to audio file

        Returns:
            Created Transcript model instance

        Raises:
            Exception: If transcription fails
        """
        provider = self.transcription_service.provider
        logger.info(f"Starting transcription with {provider}...")
        logger.debug(f"  Audio file: {audio_path}")
        if provider == "whisper":
            logger.debug(f"  Model: {self.transcription_service.model_size}")

        self._update_status(PipelineStatus(
            recording_id=recording.id,
            stage=PipelineStage.TRANSCRIBING,
            progress=30,
            message="Transcribing audio...",
            started_at=self._current_status.started_at if self._current_status else None,
            updated_at=datetime.utcnow()
        ))

        # Transcribe
        logger.info("Running Whisper transcription (this may take a while)...")
        transcription_start = time.time()
        result = self.transcription_service.transcribe(audio_path)
        transcription_time = time.time() - transcription_start

        if not result.success:
            logger.error(f"✗ Transcription failed: {result.error_message}")
            raise Exception(f"Transcription failed: {result.error_message}")

        logger.info(f"✓ Transcription successful")
        logger.info(f"  Provider: {result.provider}")
        logger.info(f"  Language detected: {result.language}")
        logger.info(f"  Duration: {result.duration_seconds:.1f}s")
        logger.info(f"  Segments: {len(result.segments)}")
        if result.has_speakers:
            logger.info(f"  Speakers detected: {result.speaker_count}")
        logger.info(f"  Text length: {len(result.full_text)} characters")
        logger.info(f"  Transcription time: {transcription_time:.2f}s")
        logger.info(f"  Speed: {result.duration_seconds / transcription_time:.1f}x realtime")

        # Show first 200 chars of transcript
        preview = result.full_text[:200].replace('\n', ' ')
        if len(result.full_text) > 200:
            preview += "..."
        logger.info(f"  Preview: \"{preview}\"")

        # Update progress
        self._update_status(PipelineStatus(
            recording_id=recording.id,
            stage=PipelineStage.TRANSCRIBING,
            progress=60,
            message=f"Transcribed {len(result.segments)} segments",
            started_at=self._current_status.started_at if self._current_status else None,
            updated_at=datetime.utcnow()
        ))

        # Convert segments to dict format for JSON storage
        logger.debug("Converting segments to dict format...")
        segments_dict = TranscriptionService.segments_to_dict(result.segments)

        # Create transcript record
        logger.debug("Saving transcript to database...")
        transcript = Transcript(
            recording_id=recording.id,
            full_text=result.full_text,
            segments=segments_dict,
            language=result.language,
            duration_seconds=result.duration_seconds
        )
        self.db.add(transcript)
        self.db.commit()
        self.db.refresh(transcript)

        # Update recording duration if not already set
        if not recording.duration_seconds:
            recording.duration_seconds = int(result.duration_seconds)
            self.db.commit()

        logger.info(f"✓ Transcript saved to database (ID: {transcript.id})")

        return transcript

    def _analyze_transcript(self, recording: Recording, transcript: Transcript) -> Optional[Analysis]:
        """
        Analyze transcript with LLM.

        Args:
            recording: Recording model instance
            transcript: Transcript model instance

        Returns:
            Created Analysis model instance, or None if analysis unavailable

        Note:
            Analysis is optional - if Ollama is not available, the pipeline
            continues without analysis rather than failing.
        """
        logger.info("Starting LLM analysis...")
        logger.debug(f"  Model: {self.analyzer_service.model}")
        logger.debug(f"  Transcript length: {len(transcript.full_text)} characters")

        self._update_status(PipelineStatus(
            recording_id=recording.id,
            stage=PipelineStage.ANALYZING,
            progress=70,
            message="Analyzing transcript...",
            started_at=self._current_status.started_at if self._current_status else None,
            updated_at=datetime.utcnow()
        ))

        # Check if analyzer is available
        logger.debug("Checking Ollama availability...")
        if not self.analyzer_service.is_available():
            logger.warning("⚠ Ollama not available - skipping analysis")
            logger.warning("  Start Ollama with: ollama serve")
            self._update_status(PipelineStatus(
                recording_id=recording.id,
                stage=PipelineStage.ANALYZING,
                progress=90,
                message="Analysis skipped (Ollama not available)",
                started_at=self._current_status.started_at if self._current_status else None,
                updated_at=datetime.utcnow()
            ))
            return None

        logger.info(f"Ollama available, using model: {self.analyzer_service.model}")

        # Analyze transcript
        logger.info("Sending transcript to LLM for analysis...")
        analysis_start = time.time()
        result = self.analyzer_service.analyze(transcript.full_text)
        analysis_time = time.time() - analysis_start

        if not result.success:
            logger.warning(f"⚠ Analysis failed: {result.error_message}")
            logger.warning("  Pipeline will continue without analysis")
            return None

        logger.info(f"✓ LLM analysis successful")
        logger.info(f"  Analysis time: {analysis_time:.2f}s")
        logger.info(f"  Summary: {result.summary[:100]}..." if len(result.summary) > 100 else f"  Summary: {result.summary}")
        logger.info(f"  Action items: {len(result.action_items)}")
        for i, item in enumerate(result.action_items[:3], 1):
            logger.info(f"    {i}. {item.speaker}: {item.task}")
        if len(result.action_items) > 3:
            logger.info(f"    ... and {len(result.action_items) - 3} more")
        logger.info(f"  Decisions: {len(result.decisions)}")
        logger.info(f"  Key topics: {len(result.key_topics)}")

        self._update_status(PipelineStatus(
            recording_id=recording.id,
            stage=PipelineStage.ANALYZING,
            progress=90,
            message=f"Analysis complete: {len(result.action_items)} action items",
            started_at=self._current_status.started_at if self._current_status else None,
            updated_at=datetime.utcnow()
        ))

        # Convert action items to dict format for JSON storage
        logger.debug("Saving analysis to database...")
        action_items_dict = AnalyzerService.action_items_to_dict(result.action_items)

        # Create analysis record
        analysis = Analysis(
            recording_id=recording.id,
            summary=result.summary,
            action_items=action_items_dict,
            decisions=result.decisions,
            key_topics=result.key_topics,
            model_used=self.analyzer_service.model
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        logger.info(f"Analysis created for recording {recording.id}")

        return analysis

    def _update_status(self, status: PipelineStatus) -> None:
        """Update current status and notify callback."""
        self._current_status = status
        if self._callback:
            try:
                self._callback(status)
            except Exception as e:
                logger.warning(f"Status callback error: {e}")

    def get_current_status(self) -> Optional[PipelineStatus]:
        """Get the current pipeline status."""
        return self._current_status


# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def process_recording_sync(
    db: Session,
    recording_id: int,
    callback: Optional[StatusCallback] = None
) -> PipelineResult:
    """
    Convenience function to process a recording synchronously.

    Args:
        db: Database session
        recording_id: ID of recording to process
        callback: Optional status callback

    Returns:
        PipelineResult from processing
    """
    pipeline = ProcessingPipeline(db)
    return pipeline.process(recording_id, callback)
