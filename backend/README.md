# Meeting Agent - Backend

## Overview

FastAPI backend for the Meeting Agent application. Provides REST API endpoints for uploading, processing, transcribing, and analyzing meeting recordings.

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | High-performance async web framework |
| Database ORM | SQLAlchemy 2.0 | Database abstraction and models |
| Data Validation | Pydantic 2.0 | Request/response validation |
| ASGI Server | Uvicorn | Production-ready ASGI server |
| Transcription | OpenAI Whisper | Speech-to-text conversion |
| Audio Processing | pydub + FFmpeg | Audio file manipulation |
| LLM Analysis | Ollama | Local LLM for meeting analysis |
| HTTP Client | httpx | Async HTTP requests |
| WebSockets | websockets | Real-time status updates |
| Testing | pytest | Unit and integration testing |

---

## Quick Start

```bash
# 1. Install system dependencies
sudo apt install ffmpeg  # Ubuntu/Debian
# brew install ffmpeg    # macOS

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn app.main:app --reload --port 8000

# 5. Verify it works
curl http://localhost:8000/api/health
```

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application configuration
│   ├── api/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoint
│   │   ├── recordings.py    # Recording CRUD endpoints
│   │   └── websocket.py     # WebSocket status updates
│   ├── db/                  # Database layer
│   │   ├── __init__.py
│   │   └── database.py      # SQLAlchemy engine and session
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── recording.py     # Recording model
│   │   └── transcript.py    # Transcript model
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── recording.py     # Recording schemas
│   │   └── transcript.py    # Transcript schemas
│   └── services/            # Business logic
│       ├── __init__.py
│       ├── storage.py       # File storage service
│       ├── audio.py         # Audio extraction (FFmpeg)
│       ├── transcription.py # Whisper transcription
│       ├── analyzer.py      # LLM analysis (Ollama)
│       ├── pipeline.py      # Processing orchestration
│       └── export.py        # Export to Markdown/JSON/Text
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_health.py       # Health endpoint tests
│   ├── test_upload.py       # Upload endpoint tests
│   ├── test_audio.py        # Audio service tests
│   ├── test_transcription.py # Transcription tests
│   ├── test_analyzer.py     # Analyzer service tests
│   ├── test_pipeline.py     # Pipeline service tests
│   ├── test_websocket.py    # WebSocket tests
│   └── test_export.py       # Export service tests
├── uploads/                 # Uploaded recordings
├── processed/               # Processed audio files
├── requirements.txt
└── pyproject.toml
```

---

## System Requirements

### Required for All Phases
- Python 3.10+
- pip (Python package manager)

### Phase 3+ Requirements
- **FFmpeg** - Audio/video processing
  ```bash
  # Ubuntu/Debian
  sudo apt install ffmpeg

  # macOS
  brew install ffmpeg

  # Verify installation
  ffmpeg -version
  ```

### Phase 4+ Requirements
- **LLM Provider** - Choose one of the following:

  **Option 1: Ollama (Local - Free & Private)**
  ```bash
  # Install Ollama
  curl -fsSL https://ollama.com/install.sh | sh

  # Pull a model
  ollama pull mistral   # 4.4 GB - recommended
  # ollama pull llama2    # 3.8 GB - alternative

  # Verify
  ollama list
  ```

  **Option 2: OpenAI API**
  ```bash
  # Set in .env file
  LLM_PROVIDER=openai
  OPENAI_API_KEY=sk-your-api-key
  OPENAI_MODEL=gpt-4o-mini  # or gpt-4o, gpt-4-turbo
  ```

  **Option 3: Anthropic Claude API**
  ```bash
  # Set in .env file
  LLM_PROVIDER=anthropic
  ANTHROPIC_API_KEY=sk-ant-your-api-key
  ANTHROPIC_MODEL=claude-sonnet-4-20250514  # or claude-3-5-haiku-20241022
  ```

---

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite:///./meeting_agent.db

# File Storage
UPLOAD_DIR=uploads
PROCESSED_DIR=processed
MAX_FILE_SIZE_MB=500

# CORS (frontend URLs)
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Whisper (transcription)
WHISPER_MODEL=base  # tiny, base, small, medium, large

# LLM Provider Configuration
LLM_PROVIDER=ollama  # ollama, openai, or anthropic

# Ollama (local - default)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# OpenAI (optional)
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o-mini  # gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo

# Anthropic (optional)
ANTHROPIC_API_KEY=sk-ant-your-api-key
ANTHROPIC_MODEL=claude-sonnet-4-20250514  # claude-sonnet-4-20250514, claude-3-5-haiku-20241022

# LLM Settings
LLM_TIMEOUT=120
LLM_TEMPERATURE=0.3

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

## API Endpoints

| Method | Endpoint | Description | Phase |
|--------|----------|-------------|-------|
| GET | `/` | Root endpoint with API info | 1 |
| GET | `/api/health` | Health check with DB status | 1 |
| POST | `/api/recordings/upload` | Upload a recording | 2 |
| GET | `/api/recordings` | List all recordings | 2 |
| GET | `/api/recordings/{id}` | Get recording details | 2 |
| DELETE | `/api/recordings/{id}` | Delete a recording | 2 |
| POST | `/api/recordings/{id}/process` | Start processing | 5 |
| GET | `/api/recordings/{id}/details` | Get with transcript & analysis | 5 |
| WS | `/ws/recordings/{id}` | WebSocket status updates | 5 |
| GET | `/api/recordings/{id}/export` | Export to Markdown/JSON/Text | 6 |
| GET | `/api/recordings/{id}/export/action-items` | Export action items only | 6 |
| GET | `/docs` | Swagger UI documentation | 1 |
| GET | `/redoc` | ReDoc documentation | 1 |

---

## Phase-by-Phase Guide

### Phase 1: Project Setup & Core Infrastructure

**What's Included:**
- FastAPI application with CORS
- SQLite database with SQLAlchemy
- Health check endpoint
- Pydantic configuration
- pytest test setup

**Requirements:**
```bash
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings
```

**Run & Verify:**
```bash
# Start server
uvicorn app.main:app --reload --port 8000

