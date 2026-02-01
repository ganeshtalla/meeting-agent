"""
Meeting Agent - Services Package
================================

This package contains the business logic layer for the Meeting Agent.
Services encapsulate complex operations and are used by API endpoints.

Exports:
    Phase 2 (File Upload):
    - StorageService: File storage and management
    - ALLOWED_MIME_TYPES: Set of accepted MIME types
    - ALLOWED_EXTENSIONS: Set of accepted file extensions

    Phase 3 (Audio Processing & Transcription):
    - AudioService: Audio extraction from video files using FFmpeg
    - AudioExtractionResult: Result dataclass for extraction operations
    - AudioInfo: Audio file metadata
    - TranscriptionService: Whisper speech-to-text transcription
    - TranscriptResult: Complete transcription result
    - TranscriptSegment: Single segment with timing

Future Services (to be added in later phases):
    - AnalyzerService: Ollama LLM analysis (Phase 4)
    - PipelineService: Processing orchestration (Phase 5)
    - ExportService: Export to various formats (Phase 6)

Service Pattern:
    Services follow a class-based pattern for encapsulation:

    class ExampleService:
        def __init__(self, config=None):
            self.config = config or default_config

        def process(self, input_data):
            # Business logic here
            return result

Usage:
    from app.services import StorageService, AudioService, TranscriptionService

    # File storage
    storage = StorageService()
    file_path = storage.save_file(file_obj, recording_id=1, original_filename="test.wav")

    # Audio extraction
    audio = AudioService()
    result = audio.extract_audio(input_path, output_path)

    # Transcription
    transcriber = TranscriptionService(model_size="base")
    transcript = transcriber.transcribe(audio_path)
"""

from .storage import StorageService, ALLOWED_MIME_TYPES, ALLOWED_EXTENSIONS
from .audio import AudioService, AudioExtractionResult, AudioInfo
from .transcription import TranscriptionService, TranscriptResult, TranscriptSegment
from .analyzer import (
    AnalyzerService,
    AnalysisResult,
    ActionItem,
    ServiceUnavailableError,
    AnalysisTimeoutError,
)
from .pipeline import (
    ProcessingPipeline,
    PipelineStatus,
    PipelineResult,
    PipelineStage,
    process_recording_sync,
)
from .export import ExportService, ExportResult

__all__ = [
    # Storage (Phase 2)
    "StorageService",
    "ALLOWED_MIME_TYPES",
    "ALLOWED_EXTENSIONS",
    # Audio (Phase 3)
    "AudioService",
    "AudioExtractionResult",
    "AudioInfo",
    # Transcription (Phase 3)
    "TranscriptionService",
    "TranscriptResult",
    "TranscriptSegment",
    # Analyzer (Phase 4)
    "AnalyzerService",
    "AnalysisResult",
    "ActionItem",
    "ServiceUnavailableError",
    "AnalysisTimeoutError",
    # Pipeline (Phase 5)
    "ProcessingPipeline",
    "PipelineStatus",
    "PipelineResult",
    "PipelineStage",
    "process_recording_sync",
    # Export (Phase 6)
    "ExportService",
    "ExportResult",
]
