# Services Package (`services/`)

## Overview

This package contains the business logic layer of the application. Services encapsulate complex operations and are used by API endpoints to perform tasks.

## Files

| File | Purpose | Phase |
|------|---------|-------|
| `__init__.py` | Package exports and documentation | All |
| `storage.py` | File storage and validation | Phase 2 |
| `audio.py` | Audio extraction with FFmpeg | Phase 3 |
| `transcription.py` | Whisper speech-to-text | Phase 3 |
| `analyzer.py` | LLM analysis with Ollama | Phase 4 |
| `pipeline.py` | Processing orchestration | Phase 5 |

## Files (Future Phases)

| File | Purpose | Phase |
|------|---------|-------|
| `export.py` | Export to Markdown/JSON | Phase 6 |

---

## StorageService (Phase 2)

File storage and validation service.

### Package
- `pathlib` - Cross-platform path handling

### Key Methods

| Method | Description |
|--------|-------------|
| `save_file(file_obj, recording_id, original_filename)` | Save uploaded file to disk |
| `delete_file(file_path)` | Delete a file from storage |
| `is_valid_mime_type(mime_type)` | Check if MIME type is allowed |
| `is_valid_extension(filename)` | Check if file extension is allowed |

### Constants
- `ALLOWED_MIME_TYPES` - Set of accepted audio/video MIME types
- `ALLOWED_EXTENSIONS` - Set of accepted file extensions

### Usage

```python
from app.services import StorageService

storage = StorageService()

# Save an uploaded file
file_path = storage.save_file(
    file_obj=upload.file,
    recording_id=1,
    original_filename="meeting.mp4"
)

# Validate before saving
if StorageService.is_valid_mime_type(file.content_type):
    storage.save_file(file, ...)
```

---

## AudioService (Phase 3)

Audio extraction and processing using FFmpeg.

### Packages
- `subprocess` - Execute FFmpeg commands
- `pydub` - Audio manipulation and metadata
- `pathlib` - Cross-platform paths

### System Requirements
- **FFmpeg** must be installed
  - Ubuntu: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`

### Key Methods

| Method | Description |
|--------|-------------|
| `extract_audio(input_path, output_path)` | Extract/convert audio to Whisper format |
| `get_audio_info(file_path)` | Get audio file metadata |
| `is_whisper_compatible(file_path)` | Check if file is ready for transcription |
| `is_ffmpeg_available()` | Check if FFmpeg is installed |
| `delete_processed_file(file_path)` | Delete processed audio file |

### Result Classes

**AudioExtractionResult**
```python
@dataclass
class AudioExtractionResult:
    success: bool
    output_path: Optional[Path]
    duration_seconds: float
    sample_rate: int  # Target: 16000
    channels: int     # Target: 1 (mono)
    error_message: Optional[str]
```

**AudioInfo**
```python
@dataclass
class AudioInfo:
    duration_seconds: float
    sample_rate: int
    channels: int
    format: str
```

### Usage

```python
from app.services import AudioService
from pathlib import Path

audio = AudioService()

# Check FFmpeg availability
if audio.is_ffmpeg_available():
    # Extract audio from video
    result = audio.extract_audio(
        input_path=Path("video.mp4"),
        output_path=Path("audio.wav")
    )

    if result.success:
        print(f"Duration: {result.duration_seconds}s")
        print(f"Output: {result.output_path}")

