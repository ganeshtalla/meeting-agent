# Meeting Agent

A local-first meeting recording analyzer that transcribes audio/video recordings and extracts actionable insights using AI.

## Features

- **Upload** audio/video recordings (MP3, WAV, MP4, WebM, etc.)
- **Transcribe** speech to text using OpenAI Whisper (runs locally)
- **Analyze** transcripts with local LLM (Ollama) to extract:
  - Meeting summary
  - Action items with speaker attribution
  - Key decisions made
  - Important topics discussed
- **Export** results to Markdown, JSON, or plain text
- **Real-time status** updates via WebSocket during processing

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.10+ / FastAPI |
| **Frontend** | React 18 + TypeScript + Vite |
| **Transcription** | OpenAI Whisper (local) |
| **LLM** | Ollama (local) / OpenAI / Anthropic |
| **Database** | SQLite + SQLAlchemy |
| **Audio Processing** | FFmpeg + pydub |
| **Testing** | pytest (backend) + vitest (frontend) |

---

## Quick Start

### Prerequisites

Install system dependencies:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv ffmpeg nodejs npm

# macOS
brew install python ffmpeg node
```

Install Ollama (local LLM runtime) - or use OpenAI/Anthropic API keys:

```bash
# Option 1: Local LLM with Ollama (free, private)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral

# Option 2: OpenAI API (set OPENAI_API_KEY in .env)
# Option 3: Anthropic Claude API (set ANTHROPIC_API_KEY in .env)
```

### Setup & Run

**Terminal 1 - Backend:**
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

**Terminal 3 - Ollama (if not running as service):**
```bash
ollama serve
```

### Verify Installation

```bash
# Backend health check
curl http://localhost:8000/api/health
# Expected: {"status":"ok","database":"ok"}

# Ollama check
curl http://localhost:11434/api/tags
# Expected: {"models":[{"name":"mistral",...}]}

# Frontend
open http://localhost:5173
```

---

## Project Structure

```
meeting-agent/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   ├── config.py       # Configuration settings
│   │   ├── api/            # REST endpoints
│   │   ├── db/             # Database layer
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── tests/              # pytest tests
│   ├── requirements.txt    # Python dependencies
│   └── README.md           # Backend documentation
│
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   ├── tests/              # vitest tests
│   ├── package.json        # Node dependencies
│   └── README.md           # Frontend documentation
│
├── uploads/                # Uploaded recordings
├── processed/              # Processed audio files
└── README.md               # This file
```

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.10 or higher |
| Node.js | 18 or higher |
| RAM | 4 GB (8 GB recommended) |
| Disk Space | 10 GB (for models and recordings) |
| FFmpeg | Required for audio processing |

### Optional (for LLM Analysis)

| Component | Requirement |
|-----------|-------------|
| Ollama | Latest version |
| LLM Model | mistral (4.4 GB) or tinyllama (637 MB) |

---

## Backend Dependencies

```
# requirements.txt
fastapi>=0.109.0          # Web framework
uvicorn>=0.27.0           # ASGI server
sqlalchemy>=2.0.0         # Database ORM
pydantic>=2.0.0           # Data validation
pydantic-settings>=2.0.0  # Settings management
python-multipart>=0.0.6   # File uploads
openai-whisper>=20231117  # Speech-to-text
pydub>=0.25.1             # Audio processing
httpx>=0.26.0             # HTTP client
websockets>=12.0          # WebSocket support
pytest>=8.0.0             # Testing
pytest-asyncio>=0.23.0    # Async test support

# Optional LLM providers
openai>=1.0.0             # OpenAI API (GPT-4, GPT-3.5)
anthropic>=0.18.0         # Anthropic API (Claude)
```

## Frontend Dependencies

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.0.0"
  },
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vitest": "^1.2.0"
  }
}
```

---

## Environment Variables

### Backend (.env)

Create `backend/.env`:

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

