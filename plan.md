# Meeting Agent - Implementation Plan

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+ / FastAPI |
| **Frontend** | React 18 + TypeScript + Vite |
| **Transcription** | whisper (openai-whisper) |
| **LLM** | Ollama (local) with Mistral/Llama |
| **Database** | SQLite + SQLAlchemy |
| **Audio Processing** | FFmpeg + pydub |
| **Testing** | pytest (backend) + vitest (frontend) |

---

## Project Structure

```
meeting-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings/configuration
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── recording.py
│   │   │   └── analysis.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── recording.py
│   │   │   └── analysis.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── transcription.py
│   │   │   ├── analyzer.py
│   │   │   └── audio.py
│   │   ├── api/                 # Route handlers
│   │   │   ├── __init__.py
│   │   │   ├── recordings.py
│   │   │   └── health.py
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── database.py
│   │       └── migrations/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_transcription.py
│   │   ├── test_analyzer.py
│   │   ├── test_api.py
│   │   └── fixtures/
│   │       └── sample.wav
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── FileUpload.tsx
│   │   │   ├── RecordingList.tsx
│   │   │   ├── ProcessingStatus.tsx
│   │   │   └── ResultsView.tsx
│   │   ├── hooks/
│   │   │   └── useRecordings.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── index.ts
│   ├── tests/
│   │   └── components/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── uploads/                     # Uploaded recordings
├── processed/                   # Extracted audio
└── docker-compose.yml           # Ollama service
```

---

## Implementation Phases

---

## Phase 1: Project Setup & Core Infrastructure

### Scope
- Initialize Python backend with FastAPI
- Initialize React frontend with Vite + TypeScript
- Setup SQLite database with SQLAlchemy
- Basic health check endpoint
- CORS configuration

### Files to Create

**Backend:**
- `backend/app/main.py` - FastAPI application
- `backend/app/config.py` - Configuration settings
- `backend/app/db/database.py` - Database connection
- `backend/app/models/recording.py` - Recording model
- `backend/app/schemas/recording.py` - Pydantic schemas
- `backend/app/api/health.py` - Health check route
- `backend/requirements.txt` - Dependencies
- `backend/pyproject.toml` - Project config

**Frontend:**
- `frontend/package.json` - Dependencies
- `frontend/src/main.tsx` - Entry point
- `frontend/src/App.tsx` - Root component
- `frontend/src/services/api.ts` - API client
- `frontend/src/types/index.ts` - TypeScript types

### Test Cases - Phase 1

```python
# backend/tests/test_health.py

def test_health_check_returns_ok(client):
    """Health endpoint should return 200 with status ok"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_database_connection(db_session):
    """Database session should be active and usable"""
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

def test_cors_headers_present(client):
    """CORS headers should be present for frontend access"""
    response = client.options("/api/health", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-origin" in response.headers
```

```typescript
// frontend/tests/api.test.ts

describe('API Client', () => {
  it('should have correct base URL configured', () => {
    expect(api.defaults.baseURL).toBe('http://localhost:8000/api');
  });

  it('should handle health check response', async () => {
    const response = await api.get('/health');
    expect(response.data.status).toBe('ok');
  });
});
```

---

## Phase 2: File Upload & Storage

### Scope
- File upload endpoint (multipart/form-data)
- File validation (type, size)
- Store file metadata in database
- React file upload component with drag-drop

### Files to Create/Modify

**Backend:**
- `backend/app/api/recordings.py` - Upload endpoint
- `backend/app/services/storage.py` - File storage service
- Modify `backend/app/models/recording.py` - Add fields

**Frontend:**
- `frontend/src/components/FileUpload.tsx` - Upload UI
- `frontend/src/hooks/useFileUpload.ts` - Upload logic

### Test Cases - Phase 2

