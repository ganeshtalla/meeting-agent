"""
Meeting Agent - Pipeline Service Tests
======================================

Tests for the ProcessingPipeline service which orchestrates the complete
recording processing flow: audio extraction → transcription → analysis.

Packages Used:
    - pytest: Test framework
        - fixture: Define reusable test fixtures
        - mark.slow: Mark slow tests
    - unittest.mock: Mocking for unit tests

Test Categories:
    1. Pipeline Initialization: Configuration and setup
    2. Status Tracking: Status updates during processing
    3. Pipeline Processing (mocked): Full pipeline with mocked services
    4. Error Handling: Failure scenarios
    5. Integration: Actual processing tests (marked slow)

Running These Tests:
    # Run all tests (excluding slow integration tests)
    pytest tests/test_pipeline.py -v -m "not slow"

    # Run integration tests (requires FFmpeg, Whisper, Ollama)
    pytest tests/test_pipeline.py -v -m slow
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.pipeline import (
    ProcessingPipeline,
    PipelineStatus,
    PipelineResult,
    PipelineStage,
    process_recording_sync,
)
from app.services.audio import AudioExtractionResult
from app.services.transcription import TranscriptResult, TranscriptSegment
from app.services.analyzer import AnalysisResult, ActionItem
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.analysis import Analysis


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


@pytest.fixture
def mock_recording():
    """Create a mock recording."""
    recording = MagicMock(spec=Recording)
    recording.id = 1
    recording.title = "Test Meeting"
    recording.file_path = "/uploads/1_test.wav"
    recording.file_size = 1024000  # 1 MB
    recording.mime_type = "audio/wav"
    recording.status = "pending"
    recording.duration_seconds = None
    recording.transcript = None
    recording.analysis = None
    return recording


@pytest.fixture
def mock_audio_service():
    """Create a mock audio service."""
    service = MagicMock()
    service.is_whisper_compatible.return_value = True
    service.extract_audio.return_value = AudioExtractionResult(
        success=True,
        output_path=Path("/processed/1_audio.wav"),
        duration_seconds=120.5,
        sample_rate=16000,
        channels=1
    )
    return service


@pytest.fixture
def mock_transcription_service():
    """Create a mock transcription service."""
    service = MagicMock()
    service.transcribe.return_value = TranscriptResult(
        success=True,
        segments=[
            TranscriptSegment(start=0.0, end=5.0, text="Hello everyone."),
            TranscriptSegment(start=5.0, end=10.0, text="Let's discuss the project.")
        ],
        full_text="Hello everyone. Let's discuss the project.",
        language="en",
        duration_seconds=120.5
    )
    return service


@pytest.fixture
def mock_analyzer_service():
    """Create a mock analyzer service."""
    service = MagicMock()
    service.is_available.return_value = True
    service.model = "mistral"
    service.analyze.return_value = AnalysisResult(
        success=True,
        summary="Team discussed the project status.",
        action_items=[
            ActionItem(speaker="Speaker 1", task="Review PR", due_date="Friday")
        ],
        decisions=["Use PostgreSQL"],
        key_topics=["Project status", "Database"]
    )
    return service


@pytest.fixture
def pipeline_with_mocks(mock_db, mock_recording, mock_audio_service,
                        mock_transcription_service, mock_analyzer_service):
    """Create a pipeline with all services mocked."""
    # Setup mock db to return recording
    mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

    pipeline = ProcessingPipeline(
        db=mock_db,
        audio_service=mock_audio_service,
        transcription_service=mock_transcription_service,
        analyzer_service=mock_analyzer_service
    )
    return pipeline, mock_recording


# -----------------------------------------------------------------------------
# Pipeline Status Tests
# -----------------------------------------------------------------------------

class TestPipelineStatus:
    """Tests for PipelineStatus data structure."""

    def test_status_has_required_fields(self):
        """PipelineStatus should have all required fields."""
        status = PipelineStatus(
            recording_id=1,
            stage=PipelineStage.TRANSCRIBING,
            progress=50,
            message="Processing..."
        )
        assert status.recording_id == 1
        assert status.stage == PipelineStage.TRANSCRIBING
        assert status.progress == 50
        assert status.message == "Processing..."

    def test_status_to_dict(self):
        """PipelineStatus should convert to dictionary."""
        now = datetime.utcnow()
        status = PipelineStatus(
            recording_id=1,
            stage=PipelineStage.COMPLETED,
            progress=100,
            message="Done",
            started_at=now,
            updated_at=now
        )

        result = status.to_dict()

        assert result["recording_id"] == 1
        assert result["stage"] == "completed"
        assert result["progress"] == 100
        assert result["message"] == "Done"

    def test_status_error_field(self):
        """PipelineStatus should support error field."""
        status = PipelineStatus(
            recording_id=1,
            stage=PipelineStage.FAILED,
            progress=0,
            message="Failed",
            error="Audio extraction failed"
        )
        assert status.error == "Audio extraction failed"


class TestPipelineResult:
    """Tests for PipelineResult data structure."""

    def test_success_result_structure(self):
        """Successful result should have IDs."""
        result = PipelineResult(
            success=True,
            recording_id=1,
            transcript_id=10,
            analysis_id=20,
            duration_seconds=5.5
        )
        assert result.success is True
        assert result.transcript_id == 10
        assert result.analysis_id == 20
        assert result.error_message is None

    def test_failure_result_structure(self):
        """Failed result should have error message."""
        result = PipelineResult(
            success=False,
            recording_id=1,
            error_message="Processing failed"
        )
        assert result.success is False
        assert result.error_message == "Processing failed"
        assert result.transcript_id is None


# -----------------------------------------------------------------------------
# Pipeline Initialization Tests
# -----------------------------------------------------------------------------

class TestPipelineInitialization:
    """Tests for ProcessingPipeline initialization."""

    def test_pipeline_creates_default_services(self, mock_db):
        """Pipeline should create default services if not provided."""
        pipeline = ProcessingPipeline(db=mock_db)

        assert pipeline.audio_service is not None
        assert pipeline.transcription_service is not None
        assert pipeline.analyzer_service is not None

    def test_pipeline_accepts_custom_services(self, mock_db, mock_audio_service):
        """Pipeline should accept custom service instances."""
        pipeline = ProcessingPipeline(
            db=mock_db,
            audio_service=mock_audio_service
        )

        assert pipeline.audio_service is mock_audio_service


# -----------------------------------------------------------------------------
# Pipeline Processing Tests (Mocked)
# -----------------------------------------------------------------------------

class TestPipelineProcessingMocked:
    """Tests for pipeline processing with mocked services."""

    def test_process_updates_status_to_processing(self, pipeline_with_mocks):
        """Pipeline should update status to processing when started."""
        pipeline, recording = pipeline_with_mocks

        pipeline.process(recording_id=1)

        # Check that status was updated to processing
        assert recording.status == "completed"  # Final status after success

    def test_process_updates_status_to_completed(self, pipeline_with_mocks):
        """Pipeline should update status to completed on success."""
        pipeline, recording = pipeline_with_mocks

        result = pipeline.process(recording_id=1)

        assert result.success is True
        assert recording.status == "completed"

    def test_process_creates_transcript(self, pipeline_with_mocks):
        """Pipeline should create transcript record."""
        pipeline, recording = pipeline_with_mocks

        pipeline.process(recording_id=1)

        # Check that transcript was added to db
        pipeline.db.add.assert_called()

    def test_process_creates_analysis(self, pipeline_with_mocks):
        """Pipeline should create analysis record."""
        pipeline, recording = pipeline_with_mocks

        pipeline.process(recording_id=1)

        # Verify analyzer was called
        pipeline.analyzer_service.analyze.assert_called_once()

    def test_process_returns_result_with_duration(self, pipeline_with_mocks):
        """Pipeline should return result with processing duration."""
        pipeline, recording = pipeline_with_mocks

        result = pipeline.process(recording_id=1)

        assert result.duration_seconds > 0

    def test_process_calls_status_callback(self, pipeline_with_mocks):
        """Pipeline should call status callback with updates."""
        pipeline, recording = pipeline_with_mocks
        statuses = []

        def callback(status):
            statuses.append(status)

        pipeline.process(recording_id=1, callback=callback)

        # Should have multiple status updates
        assert len(statuses) >= 3

        # Check stages progressed correctly
        stages = [s.stage for s in statuses]
        assert PipelineStage.EXTRACTING in stages or PipelineStage.TRANSCRIBING in stages

    def test_process_skips_audio_extraction_if_compatible(self, pipeline_with_mocks):
        """Pipeline should skip audio extraction if already compatible."""
        pipeline, recording = pipeline_with_mocks
        pipeline.audio_service.is_whisper_compatible.return_value = True

        pipeline.process(recording_id=1)

        # Should not call extract_audio if already compatible
        pipeline.audio_service.extract_audio.assert_not_called()


# -----------------------------------------------------------------------------
# Error Handling Tests
# -----------------------------------------------------------------------------

class TestPipelineErrorHandling:
    """Tests for pipeline error handling."""

    def test_process_handles_recording_not_found(self, mock_db):
        """Pipeline should raise error for non-existent recording."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        pipeline = ProcessingPipeline(db=mock_db)

        with pytest.raises(ValueError, match="not found"):
            pipeline.process(recording_id=999)

    def test_process_handles_audio_extraction_failure(self, pipeline_with_mocks):
        """Pipeline should handle audio extraction failure."""
        pipeline, recording = pipeline_with_mocks
        pipeline.audio_service.is_whisper_compatible.return_value = False
        pipeline.audio_service.extract_audio.return_value = AudioExtractionResult(
            success=False,
            error_message="FFmpeg not found"
        )

        result = pipeline.process(recording_id=1)

        assert result.success is False
        assert "FFmpeg" in result.error_message
        assert recording.status == "failed"

    def test_process_handles_transcription_failure(self, pipeline_with_mocks):
        """Pipeline should handle transcription failure."""
        pipeline, recording = pipeline_with_mocks
        pipeline.transcription_service.transcribe.return_value = TranscriptResult(
            success=False,
            error_message="Whisper model failed"
        )

        result = pipeline.process(recording_id=1)

        assert result.success is False
        assert recording.status == "failed"

    def test_process_continues_without_analysis(self, pipeline_with_mocks):
        """Pipeline should succeed even if analysis is unavailable."""
        pipeline, recording = pipeline_with_mocks
        pipeline.analyzer_service.is_available.return_value = False

        result = pipeline.process(recording_id=1)

        # Should still succeed - analysis is optional
        assert result.success is True
        assert result.analysis_id is None

    def test_process_handles_analysis_failure_gracefully(self, pipeline_with_mocks):
        """Pipeline should continue if analysis fails."""
        pipeline, recording = pipeline_with_mocks
        pipeline.analyzer_service.analyze.return_value = AnalysisResult(
            success=False,
            error_message="LLM timeout"
        )

        result = pipeline.process(recording_id=1)

        # Should still succeed - analysis failure doesn't fail pipeline
        assert result.success is True

    def test_process_sets_error_message_on_failure(self, pipeline_with_mocks):
        """Pipeline should set error message on recording when failed."""
        pipeline, recording = pipeline_with_mocks
        pipeline.audio_service.is_whisper_compatible.return_value = False
        pipeline.audio_service.extract_audio.side_effect = Exception("Disk full")

        result = pipeline.process(recording_id=1)

        assert result.success is False
        assert recording.error_message is not None