# Verify health check
curl http://localhost:8000/api/health
# Expected: {"status":"ok","database":"ok"}

# Run tests
pytest tests/test_health.py -v
# Expected: 5 passed
```

---

### Phase 2: File Upload & Storage

**What's Included:**
- File upload endpoint (multipart/form-data)
- File validation (type, size, extension)
- Recording CRUD operations
- File storage on disk

**Additional Requirements:**
```bash
pip install python-multipart
```

**Run & Verify:**
```bash
# Start server
uvicorn app.main:app --reload --port 8000

# Upload a test file
curl -X POST http://localhost:8000/api/recordings/upload \
  -F "file=@test.mp3"
# Expected: {"id":1,"title":"test","status":"pending",...}

# List recordings
curl http://localhost:8000/api/recordings
# Expected: {"recordings":[...],"total":1}

# Run tests
pytest tests/test_upload.py -v
# Expected: 14 passed
```

---

### Phase 3: Audio Processing & Transcription

**What's Included:**
- Audio extraction from video (FFmpeg)
- Audio conversion to Whisper format (16kHz mono WAV)
- Whisper speech-to-text transcription
- Transcript model with timed segments

**System Requirements:**
```bash
# Install FFmpeg
sudo apt install ffmpeg  # Ubuntu
brew install ffmpeg      # macOS
```

**Additional Python Requirements:**
```bash
pip install openai-whisper pydub
```

**Run & Verify:**
```bash
# Verify FFmpeg
ffmpeg -version

# Start server
uvicorn app.main:app --reload --port 8000