```python
# backend/tests/test_upload.py

def test_upload_valid_audio_file(client, sample_audio_file):
    """Should accept valid audio file and return recording ID"""
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.wav", sample_audio_file, "audio/wav")}
    )
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["status"] == "pending"

def test_upload_rejects_invalid_file_type(client):
    """Should reject non-audio files"""
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.txt", b"not audio", "text/plain")}
    )
    assert response.status_code == 400
    assert "invalid file type" in response.json()["detail"].lower()

def test_upload_rejects_oversized_file(client, large_file):
    """Should reject files exceeding size limit"""
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("large.wav", large_file, "audio/wav")}
    )
    assert response.status_code == 413

def test_upload_creates_database_record(client, db_session, sample_audio_file):
    """Upload should create a recording entry in database"""
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.wav", sample_audio_file, "audio/wav")}
    )
    recording_id = response.json()["id"]
    recording = db_session.query(Recording).filter_by(id=recording_id).first()
    assert recording is not None
    assert recording.status == "pending"

def test_upload_stores_file_on_disk(client, sample_audio_file):
    """Upload should save file to uploads directory"""
    response = client.post(
        "/api/recordings/upload",
        files={"file": ("test.wav", sample_audio_file, "audio/wav")}
    )
    recording_id = response.json()["id"]
    # Check file exists
    assert Path(f"uploads/{recording_id}.wav").exists()
```

```typescript
// frontend/tests/FileUpload.test.tsx

describe('FileUpload Component', () => {
  it('should render drop zone', () => {
    render(<FileUpload onUpload={vi.fn()} />);
    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument();
  });

  it('should accept audio files', async () => {
    const onUpload = vi.fn();
    render(<FileUpload onUpload={onUpload} />);

    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' });
    const input = screen.getByTestId('file-input');
    await userEvent.upload(input, file);

    expect(onUpload).toHaveBeenCalledWith(file);
  });

  it('should reject non-audio files', async () => {
    render(<FileUpload onUpload={vi.fn()} />);

    const file = new File(['text'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByTestId('file-input');
    await userEvent.upload(input, file);

    expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
  });

  it('should show upload progress', async () => {
    render(<FileUpload onUpload={vi.fn()} />);
    // Simulate upload in progress
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

---

## Phase 3: Audio Processing & Transcription

### Scope
- Extract audio from video files using FFmpeg
- Transcribe audio using Whisper
- Background task processing
- Store transcript with timestamps

### Files to Create/Modify

**Backend:**
- `backend/app/services/audio.py` - Audio extraction
- `backend/app/services/transcription.py` - Whisper integration
- `backend/app/models/transcript.py` - Transcript model
- `backend/app/tasks/process.py` - Background processing

### Test Cases - Phase 3

```python
# backend/tests/test_audio.py

def test_extract_audio_from_video(sample_video_path, tmp_path):
    """Should extract audio track from video file"""
    output_path = tmp_path / "output.wav"
    result = extract_audio(sample_video_path, output_path)

    assert result.success
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_extract_audio_converts_to_16khz_mono(sample_video_path, tmp_path):
    """Extracted audio should be 16kHz mono for Whisper"""
    output_path = tmp_path / "output.wav"
    extract_audio(sample_video_path, output_path)

    # Verify format
    audio = AudioSegment.from_wav(output_path)
    assert audio.frame_rate == 16000
    assert audio.channels == 1

def test_extract_audio_handles_missing_file():
    """Should raise error for non-existent file"""
    with pytest.raises(FileNotFoundError):
        extract_audio(Path("/nonexistent.mp4"), Path("/output.wav"))


# backend/tests/test_transcription.py

def test_transcribe_audio_returns_segments(sample_audio_path):
    """Should return list of transcript segments"""
    result = transcribe_audio(sample_audio_path)

    assert isinstance(result.segments, list)
    assert len(result.segments) > 0

def test_transcript_segment_has_required_fields(sample_audio_path):
    """Each segment should have start, end, text"""
    result = transcribe_audio(sample_audio_path)
    segment = result.segments[0]

    assert "start" in segment
    assert "end" in segment
    assert "text" in segment
    assert isinstance(segment["start"], float)
    assert isinstance(segment["end"], float)

def test_transcribe_handles_empty_audio(silent_audio_path):
    """Should handle silent/empty audio gracefully"""
    result = transcribe_audio(silent_audio_path)
    assert result.segments == [] or result.text == ""

def test_transcribe_long_audio_in_chunks(long_audio_path):
    """Should process long audio without memory issues"""
    result = transcribe_audio(long_audio_path)  # 30+ min file
    assert result.success
    assert len(result.text) > 0
