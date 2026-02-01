"""
Meeting Agent - Application Configuration
==========================================

This module defines all application settings using Pydantic Settings.
Settings can be configured via environment variables or a .env file.

Packages Used:
    - pydantic_settings: Settings management with validation
        - BaseSettings: Base class for settings with env var support
        - SettingsConfigDict: Configuration for settings behavior
    - pathlib: Object-oriented filesystem paths
        - Path: Cross-platform path handling

Key Components:
    - Settings: Configuration class with all app settings
    - settings: Singleton instance for global access

Environment Variables:
    All settings can be overridden via environment variables.
    Variable names are case-insensitive (e.g., DATABASE_URL or database_url).

Usage:
    from app.config import settings
    print(settings.database_url)
    print(settings.cors_origins)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings have default values but can be overridden via:
    1. Environment variables
    2. A .env file in the backend directory

    Attributes:
        database_url (str): SQLite database connection string
        upload_dir (Path): Directory for uploaded files
        processed_dir (Path): Directory for processed audio files
        max_file_size_mb (int): Maximum upload file size in megabytes
        cors_origins (list[str]): Allowed frontend origins for CORS
        ollama_base_url (str): Ollama API base URL
        ollama_model (str): LLM model name for analysis
        whisper_model (str): Whisper model size for transcription
    """

    # -------------------------------------------------------------------------
    # Pydantic Settings Configuration
    # -------------------------------------------------------------------------
    # model_config replaces the deprecated inner Config class
    # - env_file: Path to .env file for loading environment variables
    # - env_file_encoding: Character encoding for .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # -------------------------------------------------------------------------
    # Database Configuration
    # -------------------------------------------------------------------------
    # SQLite database URL. For production, consider PostgreSQL.
    # Format: sqlite:///./filename.db (relative) or sqlite:////absolute/path.db
    database_url: str = "sqlite:///./meeting_agent.db"

    # -------------------------------------------------------------------------
    # File Storage Configuration
    # -------------------------------------------------------------------------
    # Directories for storing uploaded and processed files
    upload_dir: Path = Path("uploads")      # Raw uploaded recordings
    processed_dir: Path = Path("processed")  # Extracted/converted audio
    max_file_size_mb: int = 500             # Max upload size (500MB default)

    # -------------------------------------------------------------------------
    # CORS Configuration
    # -------------------------------------------------------------------------
    # List of allowed origins for Cross-Origin Resource Sharing.
    # The frontend development server runs on port 5173 by default.
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # -------------------------------------------------------------------------
    # LLM Provider Configuration
    # -------------------------------------------------------------------------
    # Supported providers: "ollama", "openai", "anthropic"
    llm_provider: str = "ollama"

    # -------------------------------------------------------------------------
    # Ollama Configuration (local LLM)
    # -------------------------------------------------------------------------
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # -------------------------------------------------------------------------
    # OpenAI Configuration
    # -------------------------------------------------------------------------
    openai_api_key: str = ""  # Set via OPENAI_API_KEY env var
    openai_model: str = "gpt-4o-mini"  # Options: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
    openai_base_url: str = "https://api.openai.com/v1"  # Can override for Azure/proxies

    # -------------------------------------------------------------------------
    # Anthropic (Claude) Configuration
    # -------------------------------------------------------------------------
    anthropic_api_key: str = ""  # Set via ANTHROPIC_API_KEY env var
    anthropic_model: str = "claude-sonnet-4-20250514"  # Options: claude-sonnet-4-20250514, claude-3-5-haiku-20241022, claude-3-opus-20240229

    # -------------------------------------------------------------------------
    # LLM General Settings
    # -------------------------------------------------------------------------
    llm_timeout: int = 120  # Request timeout in seconds
    llm_temperature: float = 0.3  # Lower = more focused output

    # -------------------------------------------------------------------------
    # Transcription Configuration
    # -------------------------------------------------------------------------
    # Provider: "whisper" (local, no speakers), "whisper-diarize" (local, with speakers),
    #           or "assemblyai" (cloud, with speakers)
    transcription_provider: str = "whisper-diarize"

    # Whisper settings (local transcription)
    # Available models: tiny, base, small, medium, large
    whisper_model: str = "base"

    # AssemblyAI settings (cloud transcription with speaker diarization)
    assemblyai_api_key: str = ""  # Set via ASSEMBLYAI_API_KEY env var

    # -------------------------------------------------------------------------
    # Logging Configuration
    # -------------------------------------------------------------------------
    # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_level: str = "INFO"


# -----------------------------------------------------------------------------
# Global Settings Instance
# -----------------------------------------------------------------------------
# Create a singleton instance for use throughout the application.
# This instance loads settings from environment variables and .env file.
settings = Settings()


# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------
import logging
import sys

def setup_logging():
    """Configure application-wide logging."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Get log level from settings
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set specific loggers
    logging.getLogger("app").setLevel(level)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {settings.log_level} level")

# Initialize logging on import
setup_logging()
