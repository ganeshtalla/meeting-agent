# Models Package (`models/`)

## Overview

This package contains SQLAlchemy ORM model definitions. Models represent database tables and provide an object-oriented interface for database operations.

## Files

| File | Purpose | Phase |
|------|---------|-------|
| `__init__.py` | Package exports for easy imports | All |
| `recording.py` | Recording model for meeting recordings | Phase 1 |
| `transcript.py` | Transcript model for transcription results | Phase 3 |
| `analysis.py` | Analysis model (future) | Phase 4 |

## Model Relationships

```
Recording (1) <---> (1) Transcript
Recording (1) <---> (1) Analysis (Phase 4)
```

## Packages Used

| Package | Component | Purpose |
|---------|-----------|---------|
| `sqlalchemy` | `Column` | Defines table columns |
| `sqlalchemy` | `Integer`, `String`, `Float`, `DateTime`, `Text`, `JSON` | Column data types |
| `sqlalchemy` | `ForeignKey` | Define foreign key relationships |
| `sqlalchemy.orm` | `relationship` | ORM relationship mapping |
| `sqlalchemy.sql` | `func` | SQL functions (e.g., `func.now()`) |

---

## Recording Model (Phase 1-2)

**File:** `recording.py`

Represents a meeting recording in the database.

### Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key, auto-increment |
| `title` | String(255) | Recording title |
| `original_filename` | String(255) | Uploaded file name |
| `file_path` | String(512) | Path to stored file |
| `file_size` | Integer | File size in bytes |
| `mime_type` | String(100) | MIME type (audio/wav, etc.) |
| `duration_seconds` | Integer | Audio duration (nullable) |
| `status` | String(50) | Processing status |
| `error_message` | Text | Error details if failed |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `processed_at` | DateTime | Processing completion time |

### Relationships

| Relationship | Type | Description |
|--------------|------|-------------|
| `transcript` | One-to-One | Related Transcript model |

### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Awaiting processing |
| `processing` | Currently being processed |
| `completed` | Successfully processed |
| `failed` | Processing failed |

### Usage

```python
from app.models import Recording
from app.db import get_db

# Create a new recording
recording = Recording(
    title="Team Standup",
    original_filename="standup.mp3",
    file_path="/uploads/123.mp3",
    file_size=1024000,
    mime_type="audio/mpeg",
    status="pending"
)
db.add(recording)
db.commit()

# Query recordings
recordings = db.query(Recording).filter_by(status="completed").all()

# Access transcript via relationship
if recording.transcript:
    print(recording.transcript.full_text)
```

---

## Transcript Model (Phase 3)

**File:** `transcript.py`

Stores transcription results with full text and timed segments.

### Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key, auto-increment |
| `recording_id` | Integer | Foreign key to recordings table |
| `full_text` | Text | Complete transcript text |
| `segments` | JSON | Array of segments with timing |
| `language` | String(10) | Language code (e.g., 'en', 'es') |
| `duration_seconds` | Float | Audio duration in seconds |
| `word_count` | Integer | Approximate word count |
| `created_at` | DateTime | Creation timestamp |

### Segments JSON Structure

```json
[
    {
        "start": 0.0,
        "end": 2.5,
        "text": "Hello everyone.",
        "speaker": null
    },
    {
        "start": 2.5,
        "end": 5.0,
        "text": "Welcome to the meeting.",
        "speaker": null
    }
]
```

### Relationships

| Relationship | Type | Description |
|--------------|------|-------------|
| `recording` | Many-to-One | Parent Recording model |

### Helper Methods

| Method | Description |
|--------|-------------|
| `calculate_word_count()` | Calculate and set word count from full_text |
| `get_segment_at_time(time)` | Get segment containing the specified time |
| `get_text_between(start, end)` | Get text between two timestamps |

### Usage

```python
from app.models import Recording, Transcript

# Create transcript for a recording
transcript = Transcript(
    recording_id=recording.id,
    full_text="Hello everyone. Welcome to the meeting.",
    segments=[
        {"start": 0.0, "end": 2.5, "text": "Hello everyone."},
        {"start": 2.5, "end": 5.0, "text": "Welcome to the meeting."}
    ],
    language="en",
    duration_seconds=5.0
)
transcript.calculate_word_count()
db.add(transcript)
db.commit()

# Access via relationship
recording = db.query(Recording).get(1)
if recording.transcript:
    print(f"Words: {recording.transcript.word_count}")
    print(f"Language: {recording.transcript.language}")

    # Get segment at specific time
    segment = recording.transcript.get_segment_at_time(1.0)
    print(f"At 1s: {segment['text']}")
```

---

## Database Schema

```sql
-- recordings table
CREATE TABLE recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    duration_seconds INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    processed_at DATETIME
);

-- transcripts table
CREATE TABLE transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id INTEGER NOT NULL,
    full_text TEXT NOT NULL DEFAULT '',
    segments JSON NOT NULL DEFAULT '[]',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    duration_seconds FLOAT,
    word_count INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recording_id) REFERENCES recordings(id) ON DELETE CASCADE
);
```

## Database Migrations

For production, use Alembic for database migrations:

```bash
# Initialize Alembic
alembic init migrations

# Generate migration
alembic revision --autogenerate -m "Add transcript table"

# Apply migrations
alembic upgrade head
```

## Cascade Deletes

When a Recording is deleted, its associated Transcript is automatically deleted due to:
1. `ondelete="CASCADE"` on the foreign key
2. `cascade="all, delete-orphan"` on the relationship