# LLM Provider (ollama, openai, or anthropic)
LLM_PROVIDER=ollama

# Ollama (local LLM - default)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# OpenAI (optional - set API key to enable)
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o-mini  # Options: gpt-4o, gpt-4o-mini, gpt-4-turbo

# Anthropic Claude (optional - set API key to enable)
ANTHROPIC_API_KEY=sk-ant-your-api-key
ANTHROPIC_MODEL=claude-sonnet-4-20250514  # Options: claude-sonnet-4-20250514, claude-3-5-haiku-20241022

# LLM Settings
LLM_TIMEOUT=120
LLM_TEMPERATURE=0.3

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Frontend (.env)

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/recordings/upload` | Upload recording |
| GET | `/api/recordings` | List recordings |
| GET | `/api/recordings/{id}` | Get recording |
| DELETE | `/api/recordings/{id}` | Delete recording |
| POST | `/api/recordings/{id}/process` | Start processing |
| GET | `/api/recordings/{id}/details` | Get with transcript & analysis |
| GET | `/api/recordings/{id}/export` | Export (markdown/json/text) |
| WS | `/ws/recordings/{id}` | Real-time status updates |

Full API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Running Tests

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests (excluding slow integration tests)
pytest -v -m "not slow"

# Run all tests including integration
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_pipeline.py -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

### Test Summary

| Component | Test File | Tests |
|-----------|-----------|-------|
| Backend | test_health.py | 5 |
| Backend | test_upload.py | 14 |
| Backend | test_audio.py | 22 |
| Backend | test_transcription.py | 18 |
| Backend | test_analyzer.py | 24 |
| Backend | test_pipeline.py | 22 |
| Backend | test_websocket.py | 17 |
| Backend | test_export.py | 29 |
| **Total** | | **151** |

---

## Usage Workflow

1. **Upload a recording**
   ```bash
   curl -X POST http://localhost:8000/api/recordings/upload \
     -F "file=@meeting.mp3" \
     -F "title=Sprint Planning"
   # Returns: {"id": 1, "status": "pending", ...}
   ```

2. **Start processing**
   ```bash
   curl -X POST http://localhost:8000/api/recordings/1/process
   # Returns: {"message": "Processing started", "recording_id": 1}
   ```

3. **Check status** (or use WebSocket for real-time)
   ```bash
   curl http://localhost:8000/api/recordings/1
   # Returns: {"status": "processing", ...} or {"status": "completed", ...}
   ```

4. **Get results**
   ```bash
   curl http://localhost:8000/api/recordings/1/details
   # Returns full transcript and analysis
   ```

5. **Export**
   ```bash
   curl http://localhost:8000/api/recordings/1/export?format=markdown
   # Returns formatted Markdown report
   ```

---

## Troubleshooting

### FFmpeg not found
```bash
# Verify installation
ffmpeg -version

# Install if missing
sudo apt install ffmpeg  # Ubuntu
brew install ffmpeg      # macOS
```

### Ollama connection refused
```bash
# Start Ollama service
ollama serve

# Or check if running
curl http://localhost:11434/api/tags
```

### Whisper model download fails
```bash
# Clear cache and retry
rm -rf ~/.cache/whisper/
python3 -c "import whisper; whisper.load_model('base')"
```

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Database errors
```bash
# Reset database
rm backend/meeting_agent.db
# Restart server (creates new DB)
```

---

## Development

### Adding a New Feature

1. Create/modify backend service in `backend/app/services/`
2. Add API endpoint in `backend/app/api/`
3. Create Pydantic schemas in `backend/app/schemas/`
4. Add tests in `backend/tests/`
5. Update frontend components as needed
6. Update documentation

### Code Style

- Backend: Follow PEP 8, use type hints
- Frontend: Follow ESLint rules, use TypeScript strictly

---

## License

MIT License - See LICENSE file for details.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [Ollama](https://ollama.com/) - Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework
