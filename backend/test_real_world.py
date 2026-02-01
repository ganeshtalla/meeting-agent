#!/usr/bin/env python3
"""
Real-World Meeting Test Script
==============================

This script tests the Meeting Agent pipeline with real meeting recordings.

Usage:
    # Test with a local file
    python test_real_world.py /path/to/meeting.mp4

    # Test with a URL (downloads first)
    python test_real_world.py https://example.com/meeting.mp4

    # Test with sample public meetings
    python test_real_world.py --sample

Output:
    Results are saved to: test_outputs/
    - transcript.txt - Full transcript
    - transcript_segments.json - Timed segments
    - analysis.json - Summary, action items, decisions
    - analysis.md - Formatted Markdown report
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings, setup_logging
from app.db.database import SessionLocal, engine, Base
from app.models.recording import Recording
from app.services.pipeline import ProcessingPipeline
from app.services.transcription import TranscriptionService
from app.services.analyzer import AnalyzerService
from app.services.export import ExportService

# Create output directory
OUTPUT_DIR = Path(__file__).parent / "test_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# -----------------------------------------------------------------------------
# Public Meeting Recording Sources
# -----------------------------------------------------------------------------

PUBLIC_MEETING_SOURCES = """
=== PUBLIC MEETING RECORDING SOURCES ===

1. **Internet Archive - Open Meetings**
   https://archive.org/search?query=meeting+recording
   - City council meetings, board meetings, conferences
   - Free to download, various formats

2. **YouTube - Public Meetings**
   Search: "city council meeting" OR "board meeting recording" OR "zoom meeting recording"
   Use yt-dlp to download: yt-dlp -x --audio-format wav "URL"

3. **C-SPAN - Congressional Hearings**
   https://www.c-span.org/
   - Congressional hearings and public government meetings
   - High quality audio, real discussions

4. **Open States / Government Sites**
   - Many state/local governments post meeting recordings
   - Example: California Legislature: https://www.legislature.ca.gov/

5. **TED Talks / Conference Recordings**
   - Not meetings, but good for testing transcription
   - Clear audio, multiple speakers

6. **Sample Files for Testing (Short)**
   - LibriSpeech dataset: https://www.openslr.org/12/
   - Common Voice: https://commonvoice.mozilla.org/

=== QUICK DOWNLOAD COMMANDS ===

# Using yt-dlp (install: pip install yt-dlp)
yt-dlp -x --audio-format wav -o "meeting.%(ext)s" "YOUTUBE_URL"

# Using wget for direct links
wget -O meeting.mp4 "DIRECT_URL"

# Using curl
curl -L -o meeting.mp4 "DIRECT_URL"
"""


# -----------------------------------------------------------------------------
# Test Functions
# -----------------------------------------------------------------------------

def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL."""
    import subprocess

    print(f"Downloading from: {url}")
    print(f"Saving to: {output_path}")

    try:
        # Try yt-dlp first (for YouTube, etc.)
        if "youtube.com" in url or "youtu.be" in url:
            result = subprocess.run([
                "yt-dlp", "-x", "--audio-format", "wav",
                "-o", str(output_path.with_suffix(".%(ext)s")),
                url
            ], capture_output=True, text=True)
            if result.returncode == 0:
                # Find the downloaded file
                for ext in [".wav", ".mp3", ".m4a"]:
                    check_path = output_path.with_suffix(ext)
                    if check_path.exists():
                        return True

        # Try wget
        result = subprocess.run([
            "wget", "-O", str(output_path), url
        ], capture_output=True, text=True)

        if result.returncode == 0 and output_path.exists():
            return True

        # Try curl
        result = subprocess.run([
            "curl", "-L", "-o", str(output_path), url
        ], capture_output=True, text=True)

        return result.returncode == 0 and output_path.exists()

    except FileNotFoundError as e:
        print(f"Download tool not found: {e}")
        return False