```

---

## Phase 4: LLM Analysis & Action Extraction

### Scope
- Integrate with Ollama for local LLM
- Design analysis prompt
- Parse structured output (summary, actions, decisions)
- Store analysis results

### Files to Create/Modify

**Backend:**
- `backend/app/services/analyzer.py` - LLM analysis service
- `backend/app/models/analysis.py` - Analysis model
- `backend/app/schemas/analysis.py` - Response schemas

### Test Cases - Phase 4

```python
# backend/tests/test_analyzer.py

SAMPLE_TRANSCRIPT = """
Speaker 1: Let's discuss the deployment timeline.
Speaker 2: I can have the PR ready by Friday.
Speaker 1: Great. Can you also send an email to the client?
Speaker 2: Sure, I'll send that today.
Speaker 1: We've decided to use PostgreSQL instead of MySQL.
"""

def test_analyzer_returns_summary(analyzer_service):
    """Should generate meeting summary"""
    result = analyzer_service.analyze(SAMPLE_TRANSCRIPT)

    assert result.summary is not None
    assert len(result.summary) > 20
    assert len(result.summary) < 500  # Concise

def test_analyzer_extracts_action_items(analyzer_service):
    """Should extract action items with speaker attribution"""
    result = analyzer_service.analyze(SAMPLE_TRANSCRIPT)

    assert len(result.action_items) >= 2

    # Check structure
    action = result.action_items[0]
    assert "speaker" in action
    assert "task" in action

def test_analyzer_extracts_decisions(analyzer_service):
    """Should identify decisions made"""
    result = analyzer_service.analyze(SAMPLE_TRANSCRIPT)

    assert len(result.decisions) >= 1
    assert any("postgresql" in d.lower() for d in result.decisions)

def test_analyzer_handles_empty_transcript(analyzer_service):
    """Should handle empty input gracefully"""
    result = analyzer_service.analyze("")

    assert result.summary == "" or "no content" in result.summary.lower()
    assert result.action_items == []

def test_analyzer_handles_ollama_connection_error(analyzer_service, mocker):
    """Should raise clear error when Ollama unavailable"""
    mocker.patch('httpx.post', side_effect=ConnectionError)

    with pytest.raises(ServiceUnavailableError) as exc:
        analyzer_service.analyze(SAMPLE_TRANSCRIPT)

    assert "ollama" in str(exc.value).lower()

def test_analyzer_respects_timeout(analyzer_service, mocker):
    """Should timeout for very long analysis"""
    mocker.patch('httpx.post', side_effect=TimeoutError)

    with pytest.raises(AnalysisTimeoutError):
        analyzer_service.analyze(SAMPLE_TRANSCRIPT)
```

---

## Phase 5: Processing Pipeline & Status Tracking

### Scope
- End-to-end processing pipeline
- Status updates (pending → processing → completed/failed)
- WebSocket for real-time status updates
- Error handling and retry logic

### Files to Create/Modify

**Backend:**
- `backend/app/services/pipeline.py` - Orchestration
- `backend/app/api/websocket.py` - WebSocket endpoint
- Modify `backend/app/models/recording.py` - Status tracking

**Frontend:**
- `frontend/src/components/ProcessingStatus.tsx`
- `frontend/src/hooks/useWebSocket.ts`

### Test Cases - Phase 5

```python
# backend/tests/test_pipeline.py

def test_pipeline_updates_status_to_processing(db_session, sample_recording):
    """Pipeline should update status to processing when started"""
    pipeline = ProcessingPipeline(db_session)
    pipeline.start(sample_recording.id)

    db_session.refresh(sample_recording)
    assert sample_recording.status == "processing"

def test_pipeline_updates_status_to_completed(db_session, sample_recording):
    """Pipeline should update status to completed on success"""
    pipeline = ProcessingPipeline(db_session)
    pipeline.process(sample_recording.id)

    db_session.refresh(sample_recording)
    assert sample_recording.status == "completed"
    assert sample_recording.processed_at is not None

def test_pipeline_updates_status_to_failed_on_error(db_session, sample_recording, mocker):
    """Pipeline should update status to failed on error"""
    mocker.patch.object(TranscriptionService, 'transcribe', side_effect=Exception("Whisper failed"))

    pipeline = ProcessingPipeline(db_session)
    with pytest.raises(Exception):
        pipeline.process(sample_recording.id)

    db_session.refresh(sample_recording)
    assert sample_recording.status == "failed"
    assert sample_recording.error_message is not None

