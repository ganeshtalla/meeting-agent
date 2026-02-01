"""
Meeting Agent - LLM Analysis Service
=====================================

This module provides meeting analysis capabilities using multiple LLM providers:
- Ollama (local)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)

The provider is configurable via the LLM_PROVIDER environment variable.

Packages Used:
    - httpx: HTTP client for Ollama API
    - openai: OpenAI Python SDK (optional)
    - anthropic: Anthropic Python SDK (optional)
    - json: JSON parsing for structured output
    - logging: Standard logging for error tracking
    - dataclasses: Data classes for structured results

Key Components:
    - AnalyzerService: Main service class (factory pattern)
    - LLMProvider: Base class for LLM providers
    - OllamaProvider: Local Ollama provider
    - OpenAIProvider: OpenAI API provider
    - AnthropicProvider: Anthropic Claude provider

Usage:
    from app.services.analyzer import AnalyzerService

    # Uses provider from settings (LLM_PROVIDER env var)
    analyzer = AnalyzerService()

    # Or specify provider explicitly
    analyzer = AnalyzerService(provider="openai")

    if analyzer.is_available():
        result = analyzer.analyze(transcript_text)
        if result.success:
            print(f"Summary: {result.summary}")
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List

import httpx

from app.config import settings

# Configure logging for this module
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Result Data Classes
# -----------------------------------------------------------------------------

@dataclass
class ActionItem:
    """
    A single action item extracted from the meeting.

    Attributes:
        speaker (str): Speaker assigned to this action
        task (str): Description of the task/action
        due_date (str): Optional due date mentioned
        priority (str): Optional priority level (high, medium, low)
    """
    speaker: str
    task: str
    due_date: Optional[str] = None
    priority: Optional[str] = None


@dataclass
class AnalysisResult:
    """
    Complete result of meeting analysis.

    Attributes:
        success (bool): Whether analysis completed successfully
        summary (str): Concise summary of the meeting
        action_items (List[ActionItem]): List of action items with attribution
        decisions (List[str]): Key decisions made during the meeting
        key_topics (List[str]): Main topics discussed
        error_message (str): Error description if analysis failed
        provider (str): Which LLM provider was used
        model (str): Which model was used
    """
    success: bool
    summary: str = ""
    action_items: List[ActionItem] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    key_topics: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


# -----------------------------------------------------------------------------
# Custom Exceptions
# -----------------------------------------------------------------------------

class ServiceUnavailableError(Exception):
    """Raised when LLM service is not available."""
    pass


class AnalysisTimeoutError(Exception):
    """Raised when analysis takes too long."""
    pass


# -----------------------------------------------------------------------------
# Analysis Prompt (shared across providers)
# -----------------------------------------------------------------------------

ANALYSIS_PROMPT = """Analyze the following meeting transcript and extract key information.

TRANSCRIPT:
{transcript}

---

Please provide your analysis in the following JSON format (and ONLY JSON, no other text):

{{
    "summary": "A concise 2-3 sentence summary of the meeting",
    "action_items": [
        {{
            "speaker": "Name of person assigned",
            "task": "Description of the action item",
            "due_date": "Due date if mentioned, or null"
        }}
    ],
    "decisions": [
        "Decision 1 that was made",
        "Decision 2 that was made"
    ],
    "key_topics": [
        "Topic 1 discussed",
        "Topic 2 discussed"
    ]
}}

Important:
- Extract ALL action items mentioned (tasks assigned to people)
- Include speaker names exactly as they appear in the transcript
- If no action items, return an empty array
- If no decisions, return an empty array
- Keep the summary concise but informative
- Return ONLY valid JSON, no markdown or explanation"""


# -----------------------------------------------------------------------------
# Base LLM Provider
# -----------------------------------------------------------------------------

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Model being used."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response from the LLM."""
        pass


# -----------------------------------------------------------------------------
# Ollama Provider (Local)
# -----------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.base_url = base_url or settings.ollama_base_url
        self._model = model or settings.ollama_model
        self.timeout = timeout or settings.llm_timeout

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                    return self._model in models
                return False
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def list_models(self) -> List[str]:
        """List available models in Ollama."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m.get("name", "") for m in data.get("models", [])]
                return []
        except Exception:
            return []

    def generate(self, prompt: str) -> str:
        """Generate response using Ollama."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self._model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": settings.llm_temperature,
                            "num_predict": 2000,
                        }
                    }
                )

                if response.status_code != 200:
                    raise ServiceUnavailableError(
                        f"Ollama returned status {response.status_code}: {response.text}"
                    )

                data = response.json()
                return data.get("response", "")

        except httpx.TimeoutException:
            raise AnalysisTimeoutError(f"Analysis timed out after {self.timeout} seconds")
        except httpx.ConnectError:
            raise ServiceUnavailableError("Cannot connect to Ollama. Is it running? Try: ollama serve")


