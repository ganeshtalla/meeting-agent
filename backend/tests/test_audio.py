"""
Meeting Agent - Audio Service Tests
====================================

Tests for the AudioService class which handles audio extraction from
video files and audio format conversion using FFmpeg.

Packages Used:
    - pytest: Test framework
        - fixture: Define reusable test fixtures
        - mark.skipif: Conditionally skip tests
        - raises: Test for expected exceptions
    - pydub: Audio manipulation for creating test fixtures
        - AudioSegment: Create test audio data
        - generators: Generate test tones

Test Categories:
    1. FFmpeg Availability: Check FFmpeg installation
    2. Audio Extraction: Extract audio from video/audio files
    3. Audio Info: Get metadata about audio files
    4. Whisper Compatibility: Check if audio is ready for transcription

Running These Tests:
    pytest tests/test_audio.py -v

Note:
    Some tests require FFmpeg to be installed. Tests will be skipped
    if FFmpeg is not available.
"""

import pytest
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine

from app.services.audio import AudioService, AudioExtractionResult, AudioInfo


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def audio_service(tmp_path):
    """
    Create an AudioService instance with a temporary output directory.

    The tmp_path fixture provides a temporary directory unique to each test.
    """
    return AudioService(output_dir=tmp_path)


@pytest.fixture
def sample_audio_path(tmp_path) -> Path:
    """
    Create a sample audio file for testing.

    Generates a 3-second WAV file with a 440Hz sine wave (A4 note).

    Returns:
        Path: Path to the generated audio file
    """
    # Generate a 3-second sine wave at 440Hz
    tone = Sine(440).to_audio_segment(duration=3000)  # 3000ms = 3 seconds

    # Save as WAV
    audio_path = tmp_path / "test_audio.wav"
    tone.export(str(audio_path), format="wav")

    return audio_path


@pytest.fixture
def sample_stereo_audio_path(tmp_path) -> Path:
    """
    Create a stereo audio file (non-Whisper compatible) for testing.

    Returns:
        Path: Path to stereo audio file at 44.1kHz
    """
    # Generate stereo audio at 44.1kHz
    tone = Sine(440).to_audio_segment(duration=2000)
    stereo = AudioSegment.from_mono_audiosegments(tone, tone)
    stereo = stereo.set_frame_rate(44100)

    audio_path = tmp_path / "stereo_audio.wav"
    stereo.export(str(audio_path), format="wav")

    return audio_path


@pytest.fixture
def sample_mp3_path(tmp_path) -> Path:
    """
    Create a sample MP3 file for testing.

    Note: Requires FFmpeg to be installed for MP3 encoding.

    Returns:
        Path: Path to the generated MP3 file
    """
    if not AudioService.is_ffmpeg_available():
        pytest.skip("FFmpeg not installed - cannot create MP3 test file")

    tone = Sine(440).to_audio_segment(duration=2000)
    audio_path = tmp_path / "test_audio.mp3"
    tone.export(str(audio_path), format="mp3")

    return audio_path


@pytest.fixture
def silent_audio_path(tmp_path) -> Path:
    """
    Create a silent audio file for edge case testing.

    Returns:
        Path: Path to silent audio file
    """
    # Create 1 second of silence
    silence = AudioSegment.silent(duration=1000)
    audio_path = tmp_path / "silent.wav"
    silence.export(str(audio_path), format="wav")

    return audio_path


# -----------------------------------------------------------------------------
# FFmpeg Availability Tests
# -----------------------------------------------------------------------------

class TestFFmpegAvailability:
    """Tests for FFmpeg installation detection."""

    def test_ffmpeg_check_returns_bool(self):
        """is_ffmpeg_available should return a boolean."""
        result = AudioService.is_ffmpeg_available()
        assert isinstance(result, bool)

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_ffmpeg_is_available(self):
        """FFmpeg should be available for audio processing."""
        assert AudioService.is_ffmpeg_available() is True


# -----------------------------------------------------------------------------
# Audio Extraction Tests
# -----------------------------------------------------------------------------

class TestAudioExtraction:
    """Tests for audio extraction functionality."""

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_extract_audio_returns_result(self, audio_service, sample_audio_path, tmp_path):
        """extract_audio should return an AudioExtractionResult."""
        output_path = tmp_path / "output.wav"
        result = audio_service.extract_audio(sample_audio_path, output_path)

        assert isinstance(result, AudioExtractionResult)

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_extract_audio_creates_output_file(self, audio_service, sample_audio_path, tmp_path):
        """Extraction should create the output file."""
        output_path = tmp_path / "output.wav"
        result = audio_service.extract_audio(sample_audio_path, output_path)

        assert result.success
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_extract_audio_converts_to_16khz_mono(self, audio_service, sample_stereo_audio_path, tmp_path):
        """Extracted audio should be 16kHz mono for Whisper."""
        output_path = tmp_path / "output.wav"
        result = audio_service.extract_audio(sample_stereo_audio_path, output_path)

        assert result.success
        assert result.sample_rate == 16000
        assert result.channels == 1

        # Verify the actual file format
        audio = AudioSegment.from_wav(str(output_path))
        assert audio.frame_rate == 16000
        assert audio.channels == 1

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_extract_audio_reports_duration(self, audio_service, sample_audio_path, tmp_path):
        """Extraction result should include audio duration."""
        output_path = tmp_path / "output.wav"
        result = audio_service.extract_audio(sample_audio_path, output_path)

        assert result.success
        assert result.duration_seconds > 0
        # Original audio is 3 seconds
        assert 2.5 < result.duration_seconds < 3.5

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_extract_audio_from_mp3(self, audio_service, sample_mp3_path, tmp_path):
        """Should convert MP3 to WAV."""
        output_path = tmp_path / "output.wav"
        result = audio_service.extract_audio(sample_mp3_path, output_path)

        assert result.success
        assert output_path.exists()
        assert output_path.suffix == ".wav"

    def test_extract_audio_handles_missing_file(self, audio_service, tmp_path):
        """Should raise FileNotFoundError for non-existent file."""
        nonexistent = tmp_path / "nonexistent.mp4"
        output_path = tmp_path / "output.wav"

        with pytest.raises(FileNotFoundError):
            audio_service.extract_audio(nonexistent, output_path)

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_extract_audio_auto_generates_output_path(self, tmp_path, sample_audio_path):
        """Should auto-generate output path if not provided."""
        # Use a different output directory to avoid same-path collision
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        audio_service = AudioService(output_dir=output_dir)

        result = audio_service.extract_audio(sample_audio_path)

        assert result.success
        assert result.output_path is not None
        assert result.output_path.exists()
        assert result.output_path.stem == sample_audio_path.stem

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_extract_audio_overwrites_existing(self, audio_service, sample_audio_path, tmp_path):
        """Should overwrite existing output file."""
        output_path = tmp_path / "output.wav"

        # Create existing file
        output_path.write_text("existing content")
        assert output_path.stat().st_size < 100

        # Extract should overwrite
        result = audio_service.extract_audio(sample_audio_path, output_path)

        assert result.success
        assert output_path.stat().st_size > 100  # Should be much larger now


