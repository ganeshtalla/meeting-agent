"""
Meeting Agent - Transcription Service
======================================

This module provides speech-to-text transcription with optional speaker diarization.

Supported Providers:
    - Whisper (local): Free, private, no speaker diarization
    - AssemblyAI (cloud): Paid, excellent speaker diarization

Packages Used:
    - whisper: OpenAI's Whisper speech recognition model
    - assemblyai: AssemblyAI API client (for diarization)
    - pathlib: Object-oriented filesystem paths
    - logging: Standard logging for error tracking
    - dataclasses: Data classes for structured results

Key Components:
    - TranscriptionService: Main service class for transcription
    - TranscriptSegment: A single segment with timing and speaker
    - TranscriptResult: Complete transcription result

Usage:
    from app.services.transcription import TranscriptionService

    # Use local Whisper (no diarization)
    service = TranscriptionService(provider="whisper")
    result = service.transcribe(Path("meeting.wav"))

    # Use AssemblyAI (with diarization)
    service = TranscriptionService(provider="assemblyai")
    result = service.transcribe(Path("meeting.wav"))

    for segment in result.segments:
        print(f"[{segment.speaker}] {segment.text}")
"""

import logging
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

import numpy as np
import whisper
from pydub import AudioSegment

from app.config import settings

# Configure logging for this module
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Result Data Classes
# -----------------------------------------------------------------------------

@dataclass
class TranscriptSegment:
    """
    A single segment of transcribed text with timing and speaker information.

    Attributes:
        start (float): Start time in seconds
        end (float): End time in seconds
        text (str): Transcribed text
        speaker (str): Speaker identifier (e.g., "SPEAKER_00", "Speaker 1")
    """
    start: float
    end: float
    text: str
    speaker: Optional[str] = None


@dataclass
class TranscriptResult:
    """
    Complete result of a transcription operation.

    Attributes:
        success (bool): Whether transcription completed successfully
        segments (List[TranscriptSegment]): List of transcript segments
        full_text (str): Complete transcript as a single string
        language (str): Detected language code
        duration_seconds (float): Total audio duration
        has_speakers (bool): Whether speaker diarization was performed
        speaker_count (int): Number of unique speakers detected
        provider (str): Which provider was used
        error_message (str): Error description if failed
    """
    success: bool
    segments: List[TranscriptSegment] = field(default_factory=list)
    full_text: str = ""
    language: str = "en"
    duration_seconds: float = 0.0
    has_speakers: bool = False
    speaker_count: int = 0
    provider: str = "whisper"
    error_message: Optional[str] = None


# -----------------------------------------------------------------------------
# Transcription Service Class
# -----------------------------------------------------------------------------