# -----------------------------------------------------------------------------
# OpenAI Provider
# -----------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.api_key = api_key or settings.openai_api_key
        self._model = model or settings.openai_model
        self.base_url = base_url or settings.openai_base_url
        self.timeout = timeout or settings.llm_timeout
        self._client = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout
                )
            except ImportError:
                raise ServiceUnavailableError(
                    "OpenAI package not installed. Run: pip install openai"
                )
        return self._client

    def is_available(self) -> bool:
        """Check if OpenAI API is configured and accessible."""
        if not self.api_key:
            logger.debug("OpenAI API key not configured")
            return False

        try:
            client = self._get_client()
            # Make a simple API call to verify credentials
            client.models.list()
            return True
        except Exception as e:
            logger.debug(f"OpenAI not available: {e}")
            return False

    def generate(self, prompt: str) -> str:
        """Generate response using OpenAI."""
        if not self.api_key:
            raise ServiceUnavailableError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meeting analyst. Extract structured information from meeting transcripts. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.llm_temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content or ""

        except ImportError:
            raise ServiceUnavailableError("OpenAI package not installed. Run: pip install openai")
        except Exception as e:
            if "timeout" in str(e).lower():
                raise AnalysisTimeoutError(f"Analysis timed out after {self.timeout} seconds")
            raise ServiceUnavailableError(f"OpenAI API error: {e}")


