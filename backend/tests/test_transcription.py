"""
Meeting Agent - Transcription Service Tests
============================================

Tests for the TranscriptionService class which handles speech-to-text
transcription using OpenAI's Whisper model.

Packages Used:
    - pytest: Test framework
        - fixture: Define reusable test fixtures
        - mark.skipif: Conditionally skip tests
        - mark.slow: Mark slow tests (require model loading)
    - pydub: Audio manipulation for creating test fixtures

Test Categories:
    1. Service Initialization: Model loading and configuration
    2. Transcription: Basic transcription functionality
    3. Result Structure: Verify result format and fields
    4. Error Handling: Edge cases and error conditions
    5. Utility Methods: Helper function tests

Running These Tests:
    # Run all tests (including slow ones)
    pytest tests/test_transcription.py -v

    # Skip slow tests that require model loading
    pytest tests/test_transcription.py -v -m "not slow"

Note:
    - Some tests require the Whisper model to be downloaded
    - First run will download the model (~150MB for 'base')
    - Tests marked 'slow' involve actual transcription and take time
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pydub import AudioSegment
from pydub.generators import Sine

from app.services.transcription import (
    TranscriptionService,
    TranscriptResult,
    TranscriptSegment,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def transcription_service():
    """
    Create a TranscriptionService instance.

    Uses the 'tiny' model for faster tests.
    Model is not loaded until actually used.
    """
    return TranscriptionService(model_size="tiny")


@pytest.fixture
def sample_audio_path(tmp_path) -> Path:
    """
    Create a sample audio file for transcription testing.

    Creates a 16kHz mono WAV file (Whisper-compatible format).
    Note: This generates a tone, not actual speech, so transcription
    will not produce meaningful text.

    Returns:
        Path: Path to the generated audio file
    """
    # Generate a 3-second sine wave
    tone = Sine(440).to_audio_segment(duration=3000)

    # Convert to 16kHz mono (Whisper format)
    tone = tone.set_frame_rate(16000).set_channels(1)

    audio_path = tmp_path / "test_audio.wav"
    tone.export(str(audio_path), format="wav")

    return audio_path


@pytest.fixture
def mock_whisper_result():
    """
    Mock Whisper transcription result.

    Returns a properly structured result without running actual transcription.
    """
    return {
        "text": " Hello everyone. Welcome to the meeting.",
        "segments": [
            {
                "start": 0.0,
                "end": 1.5,
                "text": " Hello everyone."
            },
            {
                "start": 1.5,
                "end": 3.0,
                "text": " Welcome to the meeting."
            }
        ],
        "language": "en"
    }


# -----------------------------------------------------------------------------
# Service Initialization Tests
# -----------------------------------------------------------------------------

class TestServiceInitialization:
    """Tests for TranscriptionService initialization."""

    def test_service_accepts_model_size(self):
        """Should accept valid model sizes."""
        for size in ["tiny", "base", "small", "medium", "large"]:
            service = TranscriptionService(model_size=size)
            assert service.model_size == size

    def test_service_rejects_invalid_model(self):
        """Should raise ValueError for invalid model size."""
        with pytest.raises(ValueError) as exc_info:
            TranscriptionService(model_size="invalid")

        assert "invalid model size" in str(exc_info.value).lower()

    def test_model_not_loaded_on_init(self, transcription_service):
        """Model should not be loaded until first use."""
        assert transcription_service._model is None
        assert not transcription_service.is_model_loaded()

    def test_default_model_from_settings(self):
        """Should use model size from settings if not specified."""
        service = TranscriptionService()
        # Default is 'base' from settings
        assert service.model_size in ["tiny", "base", "small", "medium", "large"]


# -----------------------------------------------------------------------------
# Result Structure Tests
# -----------------------------------------------------------------------------

class TestResultStructure:
    """Tests for transcription result structure."""

    def test_transcript_segment_has_required_fields(self):
        """TranscriptSegment should have start, end, text."""
        segment = TranscriptSegment(
            start=0.0,
            end=1.5,
            text="Hello world"
        )

        assert segment.start == 0.0
        assert segment.end == 1.5
        assert segment.text == "Hello world"
        assert segment.speaker is None  # Optional field

    def test_transcript_segment_optional_speaker(self):
        """TranscriptSegment should support optional speaker."""
        segment = TranscriptSegment(
            start=0.0,
            end=1.5,
            text="Hello",
            speaker="Speaker 1"
        )

        assert segment.speaker == "Speaker 1"

    def test_transcript_result_success_structure(self):
        """Successful TranscriptResult should have all fields."""
        segments = [
            TranscriptSegment(start=0.0, end=1.0, text="Hello")
        ]
        result = TranscriptResult(
            success=True,
            segments=segments,
            full_text="Hello",
            language="en",
            duration_seconds=1.0
        )

        assert result.success is True
        assert len(result.segments) == 1
        assert result.full_text == "Hello"
        assert result.language == "en"
        assert result.duration_seconds == 1.0
        assert result.error_message is None

    def test_transcript_result_failure_structure(self):
        """Failed TranscriptResult should have error message."""
        result = TranscriptResult(
            success=False,
            error_message="Test error"
        )

        assert result.success is False
        assert result.error_message == "Test error"
        assert result.segments == []
        assert result.full_text == ""


# -----------------------------------------------------------------------------
# Transcription Tests (with mocking)
# -----------------------------------------------------------------------------

class TestTranscriptionMocked:
    """Tests using mocked Whisper to avoid slow model loading."""

    def test_transcribe_returns_result(self, transcription_service, sample_audio_path, mock_whisper_result):
        """transcribe should return a TranscriptResult."""
        # Mock the model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = mock_whisper_result
        mock_model.device = "cpu"

        with patch.object(transcription_service, '_model', mock_model):
            transcription_service._model = mock_model  # Set directly

            result = transcription_service.transcribe(sample_audio_path)

            assert isinstance(result, TranscriptResult)

    def test_transcribe_extracts_segments(self, transcription_service, sample_audio_path, mock_whisper_result):
        """Should extract segments from Whisper result."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = mock_whisper_result
        mock_model.device = "cpu"

        with patch.object(transcription_service, '_model', mock_model):
            transcription_service._model = mock_model

            result = transcription_service.transcribe(sample_audio_path)

            assert result.success
            assert len(result.segments) == 2
            assert result.segments[0].text == "Hello everyone."
            assert result.segments[1].text == "Welcome to the meeting."

    def test_transcribe_extracts_full_text(self, transcription_service, sample_audio_path, mock_whisper_result):
        """Should extract full text from Whisper result."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = mock_whisper_result
        mock_model.device = "cpu"

        with patch.object(transcription_service, '_model', mock_model):
            transcription_service._model = mock_model

            result = transcription_service.transcribe(sample_audio_path)

            assert "Hello everyone" in result.full_text
            assert "Welcome to the meeting" in result.full_text

    def test_transcribe_extracts_language(self, transcription_service, sample_audio_path, mock_whisper_result):
        """Should extract detected language."""
        mock_model = MagicMock()
        mock_whisper_result["language"] = "es"
        mock_model.transcribe.return_value = mock_whisper_result
        mock_model.device = "cpu"

        with patch.object(transcription_service, '_model', mock_model):
            transcription_service._model = mock_model

            result = transcription_service.transcribe(sample_audio_path)

            assert result.language == "es"

    def test_transcribe_respects_language_param(self, transcription_service, sample_audio_path, mock_whisper_result):
        """Should pass language parameter to Whisper."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = mock_whisper_result
        mock_model.device = "cpu"

        with patch.object(transcription_service, '_model', mock_model):
            transcription_service._model = mock_model

            transcription_service.transcribe(sample_audio_path, language="en")

            # Check that language was passed to transcribe
            call_kwargs = mock_model.transcribe.call_args[1]
            assert call_kwargs.get("language") == "en"