# Get audio info
info = audio.get_audio_info(Path("audio.wav"))
print(f"Sample rate: {info.sample_rate}Hz")
```

### Whisper Audio Format
The service converts audio to Whisper's optimal format:
- **Sample rate**: 16kHz
- **Channels**: 1 (mono)
- **Format**: WAV (PCM 16-bit)

---

## TranscriptionService (Phase 3)

Speech-to-text transcription using OpenAI's Whisper model.

### Packages
- `whisper` (openai-whisper) - Speech recognition model
- `dataclasses` - Result structures

### Model Sizes

| Model | Parameters | VRAM | Relative Speed |
|-------|------------|------|----------------|
| tiny | 39M | ~1GB | 32x |
| base | 74M | ~1GB | 16x |
| small | 244M | ~2GB | 6x |
| medium | 769M | ~5GB | 2x |
| large | 1550M | ~10GB | 1x |

### Key Methods

| Method | Description |
|--------|-------------|
| `transcribe(audio_path, language, task)` | Transcribe audio to text |
| `transcribe_with_timestamps(audio_path)` | Get formatted transcript with timestamps |
| `is_model_loaded()` | Check if Whisper model is loaded |
| `unload_model()` | Free model from memory |

### Result Classes

**TranscriptSegment**
```python
@dataclass
class TranscriptSegment:
    start: float      # Start time in seconds
    end: float        # End time in seconds
    text: str         # Transcribed text
    speaker: Optional[str]  # Speaker ID (if diarization enabled)
```

**TranscriptResult**
```python
@dataclass
class TranscriptResult:
    success: bool
    segments: List[TranscriptSegment]
    full_text: str
    language: str
    duration_seconds: float
    error_message: Optional[str]
```

### Usage

```python
from app.services import TranscriptionService
from pathlib import Path

# Initialize with model size
transcriber = TranscriptionService(model_size="base")

# Transcribe audio
result = transcriber.transcribe(Path("meeting.wav"))

if result.success:
    print(f"Language: {result.language}")
    print(f"Full text: {result.full_text}")

    # Access segments with timing
    for segment in result.segments:
        print(f"[{segment.start:.1f}s] {segment.text}")

# Get formatted transcript
formatted = transcriber.transcribe_with_timestamps(Path("meeting.wav"))
# Output:
# [00:00:00] Hello everyone.
# [00:00:02] Welcome to the meeting.

# Free memory when done
transcriber.unload_model()
```

### Configuration

The default model is configured in `app/config.py`:
```python
whisper_model: str = "base"  # tiny, base, small, medium, large
```

---

## AnalyzerService (Phase 4)

LLM-based meeting analysis using Ollama.

### Packages
- `httpx` - HTTP client for Ollama API
- `json` - JSON parsing for structured output
- `dataclasses` - Result structures

### System Requirements
- **Ollama** must be installed and running
  ```bash
  # Install Ollama
  curl -fsSL https://ollama.com/install.sh | sh

  # Start Ollama
  ollama serve

  # Pull a model (tinyllama is lightweight, mistral is better quality)
  ollama pull tinyllama  # or: ollama pull mistral
  ```

### Key Methods

| Method | Description |
|--------|-------------|
| `analyze(transcript)` | Analyze transcript and extract insights |
| `is_available()` | Check if Ollama is running with model |
| `list_models()` | List available Ollama models |

### Result Classes

**ActionItem**
```python
@dataclass
class ActionItem:
    speaker: str       # Person assigned
    task: str          # Task description
    due_date: Optional[str]   # Due date if mentioned
    priority: Optional[str]   # Priority level
```

**AnalysisResult**
```python
@dataclass
class AnalysisResult:
    success: bool
    summary: str                    # Meeting summary
    action_items: List[ActionItem]  # Action items with attribution
    decisions: List[str]            # Decisions made
    key_topics: List[str]           # Topics discussed
    error_message: Optional[str]
```

### Usage

```python
from app.services import AnalyzerService

analyzer = AnalyzerService()

# Check Ollama availability
if analyzer.is_available():
    # Analyze transcript
    result = analyzer.analyze('''
        Speaker 1: Let's discuss the deployment.
        Speaker 2: I'll prepare the PR by Friday.
        Speaker 1: Great. We've decided to use PostgreSQL.
    ''')

    if result.success:
        print(f"Summary: {result.summary}")

        # Action items with speaker attribution
        for item in result.action_items:
            print(f"- {item.speaker}: {item.task}")
            if item.due_date:
                print(f"  Due: {item.due_date}")

        # Decisions made
        for decision in result.decisions:
            print(f"Decision: {decision}")