def create_sample_meeting() -> Path:
    """Create a sample meeting audio using text-to-speech."""
    try:
        from gtts import gTTS
        from pydub import AudioSegment
    except ImportError:
        print("Installing gTTS for sample generation...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "gtts", "-q"])
        from gtts import gTTS
        from pydub import AudioSegment

    print("\nGenerating sample meeting audio...")

    # Sample meeting script with multiple speakers
    meeting_script = [
        ("Speaker 1", "Good morning everyone. Let's start our weekly standup meeting."),
        ("Speaker 2", "Thanks for setting this up. I've been working on the user authentication module."),
        ("Speaker 1", "Great. How's the progress on that?"),
        ("Speaker 2", "I should have the PR ready by Friday. I just need to add some unit tests."),
        ("Speaker 1", "Perfect. Make sure to include the edge cases we discussed."),
        ("Speaker 3", "I have a question about the database migration."),
        ("Speaker 1", "Sure, go ahead."),
        ("Speaker 3", "Should we use PostgreSQL or stick with SQLite for the staging environment?"),
        ("Speaker 1", "Good question. Let's decide to use PostgreSQL for staging to match production."),
        ("Speaker 2", "That makes sense. I can update the configuration files."),
        ("Speaker 1", "Great. Can you also send an email to the DevOps team about this change?"),
        ("Speaker 2", "Sure, I'll do that today."),
        ("Speaker 3", "One more thing. We need to schedule the code review for the API endpoints."),
        ("Speaker 1", "Let's do that on Thursday afternoon. Does that work for everyone?"),
        ("Speaker 2", "Works for me."),
        ("Speaker 3", "Same here."),
        ("Speaker 1", "Alright, let's wrap up. Action items: Speaker 2 will finish the auth PR by Friday and email DevOps. We'll do the code review on Thursday. Any questions?"),
        ("Speaker 2", "No questions from me."),
        ("Speaker 3", "All clear."),
        ("Speaker 1", "Great meeting everyone. Talk to you later."),
    ]

    # Generate audio for each line
    audio_segments = []
    temp_dir = OUTPUT_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)

    for i, (speaker, text) in enumerate(meeting_script):
        print(f"  Generating: {speaker} - {text[:50]}...")
        temp_file = temp_dir / f"segment_{i}.mp3"

        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(str(temp_file))

        segment = AudioSegment.from_mp3(temp_file)
        # Add a short pause between speakers
        pause = AudioSegment.silent(duration=500)
        audio_segments.append(segment + pause)

    # Combine all segments
    full_audio = sum(audio_segments)

    # Export as WAV
    output_path = OUTPUT_DIR / "sample_meeting.wav"
    full_audio.export(output_path, format="wav")

    # Cleanup temp files
    for f in temp_dir.glob("*.mp3"):
        f.unlink()
    temp_dir.rmdir()

    print(f"Sample meeting saved to: {output_path}")
    print(f"Duration: {len(full_audio) / 1000:.1f} seconds")

    return output_path


def process_recording(file_path: Path, transcription_provider: str = None, llm_provider: str = None) -> dict:
    """Process a recording through the full pipeline."""

    print(f"\n{'='*60}")
    print(f"PROCESSING: {file_path.name}")
    print(f"{'='*60}\n")

    # Initialize database
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Create recording entry
        recording = Recording(
            title=file_path.stem,
            original_filename=file_path.name,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            mime_type="audio/wav" if file_path.suffix == ".wav" else "video/mp4",
            status="pending"
        )
        db.add(recording)
        db.commit()
        db.refresh(recording)

        print(f"Recording ID: {recording.id}")
        print(f"File size: {recording.file_size / 1024 / 1024:.2f} MB")

        # Create services with specified providers
        transcription_service = TranscriptionService(provider=transcription_provider) if transcription_provider else None
        analyzer_service = AnalyzerService(provider=llm_provider) if llm_provider else None

        # Create pipeline and process
        pipeline = ProcessingPipeline(
            db=db,
            transcription_service=transcription_service,
            analyzer_service=analyzer_service
        )

        # Track status updates
        statuses = []
        def status_callback(status):
            statuses.append(status)
            print(f"  [{status.stage.value}] {status.progress}% - {status.message}")

        start_time = time.time()
        result = pipeline.process(recording_id=recording.id, callback=status_callback)
        elapsed = time.time() - start_time

        print(f"\nProcessing completed in {elapsed:.1f} seconds")

        # Refresh to get related objects
        db.refresh(recording)

        # Collect results
        output = {
            "success": result.success,
            "recording_id": recording.id,
            "duration_seconds": result.duration_seconds,
            "file": str(file_path),
            "transcript": None,
            "analysis": None,
            "error": result.error_message
        }

        if recording.transcript:
            # Check if transcript has speaker info
            segments = recording.transcript.segments or []
            has_speakers = any(seg.get("speaker") for seg in segments if isinstance(seg, dict))

            output["transcript"] = {
                "full_text": recording.transcript.full_text,
                "segments": segments,
                "language": recording.transcript.language,
                "word_count": len(recording.transcript.full_text.split()),
                "has_speakers": has_speakers,
                "speaker_count": len(set(seg.get("speaker") for seg in segments if isinstance(seg, dict) and seg.get("speaker")))
            }

        if recording.analysis:
            output["analysis"] = {
                "summary": recording.analysis.summary,
                "action_items": recording.analysis.action_items,
                "decisions": recording.analysis.decisions,
                "key_topics": recording.analysis.key_topics,
                "model_used": recording.analysis.model_used
            }

        return output

    finally:
        db.close()


