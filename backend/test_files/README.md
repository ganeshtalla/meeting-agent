# Test Files & Datasets

## Quick Test

```bash
# Start server
uvicorn app.main:app --reload --port 8000

# Run end-to-end test
python test_e2e.py
```

## Open Source Audio Datasets

### 1. LibriSpeech (Recommended for Testing)
Clean audiobook recordings, good for testing transcription accuracy.

```bash
# Download a small sample (14 MB)
wget https://www.openslr.org/resources/12/dev-clean.tar.gz
tar -xzf dev-clean.tar.gz

# Test with a file
python test_e2e.py LibriSpeech/dev-clean/1272/128104/1272-128104-0000.flac
```

### 2. Mozilla Common Voice
Multi-language speech dataset with short clips.

```bash
# Download from: https://commonvoice.mozilla.org/en/datasets
# Select a language and download the "clips" subset
```

### 3. AMI Meeting Corpus (Best for Meeting Testing)
Real meeting recordings with multiple speakers. Perfect for testing action item extraction.

**Download:** http://groups.inf.ed.ac.uk/ami/download/

```bash
# Example file structure after download:
# AMI/audio/ES2002a/ES2002a.Mix-Headset.wav
python test_e2e.py AMI/audio/ES2002a/ES2002a.Mix-Headset.wav
```

### 4. ICSI Meeting Corpus
Natural meeting recordings from UC Berkeley.

**Info:** https://catalog.ldc.upenn.edu/LDC2004S02

### 5. VoxForge
Free speech corpus, community contributed.

```bash
# Download from: http://www.voxforge.org/home/downloads
```

## Sample Meeting-Like Audio (Quick Test)

Create a synthetic "meeting" for testing:

```python
# generate_meeting.py
from gtts import gTTS
import os

# Simulate a short meeting
meeting_script = """
Hello everyone, let's begin the meeting.
John, can you give us an update on the project?
Sure, I'll have the report ready by Friday.
Great. We've decided to use the new database.
Sarah, please send the client an email today.
Meeting adjourned.
"""

tts = gTTS(text=meeting_script, lang='en')
tts.save("test_files/sample_meeting.mp3")
print("Created: test_files/sample_meeting.mp3")
```

```bash
# Install gTTS first
pip install gTTS

# Generate and test
python generate_meeting.py
python test_e2e.py test_files/sample_meeting.mp3
```

## Using YouTube Audio (for testing only)

```bash
# Install yt-dlp
pip install yt-dlp

# Download audio from a public meeting/podcast
yt-dlp -x --audio-format wav -o "test_files/%(title)s.%(ext)s" "VIDEO_URL"

# Test
python test_e2e.py "test_files/video_title.wav"
```

## Test with curl (Manual)

```bash
# 1. Upload
curl -X POST http://localhost:8000/api/recordings/upload \
  -F "file=@test_files/sample.wav" | jq

# 2. Process (use the ID from step 1)
curl -X POST http://localhost:8000/api/recordings/1/process | jq

# 3. Check status
curl http://localhost:8000/api/recordings/1 | jq

# 4. Get full results
curl http://localhost:8000/api/recordings/1/details | jq
```