def test_pipeline_creates_transcript_record(db_session, sample_recording):
    """Pipeline should create transcript in database"""
    pipeline = ProcessingPipeline(db_session)
    pipeline.process(sample_recording.id)

    transcript = db_session.query(Transcript).filter_by(recording_id=sample_recording.id).first()
    assert transcript is not None
    assert len(transcript.segments) > 0

def test_pipeline_creates_analysis_record(db_session, sample_recording):
    """Pipeline should create analysis in database"""
    pipeline = ProcessingPipeline(db_session)
    pipeline.process(sample_recording.id)

    analysis = db_session.query(Analysis).filter_by(recording_id=sample_recording.id).first()
    assert analysis is not None
    assert analysis.summary is not None


# backend/tests/test_websocket.py

@pytest.mark.asyncio
async def test_websocket_sends_status_updates():
    """WebSocket should send status updates during processing"""
    async with websocket_client("/ws/recordings/123") as ws:
        messages = []
        async for msg in ws:
            messages.append(json.loads(msg))
            if msg["status"] == "completed":
                break

        statuses = [m["status"] for m in messages]
        assert "processing" in statuses
        assert "completed" in statuses
```

```typescript
// frontend/tests/ProcessingStatus.test.tsx

describe('ProcessingStatus Component', () => {
  it('should show pending state initially', () => {
    render(<ProcessingStatus recordingId="123" status="pending" />);
    expect(screen.getByText(/waiting/i)).toBeInTheDocument();
  });

  it('should show progress during processing', () => {
    render(<ProcessingStatus recordingId="123" status="processing" progress={45} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '45');
  });

  it('should show completion state', () => {
    render(<ProcessingStatus recordingId="123" status="completed" />);
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });

  it('should show error state with message', () => {
    render(<ProcessingStatus recordingId="123" status="failed" error="Transcription failed" />);
    expect(screen.getByText(/failed/i)).toBeInTheDocument();
    expect(screen.getByText(/transcription failed/i)).toBeInTheDocument();
  });
});
```

---

## Phase 6: Results Display & UI Polish

### Scope
- Results view with summary, actions, transcript
- Recording history list
- Search/filter recordings
- Export functionality (Markdown, JSON)

### Files to Create/Modify

**Backend:**
- `backend/app/api/recordings.py` - List/get endpoints
- `backend/app/services/export.py` - Export service

**Frontend:**
- `frontend/src/components/ResultsView.tsx`
- `frontend/src/components/RecordingList.tsx`
- `frontend/src/components/TranscriptViewer.tsx`
- `frontend/src/components/ActionItems.tsx`

### Test Cases - Phase 6

```python
# backend/tests/test_api_recordings.py

def test_list_recordings_returns_all(client, db_session):
    """Should return all recordings"""
    # Create test recordings
    for i in range(3):
        create_recording(db_session, title=f"Meeting {i}")

    response = client.get("/api/recordings")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_list_recordings_ordered_by_date(client, db_session):
    """Should return recordings newest first"""
    create_recording(db_session, title="Old", created_at=datetime(2024, 1, 1))
    create_recording(db_session, title="New", created_at=datetime(2024, 6, 1))

    response = client.get("/api/recordings")
    titles = [r["title"] for r in response.json()]
    assert titles == ["New", "Old"]

def test_get_recording_with_analysis(client, processed_recording):
    """Should return recording with full analysis"""
    response = client.get(f"/api/recordings/{processed_recording.id}")

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data["analysis"]
    assert "action_items" in data["analysis"]
    assert "transcript" in data

def test_export_recording_markdown(client, processed_recording):
    """Should export recording as Markdown"""
    response = client.get(f"/api/recordings/{processed_recording.id}/export?format=markdown")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown"
    assert "# Meeting Summary" in response.text

def test_export_recording_json(client, processed_recording):
    """Should export recording as JSON"""
    response = client.get(f"/api/recordings/{processed_recording.id}/export?format=json")

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "action_items" in data
```

```typescript
// frontend/tests/ResultsView.test.tsx