```

### Configuration

Ollama settings in `app/config.py`:
```python
ollama_base_url: str = "http://localhost:11434"
ollama_model: str = "mistral"
```

### Error Handling

```python
from app.services import AnalyzerService, ServiceUnavailableError

analyzer = AnalyzerService()
result = analyzer.analyze(transcript)

if not result.success:
    print(f"Error: {result.error_message}")
    # Handle: Ollama not running, timeout, etc.
```

---

## ProcessingPipeline (Phase 5)

End-to-end processing orchestration service.

### Key Methods

| Method | Description |
|--------|-------------|
| `process(recording_id, callback)` | Run full pipeline with optional status callback |
| `get_current_status()` | Get current processing status |

### Result Classes

**PipelineStage** (Enum)
```python
class PipelineStage(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
```

**PipelineStatus**
```python
@dataclass
class PipelineStatus:
    recording_id: int
    stage: PipelineStage
    progress: int       # 0-100
    message: str
    error: Optional[str]
    started_at: Optional[datetime]
    updated_at: Optional[datetime]
```

**PipelineResult**
```python
@dataclass
class PipelineResult:
    success: bool
    recording_id: int
    transcript_id: Optional[int]
    analysis_id: Optional[int]
    duration_seconds: float
    error_message: Optional[str]
```

### Usage

```python
from app.services import ProcessingPipeline
from app.db.database import SessionLocal

db = SessionLocal()
pipeline = ProcessingPipeline(db)

# Process with status callback
def on_status(status):
    print(f"Stage: {status.stage}, Progress: {status.progress}%")

result = pipeline.process(recording_id=1, callback=on_status)

if result.success:
    print(f"Completed in {result.duration_seconds:.1f}s")
    print(f"Transcript ID: {result.transcript_id}")
    print(f"Analysis ID: {result.analysis_id}")
else:
    print(f"Failed: {result.error_message}")
```

### Pipeline Flow

1. **EXTRACTING** - Extract/convert audio to Whisper format (16kHz mono WAV)
2. **TRANSCRIBING** - Transcribe audio using Whisper
3. **ANALYZING** - Generate summary and action items using Ollama LLM
4. **COMPLETED** or **FAILED** - Final status

### Error Handling

- Audio extraction failure → Pipeline fails
- Transcription failure → Pipeline fails
- Analysis failure → Pipeline succeeds (analysis is optional)
- If Ollama is unavailable, pipeline skips analysis and succeeds

---

## Service Pattern

All services follow a consistent pattern:

```python
# services/example.py
from app.config import settings

class ExampleService:
    """Service for handling example operations."""

    def __init__(self, config=None):
        """Initialize with optional configuration."""
        self.config = config or default_config

    def process(self, input_data):
        """
        Perform the operation.

        Args:
            input_data: Data to process

        Returns:
            Result dataclass with success flag and data
        """
        # Business logic here
        return result
```

## Why Use Services?

1. **Separation of Concerns**: API endpoints handle HTTP, services handle logic
2. **Testability**: Services can be tested independently of HTTP layer
3. **Reusability**: Services can be used by multiple endpoints
4. **Maintainability**: Complex logic is organized in one place

## Example: Full Processing Pipeline

```python
# In API endpoint - using ProcessingPipeline service
from fastapi import BackgroundTasks
from app.services import ProcessingPipeline
from app.db.database import SessionLocal

@router.post("/recordings/{id}/process")
async def process_recording(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Validate recording exists
    recording = db.query(Recording).filter(Recording.id == id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    # Add processing to background tasks
    background_tasks.add_task(run_pipeline, id)

    return {"message": "Processing started", "recording_id": id}


def run_pipeline(recording_id: int):
    """Run pipeline in background with separate db session."""
    db = SessionLocal()
    try:
        pipeline = ProcessingPipeline(db)
        result = pipeline.process(recording_id)

        if result.success:
            print(f"Completed: transcript={result.transcript_id}, analysis={result.analysis_id}")
        else:
            print(f"Failed: {result.error_message}")
    finally:
        db.close()
```