def save_outputs(results: dict, output_name: str):
    """Save processing results to files."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_subdir = OUTPUT_DIR / f"{output_name}_{timestamp}"
    output_subdir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"SAVING OUTPUTS TO: {output_subdir}")
    print(f"{'='*60}\n")

    # Save full results as JSON
    results_file = output_subdir / "full_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Full results: {results_file}")

    # Save transcript text
    if results.get("transcript"):
        transcript = results["transcript"]

        # Plain text
        txt_file = output_subdir / "transcript.txt"
        with open(txt_file, "w") as f:
            f.write(transcript["full_text"])
        print(f"Transcript text: {txt_file}")

        # Segments with timestamps
        segments_file = output_subdir / "transcript_segments.json"
        with open(segments_file, "w") as f:
            json.dump(transcript["segments"], f, indent=2)
        print(f"Transcript segments: {segments_file}")

    # Save analysis
    if results.get("analysis"):
        analysis = results["analysis"]

        # JSON format
        analysis_file = output_subdir / "analysis.json"
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)
        print(f"Analysis JSON: {analysis_file}")

        # Markdown format
        md_file = output_subdir / "analysis.md"
        with open(md_file, "w") as f:
            f.write(f"# Meeting Analysis\n\n")
            f.write(f"**Model Used:** {analysis.get('model_used', 'Unknown')}\n\n")

            f.write(f"## Summary\n\n{analysis.get('summary', 'No summary')}\n\n")

            f.write(f"## Action Items\n\n")
            action_items = analysis.get("action_items", [])
            if action_items:
                for item in action_items:
                    speaker = item.get("speaker", "Unknown")
                    task = item.get("task", "")
                    due = item.get("due_date", "")
                    due_str = f" *(Due: {due})*" if due else ""
                    f.write(f"- [ ] **{speaker}**: {task}{due_str}\n")
            else:
                f.write("No action items identified.\n")
            f.write("\n")

            f.write(f"## Decisions\n\n")
            decisions = analysis.get("decisions", [])
            if decisions:
                for d in decisions:
                    f.write(f"- {d}\n")
            else:
                f.write("No decisions identified.\n")
            f.write("\n")

            f.write(f"## Key Topics\n\n")
            topics = analysis.get("key_topics", [])
            if topics:
                for t in topics:
                    f.write(f"- {t}\n")
            else:
                f.write("No key topics identified.\n")

        print(f"Analysis Markdown: {md_file}")

    print(f"\nAll outputs saved to: {output_subdir}")
    return output_subdir


def print_summary(results: dict):
    """Print a summary of the results."""

    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}\n")

    if not results["success"]:
        print(f"ERROR: {results.get('error', 'Unknown error')}")
        return

    print(f"Processing Time: {results['duration_seconds']:.1f} seconds")

    if results.get("transcript"):
        t = results["transcript"]
        print(f"\nTRANSCRIPT:")
        print(f"  - Word count: {t['word_count']}")
        print(f"  - Language: {t['language']}")
        print(f"  - Segments: {len(t['segments'])}")
        if t.get('has_speakers'):
            print(f"  - Speakers detected: {t['speaker_count']}")
        else:
            print(f"  - Speakers: Not available (use --transcription whisper-diarize or assemblyai for speaker labels)")
        print(f"\n  Preview (first 500 chars):")
        print(f"  {'-'*50}")
        print(f"  {t['full_text'][:500]}...")

    if results.get("analysis"):
        a = results["analysis"]
        print(f"\nANALYSIS (using {a.get('model_used', 'unknown model')}):")
        print(f"\n  SUMMARY:")
        print(f"  {a.get('summary', 'No summary')}")

        print(f"\n  ACTION ITEMS ({len(a.get('action_items', []))}):")
        for item in a.get("action_items", []):
            speaker = item.get("speaker", "Unknown")
            task = item.get("task", "")
            due = item.get("due_date", "")
            print(f"    - [{speaker}] {task}" + (f" (due: {due})" if due else ""))

        print(f"\n  DECISIONS ({len(a.get('decisions', []))}):")
        for d in a.get("decisions", []):
            print(f"    - {d}")

        print(f"\n  KEY TOPICS ({len(a.get('key_topics', []))}):")
        for t in a.get("key_topics", []):
            print(f"    - {t}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Test Meeting Agent with real-world recordings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=PUBLIC_MEETING_SOURCES
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to audio/video file or URL"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Generate and process a sample meeting"
    )
    parser.add_argument(
        "--sources",
        action="store_true",
        help="Show public meeting recording sources"
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "openai", "anthropic"],
        help="LLM provider to use (overrides config)"
    )
    parser.add_argument(
        "--transcription",
        choices=["whisper", "whisper-diarize", "assemblyai"],
        default="whisper-diarize",
        help="Transcription provider: whisper (local, no speakers), whisper-diarize (local, with speakers), or assemblyai (cloud, with speakers)"
    )

    args = parser.parse_args()

    # Show sources
    if args.sources:
        print(PUBLIC_MEETING_SOURCES)
        return

    # Validate input
    if not args.input and not args.sample:
        parser.print_help()
        print("\n" + "="*60)
        print("QUICK START:")
        print("="*60)
        print("\n1. Generate and test with sample meeting:")
        print("   python test_real_world.py --sample")
        print("\n2. Test with your own file:")
        print("   python test_real_world.py /path/to/meeting.mp4")
        print("\n3. See public recording sources:")
        print("   python test_real_world.py --sources")
        return

    # Show selected providers
    if args.provider:
        print(f"Using LLM provider: {args.provider}")
    if args.transcription:
        print(f"Using transcription provider: {args.transcription}")
        if args.transcription == "assemblyai":
            if not os.getenv("ASSEMBLYAI_API_KEY"):
                print("\nWARNING: ASSEMBLYAI_API_KEY not set!")
                print("Set it with: export ASSEMBLYAI_API_KEY=your-api-key")
                print("Get a free API key at: https://www.assemblyai.com/")
                return

    # Get input file
    if args.sample:
        file_path = create_sample_meeting()
    elif args.input.startswith("http"):
        # Download from URL
        file_path = OUTPUT_DIR / "downloaded_meeting.mp4"
        if not download_file(args.input, file_path):
            print("Failed to download file")
            return
    else:
        file_path = Path(args.input)
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return

    # Process the recording
    results = process_recording(
        file_path,
        transcription_provider=args.transcription,
        llm_provider=args.provider
    )

    # Print summary
    print_summary(results)

    # Save outputs
    output_dir = save_outputs(results, file_path.stem)

    print(f"\n{'='*60}")
    print("DONE!")
    print(f"{'='*60}")
    print(f"\nView results in: {output_dir}")
    print(f"  - analysis.md    : Formatted report")
    print(f"  - analysis.json  : Structured data")
    print(f"  - transcript.txt : Full transcript")


if __name__ == "__main__":
    main()
