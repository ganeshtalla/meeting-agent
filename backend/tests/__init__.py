"""
Meeting Agent - Tests Package
=============================

This package contains all test suites for the Meeting Agent backend.

Test Organization:
    - conftest.py: Shared fixtures for all tests
    - test_health.py: Health check endpoint tests
    - test_upload.py: File upload tests (Phase 2+)
    - test_transcription.py: Transcription tests (Phase 3+)
    - test_analyzer.py: LLM analysis tests (Phase 4+)
    - test_pipeline.py: Pipeline integration tests (Phase 5+)
    - fixtures/: Test data files (audio, video samples)

Running Tests:
    # From backend directory
    pytest                    # Run all tests
    pytest -v                 # Verbose output
    pytest tests/test_health.py  # Run specific file
    pytest --cov=app          # With coverage

Test Database:
    Tests use an in-memory SQLite database that is created fresh
    for each test function and cleaned up afterward.
"""