class TranscriptionService:
    """
    Service for transcribing audio files with optional speaker diarization.

    Providers:
        - whisper: Local, free, no speaker diarization
        - assemblyai: Cloud API, paid, excellent speaker diarization

    Example:
        # Local transcription (no speakers)
        service = TranscriptionService(provider="whisper")
        result = service.transcribe(Path("meeting.wav"))

        # Cloud transcription (with speakers)
        service = TranscriptionService(provider="assemblyai")
        result = service.transcribe(Path("meeting.wav"))

        if result.has_speakers:
            for seg in result.segments:
                print(f"[{seg.speaker}] {seg.text}")
    """

    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    AVAILABLE_PROVIDERS = ["whisper", "whisper-diarize", "assemblyai"]

    def __init__(
        self,
        provider: Optional[str] = None,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the transcription service.

        Args:
            provider: "whisper" (local) or "assemblyai" (cloud with diarization)
            model_size: Whisper model size (for whisper provider)
            device: Device for whisper ('cuda', 'cpu')
            api_key: AssemblyAI API key (for assemblyai provider)
        """
        self.provider = (provider or getattr(settings, 'transcription_provider', 'whisper')).lower()
        self.model_size = model_size or settings.whisper_model
        self._device = device
        self._api_key = api_key or getattr(settings, 'assemblyai_api_key', '') or os.getenv('ASSEMBLYAI_API_KEY', '')

        # Validate
        if self.provider not in self.AVAILABLE_PROVIDERS:
            raise ValueError(f"Invalid provider: {self.provider}. Use: {self.AVAILABLE_PROVIDERS}")

        if self.provider in ("whisper", "whisper-diarize") and self.model_size not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model size: {self.model_size}. Use: {self.AVAILABLE_MODELS}")

        # Whisper model (lazy loaded)
        self._model: Optional[whisper.Whisper] = None

        logger.info(f"TranscriptionService initialized with provider: {self.provider}")

    # -------------------------------------------------------------------------
    # Whisper Model (Lazy Loading)
    # -------------------------------------------------------------------------

    @property
    def model(self) -> whisper.Whisper:
        """Get the loaded Whisper model (lazy loading)."""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self._model = whisper.load_model(self.model_size, device=self._device)
            logger.info(f"Whisper model loaded successfully on {self._model.device}")
        return self._model

    def is_model_loaded(self) -> bool:
        """Check if the Whisper model is loaded."""
        return self._model is not None

    def unload_model(self) -> None:
        """Unload the Whisper model to free memory."""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("Whisper model unloaded")

    # -------------------------------------------------------------------------
    # Main Transcription Method
    # -------------------------------------------------------------------------

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        speaker_labels: bool = True
    ) -> TranscriptResult:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to the audio file
            language: Language code (auto-detected if None)
            speaker_labels: Enable speaker diarization (AssemblyAI only)

        Returns:
            TranscriptResult: Transcription with segments and optional speakers
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if self.provider == "whisper":
            return self._transcribe_whisper(audio_path, language)
        elif self.provider == "whisper-diarize":
            return self._transcribe_whisper_diarize(audio_path, language)
        elif self.provider == "assemblyai":
            return self._transcribe_assemblyai(audio_path, language, speaker_labels)
        else:
            return TranscriptResult(
                success=False,
                error_message=f"Unknown provider: {self.provider}"
            )

    # -------------------------------------------------------------------------
    # Whisper Transcription (Local)
    # -------------------------------------------------------------------------

    def _transcribe_whisper(
        self,
        audio_path: Path,
        language: Optional[str] = None
    ) -> TranscriptResult:
        """Transcribe using local Whisper model (no speaker diarization)."""
        try:
            logger.info(f"Starting Whisper transcription of: {audio_path}")

            options = {"task": "transcribe", "verbose": False}
            if language:
                options["language"] = language

            result = self.model.transcribe(str(audio_path), **options)

            segments = []
            for seg in result.get("segments", []):
                segment = TranscriptSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip(),
                    speaker=None  # Whisper doesn't do diarization
                )
                segments.append(segment)

            duration = segments[-1].end if segments else 0.0
            detected_language = result.get("language", language or "en")

            logger.info(f"Whisper transcription complete: {len(segments)} segments")

            return TranscriptResult(
                success=True,
                segments=segments,
                full_text=result.get("text", "").strip(),
                language=detected_language,
                duration_seconds=duration,
                has_speakers=False,
                speaker_count=0,
                provider="whisper"
            )

        except Exception as e:
            error_msg = f"Whisper transcription failed: {str(e)}"
            logger.error(error_msg)
            return TranscriptResult(success=False, error_message=error_msg, provider="whisper")

    # -------------------------------------------------------------------------
    # Whisper + Diarization (Local with Speaker Labels)
    # -------------------------------------------------------------------------

    def _transcribe_whisper_diarize(
        self,
        audio_path: Path,
        language: Optional[str] = None
    ) -> TranscriptResult:
        """Transcribe using Whisper with local speaker diarization."""
        try:
            from resemblyzer import VoiceEncoder, preprocess_wav
            from spectralcluster import SpectralClusterer
        except ImportError:
            return TranscriptResult(
                success=False,
                error_message="Diarization packages not installed. Run: pip install resemblyzer spectralcluster",
                provider="whisper-diarize"
            )

        try:
            logger.info(f"Starting Whisper+Diarization transcription of: {audio_path}")

            # Step 1: Transcribe with Whisper
            options = {"task": "transcribe", "verbose": False}
            if language:
                options["language"] = language

            result = self.model.transcribe(str(audio_path), **options)
            whisper_segments = result.get("segments", [])

            if not whisper_segments:
                return TranscriptResult(
                    success=True,
                    segments=[],
                    full_text="",
                    language=result.get("language", language or "en"),
                    duration_seconds=0.0,
                    has_speakers=False,
                    speaker_count=0,
                    provider="whisper-diarize"
                )

            # Step 2: Load audio for speaker embedding
            logger.info("Loading audio for speaker diarization...")
            wav = preprocess_wav(audio_path)

            # Step 3: Initialize voice encoder
            encoder = VoiceEncoder()

            # Step 4: Extract embeddings for each segment
            logger.info(f"Extracting speaker embeddings for {len(whisper_segments)} segments...")
            embeddings = []
            valid_segment_indices = []

            # Get sample rate (resemblyzer uses 16kHz)
            sample_rate = 16000

            for i, seg in enumerate(whisper_segments):
                start_sample = int(seg["start"] * sample_rate)
                end_sample = int(seg["end"] * sample_rate)

                # Ensure we have enough samples (at least 0.5 seconds)
                if end_sample - start_sample < sample_rate * 0.5:
                    # Extend to get at least 0.5 seconds
                    end_sample = min(start_sample + int(sample_rate * 0.5), len(wav))

                if start_sample < len(wav) and end_sample > start_sample:
                    segment_wav = wav[start_sample:end_sample]
                    if len(segment_wav) > 0:
                        try:
                            embedding = encoder.embed_utterance(segment_wav)
                            embeddings.append(embedding)
                            valid_segment_indices.append(i)
                        except Exception as e:
                            logger.warning(f"Could not embed segment {i}: {e}")

            # Step 5: Cluster embeddings to identify speakers
            if len(embeddings) >= 2:
                logger.info("Clustering speaker embeddings...")
                embeddings_array = np.array(embeddings)

                clusterer = SpectralClusterer(
                    min_clusters=2,
                    max_clusters=min(8, len(embeddings)),  # Reasonable max speakers
                    refinement_options=None
                )

                labels = clusterer.predict(embeddings_array)

                # Create mapping from segment index to speaker label
                segment_to_speaker = {}
                for idx, seg_idx in enumerate(valid_segment_indices):
                    segment_to_speaker[seg_idx] = f"Speaker {labels[idx] + 1}"

                unique_speakers = set(labels)
                speaker_count = len(unique_speakers)
            else:
                # Not enough segments to cluster, assign all to Speaker 1
                segment_to_speaker = {i: "Speaker 1" for i in range(len(whisper_segments))}
                speaker_count = 1

            # Step 6: Build final segments with speaker labels
            segments = []
            speakers = set()

            for i, seg in enumerate(whisper_segments):
                speaker = segment_to_speaker.get(i, "Speaker 1")
                speakers.add(speaker)

                segment = TranscriptSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip(),
                    speaker=speaker
                )
                segments.append(segment)

            # Build full text with speaker labels
            full_text_parts = []
            current_speaker = None
            current_text = []

            for seg in segments:
                if seg.speaker != current_speaker:
                    if current_text:
                        full_text_parts.append(f"{current_speaker}: {' '.join(current_text)}")
                    current_speaker = seg.speaker
                    current_text = [seg.text]
                else:
                    current_text.append(seg.text)

            if current_text:
                full_text_parts.append(f"{current_speaker}: {' '.join(current_text)}")

            duration = segments[-1].end if segments else 0.0
            detected_language = result.get("language", language or "en")

            logger.info(
                f"Whisper+Diarization complete: {len(segments)} segments, "
                f"{len(speakers)} speakers detected"
            )

            return TranscriptResult(
                success=True,
                segments=segments,
                full_text="\n".join(full_text_parts),
                language=detected_language,
                duration_seconds=duration,
                has_speakers=True,
                speaker_count=len(speakers),
                provider="whisper-diarize"
            )

        except Exception as e:
            error_msg = f"Whisper+Diarization transcription failed: {str(e)}"
            logger.error(error_msg)
            return TranscriptResult(success=False, error_message=error_msg, provider="whisper-diarize")

    # -------------------------------------------------------------------------
    # AssemblyAI Transcription (Cloud with Diarization)
    # -------------------------------------------------------------------------

    def _transcribe_assemblyai(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        speaker_labels: bool = True
    ) -> TranscriptResult:
        """Transcribe using AssemblyAI API with speaker diarization."""
        try:
            import assemblyai as aai
        except ImportError:
            return TranscriptResult(
                success=False,
                error_message="AssemblyAI package not installed. Run: pip install assemblyai",
                provider="assemblyai"
            )

        if not self._api_key:
            return TranscriptResult(
                success=False,
                error_message="AssemblyAI API key not configured. Set ASSEMBLYAI_API_KEY environment variable.",
                provider="assemblyai"
            )

        try:
            logger.info(f"Starting AssemblyAI transcription of: {audio_path}")

            # Configure AssemblyAI
            aai.settings.api_key = self._api_key

            # Configure transcription
            config = aai.TranscriptionConfig(
                speaker_labels=speaker_labels,
                language_code=language or "en"
            )

            # Create transcriber and transcribe
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(str(audio_path), config=config)

            if transcript.status == aai.TranscriptStatus.error:
                return TranscriptResult(
                    success=False,
                    error_message=f"AssemblyAI error: {transcript.error}",
                    provider="assemblyai"
                )

            # Extract segments with speaker labels
            segments = []
            speakers = set()

            if transcript.utterances:
                # Use utterances (speaker-labeled segments)
                for utterance in transcript.utterances:
                    speaker = f"Speaker {utterance.speaker}" if utterance.speaker else None
                    if speaker:
                        speakers.add(speaker)

                    segment = TranscriptSegment(
                        start=utterance.start / 1000.0,  # Convert ms to seconds
                        end=utterance.end / 1000.0,
                        text=utterance.text.strip(),
                        speaker=speaker
                    )
                    segments.append(segment)
            elif transcript.words:
                # Fallback to words if no utterances
                current_segment = None
                for word in transcript.words:
                    speaker = f"Speaker {word.speaker}" if hasattr(word, 'speaker') and word.speaker else None
                    if speaker:
                        speakers.add(speaker)

                    if current_segment is None or current_segment.speaker != speaker:
                        if current_segment:
                            segments.append(current_segment)
                        current_segment = TranscriptSegment(
                            start=word.start / 1000.0,
                            end=word.end / 1000.0,
                            text=word.text,
                            speaker=speaker
                        )
                    else:
                        current_segment.end = word.end / 1000.0
                        current_segment.text += " " + word.text

                if current_segment:
                    segments.append(current_segment)

            # Build full text with speaker labels
            full_text_parts = []
            for seg in segments:
                if seg.speaker:
                    full_text_parts.append(f"{seg.speaker}: {seg.text}")
                else:
                    full_text_parts.append(seg.text)

            duration = segments[-1].end if segments else 0.0

            logger.info(
                f"AssemblyAI transcription complete: {len(segments)} segments, "
                f"{len(speakers)} speakers"
            )

            return TranscriptResult(
                success=True,
                segments=segments,
                full_text="\n".join(full_text_parts),
                language=language or "en",
                duration_seconds=duration,
                has_speakers=len(speakers) > 0,
                speaker_count=len(speakers),
                provider="assemblyai"
            )

        except Exception as e:
            error_msg = f"AssemblyAI transcription failed: {str(e)}"
            logger.error(error_msg)
            return TranscriptResult(success=False, error_message=error_msg, provider="assemblyai")

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def transcribe_with_timestamps(self, audio_path: Path) -> Optional[str]:
        """
        Transcribe audio and return text with inline timestamps and speakers.

        Returns:
            str: Formatted transcript, or None on failure

        Example Output:
            [00:00:00] SPEAKER_00: Hello everyone, let's start.
            [00:00:03] SPEAKER_01: Thanks for setting this up.
        """
        result = self.transcribe(audio_path)
        if not result.success:
            return None

        lines = []
        for segment in result.segments:
            hours = int(segment.start // 3600)
            minutes = int((segment.start % 3600) // 60)
            seconds = int(segment.start % 60)
            timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"

            if segment.speaker:
                lines.append(f"{timestamp} {segment.speaker}: {segment.text}")
            else:
                lines.append(f"{timestamp} {segment.text}")

        return "\n".join(lines)

    @staticmethod
    def segments_to_dict(segments: List[TranscriptSegment]) -> List[dict]:
        """Convert transcript segments to dictionary format."""
        return [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "speaker": seg.speaker
            }
            for seg in segments
        ]

    @staticmethod
    def format_transcript_with_speakers(segments: List[TranscriptSegment]) -> str:
        """
        Format segments into a readable transcript with speaker labels.

        Example:
            Speaker 1: Hello everyone.
            Speaker 2: Thanks for joining.
            Speaker 1: Let's discuss the agenda.
        """
        lines = []
        current_speaker = None

        for seg in segments:
            if seg.speaker and seg.speaker != current_speaker:
                current_speaker = seg.speaker
                lines.append(f"\n{current_speaker}: {seg.text}")
            elif seg.speaker:
                lines.append(seg.text)
            else:
                lines.append(seg.text)

        return " ".join(lines).strip()