# Test audio service (in Python)
python3 -c "
from app.services import AudioService
print('FFmpeg available:', AudioService.is_ffmpeg_available())
"
# Expected: FFmpeg available: True

# Test transcription service (downloads model on first run)
python3 -c "
from app.services import TranscriptionService
svc = TranscriptionService(model_size='tiny')
print('Model size:', svc.model_size)
"
# Expected: Model size: tiny

# Run tests
pytest tests/test_audio.py tests/test_transcription.py -v -m "not slow"
# Expected: 40 passed
```

---

### Phase 4: LLM Analysis & Action Extraction

**What's Included:**
- Ollama integration for local LLM
- Meeting summary generation
- Action item extraction with speaker attribution
- Decision identification
- Analysis model for storing results

**System Requirements:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Pull the model (one-time)
ollama pull mistral

# Verify
ollama list
```

**Additional Python Requirements:**
```bash
pip install httpx
```

**Run & Verify:**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags
# Expected: {"models":[{"name":"mistral",...}]}

# Start server
uvicorn app.main:app --reload --port 8000

# Test analyzer service (in Python)
python3 -c "
from app.services import AnalyzerService
svc = AnalyzerService()
print('Ollama available:', svc.is_available())
"
# Expected: Ollama available: True

# Run tests
pytest tests/test_analyzer.py -v -m "not slow"
# Expected: All passed
```

---

### Phase 5: Processing Pipeline & Status Tracking

**What's Included:**
- End-to-end processing pipeline (audio → transcription → analysis)
- Status updates (pending → processing → completed/failed)
- WebSocket for real-time status updates
- Background task processing
- New API endpoints: `/process`, `/details`

**New Files:**
- `backend/app/services/pipeline.py` - Processing orchestration
- `backend/app/api/websocket.py` - WebSocket endpoint

**New Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/recordings/{id}/process` | Start processing a recording |
| GET | `/api/recordings/{id}/details` | Get recording with transcript & analysis |
| WS | `/ws/recordings/{id}` | WebSocket for real-time status updates |

**Run & Verify:**
```bash
# Start server
uvicorn app.main:app --reload --port 8000

# Upload a recording
curl -X POST http://localhost:8000/api/recordings/upload \
  -F "file=@meeting.wav"
# Response: {"id": 1, "status": "pending", ...}

# Start processing
curl -X POST http://localhost:8000/api/recordings/1/process
# Response: {"message": "Processing started", "recording_id": 1}

# Check status (poll or use WebSocket)
curl http://localhost:8000/api/recordings/1
# Response: {"status": "processing", ...} or {"status": "completed", ...}

# Get full details after processing
curl http://localhost:8000/api/recordings/1/details
# Response includes transcript and analysis

# Run tests
pytest tests/test_pipeline.py tests/test_websocket.py -v -m "not slow"
# Expected: 39 passed
```