# -----------------------------------------------------------------------------
# Error Handling Tests
# -----------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for error handling in transcription."""

    def test_transcribe_handles_missing_file(self, transcription_service, tmp_path):
        """Should raise FileNotFoundError for missing file."""
        nonexistent = tmp_path / "nonexistent.wav"

        with pytest.raises(FileNotFoundError):
            transcription_service.transcribe(nonexistent)

    def test_transcribe_handles_transcription_error(self, transcription_service, sample_audio_path):
        """Should return failed result on transcription error."""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception("Transcription failed")
        mock_model.device = "cpu"

        with patch.object(transcription_service, '_model', mock_model):
            transcription_service._model = mock_model

            result = transcription_service.transcribe(sample_audio_path)

            assert result.success is False
            assert "failed" in result.error_message.lower()


# -----------------------------------------------------------------------------
# Utility Method Tests
# -----------------------------------------------------------------------------

class TestUtilityMethods:
    """Tests for utility methods."""

    def test_segments_to_dict(self):
        """Should convert segments to dictionary format."""
        segments = [
            TranscriptSegment(start=0.0, end=1.0, text="Hello", speaker="A"),
            TranscriptSegment(start=1.0, end=2.0, text="World", speaker=None)
        ]

        result = TranscriptionService.segments_to_dict(segments)

        assert len(result) == 2
        assert result[0] == {
            "start": 0.0,
            "end": 1.0,
            "text": "Hello",
            "speaker": "A"
        }
        assert result[1]["speaker"] is None

    def test_transcribe_with_timestamps_format(self, transcription_service, sample_audio_path, mock_whisper_result):
        """Should format transcript with timestamps."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = mock_whisper_result
        mock_model.device = "cpu"

        with patch.object(transcription_service, '_model', mock_model):
            transcription_service._model = mock_model

            result = transcription_service.transcribe_with_timestamps(sample_audio_path)

            # Should have timestamp prefix
            assert "[00:00:00]" in result
            # Should contain the text
            assert "Hello everyone" in result

    def test_model_unload(self, transcription_service, sample_audio_path, mock_whisper_result):
        """Should be able to unload model to free memory."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = mock_whisper_result
        mock_model.device = "cpu"

        # Load the model
        transcription_service._model = mock_model
        assert transcription_service.is_model_loaded()

        # Unload
        transcription_service.unload_model()

        assert not transcription_service.is_model_loaded()


# -----------------------------------------------------------------------------
# Integration Tests (marked slow - require actual model)
# -----------------------------------------------------------------------------

@pytest.mark.slow
class TestIntegration:
    """
    Integration tests that use the actual Whisper model.

    These tests are slow because they:
    1. Download the model on first run (~150MB for 'tiny')
    2. Actually run transcription

    Run with: pytest tests/test_transcription.py -v -m slow
    """

    @pytest.fixture
    def real_service(self):
        """Create service with real model (tiny for speed)."""
        return TranscriptionService(model_size="tiny")

    def test_actual_transcription(self, real_service, sample_audio_path):
        """
        Test actual transcription with Whisper.

        Note: The test audio is a sine wave, not speech,
        so we just verify the result structure.
        """
        result = real_service.transcribe(sample_audio_path)

        # Should return a result (may be empty for non-speech audio)
        assert isinstance(result, TranscriptResult)
        assert result.success is True
        assert isinstance(result.segments, list)
        assert result.language is not None

    def test_model_loads_on_transcribe(self, real_service, sample_audio_path):
        """Model should load lazily on first transcription."""
        assert not real_service.is_model_loaded()

        real_service.transcribe(sample_audio_path)

        assert real_service.is_model_loaded()
