#!/usr/bin/env python3
"""
End-to-End Test Script for Meeting Agent
=========================================

This script tests the complete pipeline:
1. Upload a recording
2. Start processing
3. Poll for completion
4. Display results

Usage:
    # With default test file
    python test_e2e.py

    # With your own audio file
    python test_e2e.py path/to/audio.wav

    # With a URL to download
    python test_e2e.py --url https://example.com/audio.wav
"""

import sys
import time
import requests
import argparse
from pathlib import Path

BASE_URL = "http://localhost:8000"


def upload_recording(file_path: str) -> dict:
    """Upload a recording file."""
    print(f"\n📤 Uploading: {file_path}")

    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/api/recordings/upload",
            files={"file": (Path(file_path).name, f)}
        )

    if response.status_code != 201:
        print(f"❌ Upload failed: {response.text}")
        sys.exit(1)

    data = response.json()
    print(f"✅ Uploaded! Recording ID: {data['id']}")
    return data


def start_processing(recording_id: int) -> dict:
    """Start processing a recording."""
    print(f"\n🚀 Starting processing for recording {recording_id}...")

    response = requests.post(f"{BASE_URL}/api/recordings/{recording_id}/process")

    if response.status_code != 200:
        print(f"❌ Failed to start processing: {response.text}")
        sys.exit(1)

    print("✅ Processing started!")
    return response.json()


def poll_status(recording_id: int, timeout: int = 300) -> dict:
    """Poll for processing completion."""
    print(f"\n⏳ Waiting for processing to complete (timeout: {timeout}s)...")

    start_time = time.time()
    last_status = None

    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}/api/recordings/{recording_id}")
        data = response.json()
        status = data['status']

        if status != last_status:
            print(f"   Status: {status}")
            last_status = status

        if status == 'completed':
            print("✅ Processing completed!")
            return data
        elif status == 'failed':
            print(f"❌ Processing failed: {data.get('error_message', 'Unknown error')}")
            sys.exit(1)

        time.sleep(2)

    print("❌ Timeout waiting for processing")
    sys.exit(1)


def get_details(recording_id: int) -> dict:
    """Get full recording details with transcript and analysis."""
    response = requests.get(f"{BASE_URL}/api/recordings/{recording_id}/details")
    return response.json()


def display_results(details: dict):
    """Display the processing results."""
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)

    print(f"\n📁 Recording: {details['title']}")
    print(f"   Duration: {details.get('duration_seconds', 'N/A')}s")
    print(f"   Status: {details['status']}")

    if details.get('transcript'):
        transcript = details['transcript']
        print(f"\n📝 TRANSCRIPT (Language: {transcript['language']})")
        print("-" * 40)
        text = transcript['full_text']
        if len(text) > 500:
            print(text[:500] + "...")
        else:
            print(text if text else "(empty - no speech detected)")

        if transcript.get('segments'):
            print(f"\n   Segments: {len(transcript['segments'])}")

    if details.get('analysis'):
        analysis = details['analysis']
        print(f"\n🤖 ANALYSIS (Model: {analysis.get('model_used', 'N/A')})")
        print("-" * 40)

        print(f"\n📋 Summary:")
        print(f"   {analysis['summary']}")

        if analysis.get('action_items'):
            print(f"\n✅ Action Items ({len(analysis['action_items'])}):")
            for item in analysis['action_items']:
                print(f"   • {item.get('speaker', 'Unknown')}: {item.get('task', 'N/A')}")
                if item.get('due_date'):
                    print(f"     Due: {item['due_date']}")

        if analysis.get('decisions'):
            print(f"\n🎯 Decisions ({len(analysis['decisions'])}):")
            for decision in analysis['decisions']:
                print(f"   • {decision}")

        if analysis.get('key_topics'):
            print(f"\n🏷️ Key Topics: {', '.join(analysis['key_topics'])}")
    else:
        print("\n⚠️ No analysis available (Ollama may not be running)")

    print("\n" + "=" * 60)


def download_sample(url: str, dest: str) -> str:
    """Download a sample audio file."""
    print(f"📥 Downloading from {url}...")
    response = requests.get(url, stream=True)

    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"✅ Downloaded to {dest}")
    return dest


def main():
    parser = argparse.ArgumentParser(description="Test the Meeting Agent pipeline")
    parser.add_argument('file', nargs='?', default='test_files/test_tone.wav',
                        help='Path to audio file to test')
    parser.add_argument('--url', help='URL to download audio from')
    args = parser.parse_args()

    # Check server is running
    try:
        requests.get(f"{BASE_URL}/api/health")
    except requests.ConnectionError:
        print("❌ Server not running! Start with:")
        print("   uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    # Get file to test
    if args.url:
        file_path = download_sample(args.url, "test_files/downloaded.wav")
    else:
        file_path = args.file

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        print("\nCreate a test file with:")
        print('   python -c "from pydub import AudioSegment; from pydub.generators import Sine; Sine(440).to_audio_segment(duration=5000).export(\'test.wav\', format=\'wav\')"')
        sys.exit(1)

    # Run the pipeline
    recording = upload_recording(file_path)
    start_processing(recording['id'])
    poll_status(recording['id'])
    details = get_details(recording['id'])
    display_results(details)


if __name__ == "__main__":
    main()