describe('ResultsView Component', () => {
  const mockData = {
    summary: 'Discussion about Q1 goals',
    action_items: [
      { speaker: 'Speaker 1', task: 'Send email to client' },
      { speaker: 'Speaker 2', task: 'Create Jira ticket' }
    ],
    decisions: ['Use PostgreSQL'],
    transcript: { segments: [] }
  };

  it('should render summary section', () => {
    render(<ResultsView data={mockData} />);
    expect(screen.getByText(/Q1 goals/)).toBeInTheDocument();
  });

  it('should render action items grouped by speaker', () => {
    render(<ResultsView data={mockData} />);
    expect(screen.getByText('Speaker 1')).toBeInTheDocument();
    expect(screen.getByText(/send email/i)).toBeInTheDocument();
  });

  it('should render decisions section', () => {
    render(<ResultsView data={mockData} />);
    expect(screen.getByText(/postgresql/i)).toBeInTheDocument();
  });

  it('should have working export button', async () => {
    render(<ResultsView data={mockData} recordingId="123" />);
    const exportBtn = screen.getByRole('button', { name: /export/i });
    await userEvent.click(exportBtn);
    expect(screen.getByText(/markdown/i)).toBeInTheDocument();
  });
});


// frontend/tests/RecordingList.test.tsx

describe('RecordingList Component', () => {
  it('should render list of recordings', () => {
    const recordings = [
      { id: '1', title: 'Standup', status: 'completed', created_at: '2024-01-15' },
      { id: '2', title: 'Planning', status: 'processing', created_at: '2024-01-16' }
    ];
    render(<RecordingList recordings={recordings} />);

    expect(screen.getByText('Standup')).toBeInTheDocument();
    expect(screen.getByText('Planning')).toBeInTheDocument();
  });

  it('should show status badge for each recording', () => {
    const recordings = [
      { id: '1', title: 'Test', status: 'completed', created_at: '2024-01-15' }
    ];
    render(<RecordingList recordings={recordings} />);

    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });

  it('should filter recordings by search term', async () => {
    const recordings = [
      { id: '1', title: 'Standup', status: 'completed', created_at: '2024-01-15' },
      { id: '2', title: 'Planning', status: 'completed', created_at: '2024-01-16' }
    ];
    render(<RecordingList recordings={recordings} />);

    const search = screen.getByPlaceholderText(/search/i);
    await userEvent.type(search, 'standup');

    expect(screen.getByText('Standup')).toBeInTheDocument();
    expect(screen.queryByText('Planning')).not.toBeInTheDocument();
  });
});
```

---

## Verification Plan

### Phase 1 Verification
```bash
# Backend
cd backend && pytest tests/test_health.py -v
curl http://localhost:8000/api/health

# Frontend
cd frontend && npm test
npm run dev  # Verify app loads
```

### Phase 2 Verification
```bash
# Test upload via curl
curl -X POST http://localhost:8000/api/recordings/upload \
  -F "file=@test.wav"

# Verify file stored
ls uploads/
```

### Phase 3 Verification
```bash
# Run transcription test
pytest tests/test_transcription.py -v

# Manual test with real audio
curl -X POST http://localhost:8000/api/recordings/upload \
  -F "file=@meeting.mp3"
# Check transcript generated
```

### Phase 4 Verification
```bash
# Ensure Ollama running
ollama run mistral

# Test analysis
pytest tests/test_analyzer.py -v
```

### Phase 5 Verification
```bash
# Full pipeline test
pytest tests/test_pipeline.py -v

# E2E test: upload and wait for completion
curl -X POST .../upload -F "file=@test.wav"
# Poll status until completed
```

### Phase 6 Verification
```bash
# Full E2E flow in browser
npm run dev  # Frontend
uvicorn app.main:app  # Backend

# Upload file via UI
# Verify results display
# Test export functionality
```

---

## Dependencies to Install

### Backend (requirements.txt)
```
fastapi>=0.109.0
uvicorn>=0.27.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
python-multipart>=0.0.6
openai-whisper>=20231117
pydub>=0.25.1
httpx>=0.26.0
websockets>=12.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vitest": "^1.2.0",
    "@testing-library/react": "^14.0.0"
  }
}
```

### System Dependencies
```bash
# FFmpeg for audio processing
sudo apt install ffmpeg  # Linux
brew install ffmpeg      # macOS

# Ollama for local LLM
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral
```

---

## Execution Order

1. **Phase 1** → Verify health endpoint works
2. **Phase 2** → Verify file upload works
3. **Phase 3** → Verify transcription works (need sample audio)
4. **Phase 4** → Verify LLM analysis works (need Ollama running)
5. **Phase 5** → Verify full pipeline works
6. **Phase 6** → Verify UI displays results correctly