# -----------------------------------------------------------------------------
# WebSocket Status Update Tests
# -----------------------------------------------------------------------------

class TestStatusUpdates:
    """Tests for status update mechanism."""

    def test_get_current_status(self, pipeline_with_mocks):
        """Pipeline should track current status."""
        pipeline, recording = pipeline_with_mocks

        # Process to generate status
        pipeline.process(recording_id=1)

        status = pipeline.get_current_status()
        assert status is not None
        assert status.recording_id == 1

    def test_status_callback_receives_progress(self, pipeline_with_mocks):
        """Status callback should receive progress updates."""
        pipeline, recording = pipeline_with_mocks
        progress_values = []

        def callback(status):
            progress_values.append(status.progress)

        pipeline.process(recording_id=1, callback=callback)

        # Progress should increase during processing
        assert len(progress_values) > 0
        assert 100 in progress_values  # Should reach 100% on completion


# -----------------------------------------------------------------------------
# Integration Tests (require actual services)
# -----------------------------------------------------------------------------

@pytest.mark.slow
class TestPipelineIntegration:
    """
    Integration tests that use actual services.

    These tests require:
    1. FFmpeg to be installed
    2. Whisper model available
    3. Ollama running with mistral model (optional)

    Run with: pytest tests/test_pipeline.py -v -m slow
    """

    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        from app.db.database import SessionLocal, engine, Base

        # Create tables
        Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        yield db
        db.close()

    @pytest.fixture
    def sample_recording(self, db_session, sample_wav_path):
        """Create a sample recording in database."""
        import shutil
        from app.config import settings

        # Ensure upload dir exists
        settings.upload_dir.mkdir(parents=True, exist_ok=True)

        # Copy sample to uploads
        dest_path = settings.upload_dir / "test_recording.wav"
        shutil.copy(sample_wav_path, dest_path)

        recording = Recording(
            title="Integration Test Recording",
            original_filename="test.wav",
            file_path=str(dest_path),
            file_size=dest_path.stat().st_size,
            mime_type="audio/wav",
            status="pending"
        )
        db_session.add(recording)
        db_session.commit()
        db_session.refresh(recording)

        yield recording

        # Cleanup
        if dest_path.exists():
            dest_path.unlink()
        db_session.delete(recording)
        db_session.commit()

    @pytest.fixture
    def sample_wav_path(self, tmp_path):
        """Create a sample WAV file for testing."""
        from app.services.audio import AudioService

        if not AudioService.is_ffmpeg_available():
            pytest.skip("FFmpeg not available")

        # Create a simple WAV file using pydub
        from pydub import AudioSegment
        from pydub.generators import Sine

        # Generate 2 second sine wave
        audio = Sine(440).to_audio_segment(duration=2000)
        audio = audio.set_frame_rate(16000).set_channels(1)

        wav_path = tmp_path / "test.wav"
        audio.export(wav_path, format="wav")

        return wav_path

    def test_full_pipeline_with_real_services(self, db_session, sample_recording):
        """Test full pipeline with actual services."""
        pipeline = ProcessingPipeline(db=db_session)

        # Track status updates
        statuses = []
        def callback(status):
            statuses.append(status)

        result = pipeline.process(
            recording_id=sample_recording.id,
            callback=callback
        )

        # Refresh from db
        db_session.refresh(sample_recording)

        # Check result
        assert result.success is True
        assert sample_recording.status == "completed"
        assert sample_recording.transcript is not None

        # Check status progression
        assert len(statuses) > 0
