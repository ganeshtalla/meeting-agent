# Schemas Package (`schemas/`)

## Overview

This package contains Pydantic schema definitions for request/response validation and serialization. Schemas define the structure of data exchanged via the API.

## Files

| File | Purpose | Phase |
|------|---------|-------|
| `__init__.py` | Package exports for easy imports | All |
| `recording.py` | Schemas for recording endpoints | Phase 1-2 |
| `transcript.py` | Schemas for transcript data | Phase 3 |
| `analysis.py` | Schemas for analysis results (future) | Phase 4 |

## Packages Used

| Package | Component | Purpose |
|---------|-----------|---------|
| `pydantic` | `BaseModel` | Base class for all schemas |
| `pydantic` | `ConfigDict` | Schema configuration |
| `pydantic` | `Field` | Field metadata and validation |
| `datetime` | `datetime` | Datetime type hints |
| `typing` | `Optional`, `List` | Type hints |

## Key Concepts

### Schema vs Model

- **SQLAlchemy Model**: Represents database tables (internal)
- **Pydantic Schema**: Represents API request/response format (external)

This separation allows:
1. Different validation rules for input vs output
2. Hiding internal fields from API responses
3. Transforming data between layers

## Schema Types

| Type | Purpose | Example |
|------|---------|---------|
| **Base** | Common fields shared by create/response | `RecordingBase` |
| **Create** | Fields for creating resources (input) | `RecordingCreate` |
| **Response** | Full resource data (output) | `RecordingResponse` |
| **List** | Multiple items with pagination | `RecordingList` |
| **Summary** | Minimal info for listings | `TranscriptSummary` |

---

## Recording Schemas (Phase 1-2)

**File:** `recording.py`

| Schema | Purpose |
|--------|---------|
| `RecordingBase` | Common fields (title) |
| `RecordingCreate` | Create request (extends Base) |
| `RecordingResponse` | API response with all fields |
| `RecordingList` | List response with total count |

### RecordingResponse Fields

```python
class RecordingResponse:
    id: int
    title: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    duration_seconds: Optional[int]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    processed_at: Optional[datetime]
```

---

## Transcript Schemas (Phase 3)

**File:** `transcript.py`

| Schema | Purpose |
|--------|---------|
| `TranscriptSegment` | Single segment with timing |
| `TranscriptBase` | Common transcript fields |
| `TranscriptCreate` | Create request with recording_id |
| `TranscriptResponse` | Full transcript response |
| `TranscriptSummary` | Minimal info for listings |

### TranscriptSegment

```python
class TranscriptSegment:
    start: float      # Start time in seconds (>= 0)
    end: float        # End time in seconds (>= 0)
    text: str         # Transcribed text
    speaker: Optional[str]  # Speaker identifier
```

### TranscriptResponse Fields

```python
class TranscriptResponse:
    id: int
    recording_id: int
    full_text: str
    segments: List[TranscriptSegment]
    language: str
    duration_seconds: Optional[float]
    word_count: Optional[int]
    created_at: datetime
```

### Usage

```python
from app.schemas import TranscriptResponse, TranscriptSegment

# In API endpoint
@router.get("/recordings/{id}/transcript", response_model=TranscriptResponse)
def get_transcript(id: int, db: Session = Depends(get_db)):
    recording = db.query(Recording).get(id)
    return recording.transcript

# Creating segments
segment = TranscriptSegment(
    start=0.0,
    end=2.5,
    text="Hello everyone.",
    speaker="Speaker 1"
)
```

---

## Configuration

### `from_attributes = True` (Pydantic v2)

Enables conversion from SQLAlchemy models:

```python
from pydantic import ConfigDict

class RecordingResponse(BaseModel):
    id: int
    title: str
    # ... fields

    model_config = ConfigDict(from_attributes=True)
```

This allows:
```python
# Convert SQLAlchemy model to Pydantic schema
recording_model = db.query(Recording).first()
response = RecordingResponse.model_validate(recording_model)
```

## Validation Examples

### Field Validation

```python
from pydantic import Field

class TranscriptSegment(BaseModel):
    start: float = Field(..., ge=0, description="Start time in seconds")
    end: float = Field(..., ge=0, description="End time in seconds")
    text: str = Field(..., description="Transcribed text")
```

### Custom Validators

```python
from pydantic import field_validator

class RecordingCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
```

## API Usage

```python
from fastapi import FastAPI
from app.schemas import RecordingResponse, TranscriptResponse

app = FastAPI()

# Automatic validation and serialization
@app.get("/recordings/{id}", response_model=RecordingResponse)
def get_recording(id: int, db: Session = Depends(get_db)):
    recording = db.query(Recording).get(id)
    # FastAPI automatically converts to RecordingResponse
    return recording

@app.get("/recordings/{id}/transcript", response_model=TranscriptResponse)
def get_transcript(id: int, db: Session = Depends(get_db)):
    recording = db.query(Recording).get(id)
    return recording.transcript
```