**WebSocket Usage (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/recordings/1');

ws.onmessage = (event) => {
    const status = JSON.parse(event.data);
    console.log(`Stage: ${status.stage}, Progress: ${status.progress}%`);

    if (status.stage === 'completed' || status.stage === 'failed') {
        ws.close();
    }
};
```

---

### Phase 6: Results Display & Export

**What's Included:**
- Export to Markdown format (full meeting report)
- Export to JSON format (structured data)
- Export to plain text (transcript only)
- Action items export (checklist format)
- Configurable options (timestamps, formatting)

**New Files:**
- `backend/app/services/export.py` - Export service with multiple formats

**New Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recordings/{id}/export?format=markdown` | Export as Markdown |
| GET | `/api/recordings/{id}/export?format=json` | Export as JSON |
| GET | `/api/recordings/{id}/export?format=text` | Export transcript as text |
| GET | `/api/recordings/{id}/export/action-items` | Export action items only |

**Run & Verify:**
```bash
# Start server
uvicorn app.main:app --reload --port 8000

# Export as Markdown (after processing a recording)
curl http://localhost:8000/api/recordings/1/export?format=markdown
# Response: Markdown content with summary, action items, transcript

# Export as JSON
curl http://localhost:8000/api/recordings/1/export?format=json
# Response: Structured JSON with all meeting data

# Export transcript only
curl http://localhost:8000/api/recordings/1/export?format=text
# Response: Plain text transcript with timestamps

# Export action items
curl http://localhost:8000/api/recordings/1/export/action-items
# Response: Markdown checklist of action items

# Run tests
pytest tests/test_export.py -v
# Expected: 29 passed
```

**Export Formats:**

**Markdown Export:**
```markdown
# Sprint Planning Meeting

## Meeting Details
- **Date**: 2024-01-15 10:00
- **Duration**: 30m 0s
- **File**: meeting.mp4

## Summary
Team discussed project timeline and deliverables.

## Action Items
- [ ] **John**: Review the PR *(Due: Friday)*
- [ ] **Sarah**: Send email to client *(Due: Today)* `high`

## Decisions Made
- Use PostgreSQL for the database

## Transcript
[00:00] Hello everyone.
[00:02] Let's discuss the project.
```

**JSON Export:**
```json
{
  "metadata": {
    "exported_at": "2024-01-15T10:30:00",
    "export_version": "1.0"
  },
  "recording": {
    "id": 1,
    "title": "Sprint Planning Meeting"
  },
  "transcript": {
    "full_text": "...",
    "segments": [...]
  },
  "analysis": {
    "summary": "...",
    "action_items": [...],
    "decisions": [...]
  }
}
```

---

## Running Tests

```bash
# Run all tests (excluding slow integration tests)
pytest -v -m "not slow"

# Run all tests including slow ones
pytest -v

# Run specific test file
pytest tests/test_health.py -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run tests for specific phase
pytest tests/test_health.py -v                    # Phase 1
pytest tests/test_upload.py -v                    # Phase 2
pytest tests/test_audio.py tests/test_transcription.py -v  # Phase 3
pytest tests/test_analyzer.py -v                  # Phase 4
pytest tests/test_pipeline.py tests/test_websocket.py -v   # Phase 5
pytest tests/test_export.py -v                    # Phase 6
```

### Current Test Status

| Test File | Tests | Phase |
|-----------|-------|-------|
| test_health.py | 5 | Phase 1 |
| test_upload.py | 14 | Phase 2 |
| test_audio.py | 22 | Phase 3 |
| test_transcription.py | 18 | Phase 3 |
| test_analyzer.py | 38 | Phase 4 |
| test_pipeline.py | 22 | Phase 5 |
| test_websocket.py | 17 | Phase 5 |
| test_export.py | 29 | Phase 6 |
| **Total** | **165** | |

---

## Running the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With custom log level
uvicorn app.main:app --reload --log-level debug
```

---

## Troubleshooting

### FFmpeg not found
```bash
# Check if installed
which ffmpeg

# Install if missing
sudo apt install ffmpeg  # Ubuntu
brew install ffmpeg      # macOS
```

### Ollama connection refused
```bash
# Start Ollama service
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

### Whisper model download fails
```bash
# Models are cached in ~/.cache/whisper/
# Clear cache and retry
rm -rf ~/.cache/whisper/
python3 -c "import whisper; whisper.load_model('base')"
```

### Database errors
```bash
# Delete and recreate database
rm meeting_agent.db
uvicorn app.main:app --reload  # Creates new DB on startup
```

---

## Development

### Adding a New Endpoint

1. Create route in `app/api/`
2. Add schema in `app/schemas/`
3. Register router in `app/api/__init__.py`
4. Include router in `app/main.py`
5. Add tests in `tests/`

### Adding a New Service

1. Create service in `app/services/`
2. Export from `app/services/__init__.py`
3. Add tests in `tests/`
4. Update README documentation