# -----------------------------------------------------------------------------
# Audio Info Tests
# -----------------------------------------------------------------------------

class TestAudioInfo:
    """Tests for audio file information retrieval."""

    def test_get_audio_info_returns_info(self, audio_service, sample_audio_path):
        """get_audio_info should return AudioInfo object."""
        info = audio_service.get_audio_info(sample_audio_path)

        assert isinstance(info, AudioInfo)

    def test_get_audio_info_has_duration(self, audio_service, sample_audio_path):
        """AudioInfo should include duration."""
        info = audio_service.get_audio_info(sample_audio_path)

        assert info.duration_seconds > 0
        # Sample audio is 3 seconds
        assert 2.5 < info.duration_seconds < 3.5

    def test_get_audio_info_has_sample_rate(self, audio_service, sample_audio_path):
        """AudioInfo should include sample rate."""
        info = audio_service.get_audio_info(sample_audio_path)

        assert info.sample_rate > 0
        # pydub defaults to 44100 for generated audio
        assert info.sample_rate in [16000, 22050, 44100, 48000]

    def test_get_audio_info_has_channels(self, audio_service, sample_audio_path):
        """AudioInfo should include channel count."""
        info = audio_service.get_audio_info(sample_audio_path)

        assert info.channels in [1, 2]

    def test_get_audio_info_returns_none_for_missing(self, audio_service, tmp_path):
        """Should return None for non-existent file."""
        nonexistent = tmp_path / "nonexistent.wav"
        info = audio_service.get_audio_info(nonexistent)

        assert info is None

    def test_get_audio_info_mp3(self, audio_service, sample_mp3_path):
        """Should get info from MP3 files."""
        info = audio_service.get_audio_info(sample_mp3_path)

        assert info is not None
        assert info.format == "mp3"


# -----------------------------------------------------------------------------
# Whisper Compatibility Tests
# -----------------------------------------------------------------------------

class TestWhisperCompatibility:
    """Tests for Whisper format compatibility checking."""

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_extracted_audio_is_whisper_compatible(self, audio_service, sample_audio_path, tmp_path):
        """Extracted audio should be Whisper-compatible."""
        output_path = tmp_path / "output.wav"
        audio_service.extract_audio(sample_audio_path, output_path)

        is_compatible = audio_service.is_whisper_compatible(output_path)
        assert is_compatible is True

    def test_stereo_audio_not_whisper_compatible(self, audio_service, sample_stereo_audio_path):
        """Stereo audio should not be Whisper-compatible."""
        is_compatible = audio_service.is_whisper_compatible(sample_stereo_audio_path)
        assert is_compatible is False

    def test_mp3_not_whisper_compatible(self, audio_service, sample_mp3_path):
        """MP3 format should not be considered Whisper-compatible."""
        is_compatible = audio_service.is_whisper_compatible(sample_mp3_path)
        assert is_compatible is False


# -----------------------------------------------------------------------------
# Cleanup Tests
# -----------------------------------------------------------------------------

class TestCleanup:
    """Tests for file cleanup functionality."""

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_delete_processed_file(self, audio_service, sample_audio_path, tmp_path):
        """Should delete processed audio files."""
        output_path = tmp_path / "output.wav"
        audio_service.extract_audio(sample_audio_path, output_path)

        assert output_path.exists()

        result = audio_service.delete_processed_file(output_path)

        assert result is True
        assert not output_path.exists()

    def test_delete_nonexistent_file(self, audio_service, tmp_path):
        """Should return False for non-existent file."""
        nonexistent = tmp_path / "nonexistent.wav"

        result = audio_service.delete_processed_file(nonexistent)

        assert result is False


# -----------------------------------------------------------------------------
# Edge Cases
# -----------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.skipif(
        not AudioService.is_ffmpeg_available(),
        reason="FFmpeg not installed"
    )
    def test_extract_silent_audio(self, audio_service, silent_audio_path, tmp_path):
        """Should handle silent audio files."""
        output_path = tmp_path / "output.wav"
        result = audio_service.extract_audio(silent_audio_path, output_path)

        assert result.success
        assert output_path.exists()
        # Duration should still be captured
        assert result.duration_seconds > 0