# -----------------------------------------------------------------------------
# Anthropic (Claude) Provider
# -----------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.api_key = api_key or settings.anthropic_api_key
        self._model = model or settings.anthropic_model
        self.timeout = timeout or settings.llm_timeout
        self._client = None

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(
                    api_key=self.api_key,
                    timeout=self.timeout
                )
            except ImportError:
                raise ServiceUnavailableError(
                    "Anthropic package not installed. Run: pip install anthropic"
                )
        return self._client

    def is_available(self) -> bool:
        """Check if Anthropic API is configured."""
        if not self.api_key:
            logger.debug("Anthropic API key not configured")
            return False

        # Just check if API key is set - don't make API call to save costs
        return True

    def generate(self, prompt: str) -> str:
        """Generate response using Anthropic Claude."""
        if not self.api_key:
            raise ServiceUnavailableError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable."
            )

        try:
            client = self._get_client()
            response = client.messages.create(
                model=self._model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system="You are a meeting analyst. Extract structured information from meeting transcripts. Always respond with valid JSON only.",
                temperature=settings.llm_temperature
            )
            # Extract text from content blocks
            text_content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    text_content += block.text
            return text_content

        except ImportError:
            raise ServiceUnavailableError("Anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            if "timeout" in str(e).lower():
                raise AnalysisTimeoutError(f"Analysis timed out after {self.timeout} seconds")
            raise ServiceUnavailableError(f"Anthropic API error: {e}")


# -----------------------------------------------------------------------------
# Provider Factory
# -----------------------------------------------------------------------------

def get_provider(
    provider: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Factory function to create an LLM provider.

    Args:
        provider: Provider name ("ollama", "openai", "anthropic")
        **kwargs: Additional arguments passed to provider constructor

    Returns:
        LLMProvider: Configured provider instance
    """
    provider_name = (provider or settings.llm_provider).lower()

    if provider_name == "ollama":
        return OllamaProvider(**kwargs)
    elif provider_name == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_name == "anthropic":
        return AnthropicProvider(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider_name}. Use 'ollama', 'openai', or 'anthropic'")


# -----------------------------------------------------------------------------
# Analyzer Service Class
# -----------------------------------------------------------------------------

class AnalyzerService:
    """
    Service for analyzing meeting transcripts using configurable LLM providers.

    This service handles:
    - Provider selection (Ollama, OpenAI, Anthropic)
    - Sending prompts for analysis
    - Parsing structured output
    - Error handling and retries

    Example:
        # Use default provider from settings
        analyzer = AnalyzerService()

        # Use specific provider
        analyzer = AnalyzerService(provider="openai")

        # Use with custom model
        analyzer = AnalyzerService(provider="openai", model="gpt-4o")

        if analyzer.is_available():
            result = analyzer.analyze(transcript)
            print(result.summary)
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the analyzer service.

        Args:
            provider: LLM provider ("ollama", "openai", "anthropic")
            model: Model name (provider-specific)
            **kwargs: Additional provider-specific arguments
        """
        if model:
            kwargs["model"] = model

        self._provider = get_provider(provider, **kwargs)
        logger.info(f"AnalyzerService initialized with {self._provider.name}/{self._provider.model}")

    @property
    def provider_name(self) -> str:
        """Get the current provider name."""
        return self._provider.name

    @property
    def model(self) -> str:
        """Get the current model name."""
        return self._provider.model

    # For backwards compatibility
    @property
    def base_url(self) -> str:
        """Get base URL (Ollama only)."""
        if isinstance(self._provider, OllamaProvider):
            return self._provider.base_url
        return ""

    def is_available(self) -> bool:
        """
        Check if the LLM service is available.

        Returns:
            bool: True if the provider is accessible
        """
        return self._provider.is_available()

    def list_models(self) -> List[str]:
        """
        List available models (Ollama only).

        Returns:
            List[str]: List of model names
        """
        if isinstance(self._provider, OllamaProvider):
            return self._provider.list_models()
        return [self._provider.model]

    # -------------------------------------------------------------------------
    # Response Parsing
    # -------------------------------------------------------------------------

    def _parse_response(self, response_text: str) -> AnalysisResult:
        """
        Parse the LLM response into structured data.

        Args:
            response_text: Raw response from LLM

        Returns:
            AnalysisResult: Parsed analysis result
        """
        try:
            # Try to extract JSON from the response
            json_text = response_text.strip()

            # Remove markdown code blocks if present
            if json_text.startswith("```"):
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", json_text, re.DOTALL)
                if match:
                    json_text = match.group(1)
                else:
                    start = json_text.find("{")
                    end = json_text.rfind("}") + 1
                    if start >= 0 and end > start:
                        json_text = json_text[start:end]

            # Parse JSON
            data = json.loads(json_text)

            # Extract action items
            action_items = []
            for item in data.get("action_items", []):
                if isinstance(item, dict) and item.get("task"):
                    action_items.append(ActionItem(
                        speaker=item.get("speaker", "Unknown"),
                        task=item.get("task", ""),
                        due_date=item.get("due_date"),
                        priority=item.get("priority")
                    ))

            return AnalysisResult(
                success=True,
                summary=data.get("summary", ""),
                action_items=action_items,
                decisions=data.get("decisions", []),
                key_topics=data.get("key_topics", []),
                provider=self._provider.name,
                model=self._provider.model
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return self._parse_freeform_response(response_text)

    def _parse_freeform_response(self, text: str) -> AnalysisResult:
        """
        Attempt to parse a freeform (non-JSON) response.

        Args:
            text: Raw response text

        Returns:
            AnalysisResult: Best-effort parsed result
        """
        lines = text.strip().split("\n")
        summary = ""
        for line in lines:
            line = line.strip()
            if line and not line.startswith(("-", "*", "#", "{")):
                summary = line
                break

        return AnalysisResult(
            success=True,
            summary=summary or "Analysis completed but structured data could not be extracted.",
            action_items=[],
            decisions=[],
            key_topics=[],
            error_message="Response was not in expected JSON format",
            provider=self._provider.name,
            model=self._provider.model
        )

    # -------------------------------------------------------------------------
    # Main Analysis Method
    # -------------------------------------------------------------------------

    def analyze(self, transcript: str) -> AnalysisResult:
        """
        Analyze a meeting transcript.

        Args:
            transcript: The meeting transcript text

        Returns:
            AnalysisResult: Analysis with summary, action items, decisions

        Example:
            result = analyzer.analyze('''
                Speaker 1: Let's discuss the deployment.
                Speaker 2: I'll prepare the PR by Friday.
                Speaker 1: Great. We've decided to use PostgreSQL.
            ''')

            if result.success:
                print(f"Provider: {result.provider}/{result.model}")
                print(result.summary)
        """
        # Handle empty transcript
        if not transcript or not transcript.strip():
            return AnalysisResult(
                success=True,
                summary="No content to analyze.",
                action_items=[],
                decisions=[],
                key_topics=[],
                provider=self._provider.name,
                model=self._provider.model
            )

        try:
            # Build prompt and call LLM
            prompt = ANALYSIS_PROMPT.format(transcript=transcript)
            logger.info(f"Analyzing transcript using {self._provider.name}/{self._provider.model}")

            response = self._provider.generate(prompt)

            # Parse response
            result = self._parse_response(response)

            logger.info(
                f"Analysis complete: {len(result.action_items)} action items, "
                f"{len(result.decisions)} decisions"
            )

            return result

        except ServiceUnavailableError as e:
            logger.error(f"{self._provider.name} unavailable: {e}")
            return AnalysisResult(
                success=False,
                error_message=str(e),
                provider=self._provider.name,
                model=self._provider.model
            )
        except AnalysisTimeoutError as e:
            logger.error(f"Analysis timeout: {e}")
            return AnalysisResult(
                success=False,
                error_message=str(e),
                provider=self._provider.name,
                model=self._provider.model
            )
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return AnalysisResult(
                success=False,
                error_message=f"Analysis failed: {str(e)}",
                provider=self._provider.name,
                model=self._provider.model
            )

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def action_items_to_dict(items: List[ActionItem]) -> List[dict]:
        """
        Convert action items to dictionary format for JSON serialization.

        Args:
            items: List of ActionItem objects

        Returns:
            List[dict]: Action items as dictionaries
        """
        return [
            {
                "speaker": item.speaker,
                "task": item.task,
                "due_date": item.due_date,
                "priority": item.priority
            }
            for item in items
        ]

    @staticmethod
    def get_available_providers() -> List[str]:
        """
        Get list of available LLM providers based on configuration.

        Returns:
            List[str]: Names of configured providers
        """
        available = []

        # Check Ollama
        try:
            ollama = OllamaProvider()
            if ollama.is_available():
                available.append("ollama")
        except Exception:
            pass

        # Check OpenAI
        if settings.openai_api_key:
            available.append("openai")

        # Check Anthropic
        if settings.anthropic_api_key:
            available.append("anthropic")

        return available
