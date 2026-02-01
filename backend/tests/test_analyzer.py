"""
Meeting Agent - Analyzer Service Tests
=======================================

Tests for the AnalyzerService class which handles LLM-based meeting
analysis using multiple providers (Ollama, OpenAI, Anthropic).

Packages Used:
    - pytest: Test framework
        - fixture: Define reusable test fixtures
        - mark.skipif: Conditionally skip tests
        - mark.slow: Mark slow tests
    - unittest.mock: Mocking for unit tests

Test Categories:
    1. Service Initialization: Configuration and setup
    2. Provider Selection: Test provider factory
    3. Result Structure: Verify result format and fields
    4. Analysis (mocked): Test analysis with mocked providers
    5. Response Parsing: Test JSON parsing from LLM
    6. Error Handling: Edge cases and error conditions
    7. Integration: Actual LLM tests (marked slow)

Running These Tests:
    # Run all tests (excluding slow integration tests)
    pytest tests/test_analyzer.py -v -m "not slow"

    # Run integration tests (requires LLM provider running)
    pytest tests/test_analyzer.py -v -m slow
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from app.services.analyzer import (
    AnalyzerService,
    AnalysisResult,
    ActionItem,
    ServiceUnavailableError,
    AnalysisTimeoutError,
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    get_provider,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def analyzer_service():
    """Create an AnalyzerService instance with Ollama provider."""
    return AnalyzerService(provider="ollama")


@pytest.fixture
def sample_transcript():
    """Sample meeting transcript for testing."""
    return """
Speaker 1: Let's discuss the deployment timeline.
Speaker 2: I can have the PR ready by Friday.
Speaker 1: Great. Can you also send an email to the client?
Speaker 2: Sure, I'll send that today.
Speaker 1: We've decided to use PostgreSQL instead of MySQL.
Speaker 2: Good choice. I'll update the configuration.
Speaker 1: Let's also discuss the Q4 roadmap next week.
"""


@pytest.fixture
def mock_llm_response():
    """Mock successful LLM response."""
    return json.dumps({
        "summary": "Team discussed deployment timeline and database choice.",
        "action_items": [
            {
                "speaker": "Speaker 2",
                "task": "Prepare PR by Friday",
                "due_date": "Friday"
            },
            {
                "speaker": "Speaker 2",
                "task": "Send email to client",
                "due_date": "today"
            },
            {
                "speaker": "Speaker 2",
                "task": "Update configuration for PostgreSQL",
                "due_date": None
            }
        ],
        "decisions": [
            "Use PostgreSQL instead of MySQL"
        ],
        "key_topics": [
            "Deployment timeline",
            "Database selection",
            "Q4 roadmap"
        ]
    })


# -----------------------------------------------------------------------------
# Service Initialization Tests
# -----------------------------------------------------------------------------

class TestServiceInitialization:
    """Tests for AnalyzerService initialization."""

    def test_service_uses_default_settings(self, analyzer_service):
        """Should use settings from config by default."""
        assert analyzer_service.model is not None
        assert analyzer_service.provider_name == "ollama"

    def test_service_accepts_custom_config(self):
        """Should accept custom configuration."""
        service = AnalyzerService(
            provider="ollama",
            base_url="http://custom:11434",
            model="llama2",
            timeout=60
        )
        assert service.base_url == "http://custom:11434"
        assert service.model == "llama2"


# -----------------------------------------------------------------------------
# Provider Selection Tests
# -----------------------------------------------------------------------------

class TestProviderSelection:
    """Tests for LLM provider selection."""

    def test_get_ollama_provider(self):
        """Should create Ollama provider."""
        provider = get_provider("ollama")
        assert isinstance(provider, OllamaProvider)
        assert provider.name == "ollama"

    def test_get_openai_provider(self):
        """Should create OpenAI provider."""
        provider = get_provider("openai", api_key="test-key")
        assert isinstance(provider, OpenAIProvider)
        assert provider.name == "openai"

    def test_get_anthropic_provider(self):
        """Should create Anthropic provider."""
        provider = get_provider("anthropic", api_key="test-key")
        assert isinstance(provider, AnthropicProvider)
        assert provider.name == "anthropic"

    def test_invalid_provider_raises_error(self):
        """Should raise error for unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("invalid_provider")

    def test_service_with_openai_provider(self):
        """Should create service with OpenAI provider."""
        service = AnalyzerService(provider="openai", api_key="test-key")
        assert service.provider_name == "openai"

    def test_service_with_anthropic_provider(self):
        """Should create service with Anthropic provider."""
        service = AnalyzerService(provider="anthropic", api_key="test-key")
        assert service.provider_name == "anthropic"

    def test_get_available_providers(self):
        """Should list available providers."""
        # Mock the Ollama check to avoid network calls
        with patch.object(OllamaProvider, 'is_available', return_value=False):
            providers = AnalyzerService.get_available_providers()
            # Result depends on configured API keys
            assert isinstance(providers, list)


# -----------------------------------------------------------------------------
# Result Structure Tests
# -----------------------------------------------------------------------------

class TestResultStructure:
    """Tests for result data structures."""

    def test_action_item_has_required_fields(self):
        """ActionItem should have speaker and task."""
        item = ActionItem(
            speaker="John",
            task="Send report"
        )
        assert item.speaker == "John"
        assert item.task == "Send report"
        assert item.due_date is None
        assert item.priority is None

    def test_action_item_optional_fields(self):
        """ActionItem should support optional fields."""
        item = ActionItem(
            speaker="John",
            task="Send report",
            due_date="Friday",
            priority="high"
        )
        assert item.due_date == "Friday"
        assert item.priority == "high"

    def test_analysis_result_success_structure(self):
        """Successful AnalysisResult should have all fields."""
        result = AnalysisResult(
            success=True,
            summary="Meeting summary",
            action_items=[ActionItem(speaker="A", task="Do X")],
            decisions=["Decision 1"],
            key_topics=["Topic 1"],
            provider="ollama",
            model="mistral"
        )
        assert result.success is True
        assert result.summary == "Meeting summary"
        assert len(result.action_items) == 1
        assert len(result.decisions) == 1
        assert len(result.key_topics) == 1
        assert result.error_message is None
        assert result.provider == "ollama"
        assert result.model == "mistral"

    def test_analysis_result_failure_structure(self):
        """Failed AnalysisResult should have error message."""
        result = AnalysisResult(
            success=False,
            error_message="LLM not available"
        )
        assert result.success is False
        assert result.error_message == "LLM not available"
        assert result.summary == ""
        assert result.action_items == []


# -----------------------------------------------------------------------------
# Analysis Tests (Mocked)
# -----------------------------------------------------------------------------

class TestAnalysisMocked:
    """Tests using mocked LLM to avoid external dependencies."""

    def test_analyze_returns_result(self, analyzer_service, sample_transcript, mock_llm_response):
        """analyze should return an AnalysisResult."""
        with patch.object(analyzer_service._provider, 'generate') as mock_generate:
            mock_generate.return_value = mock_llm_response

            result = analyzer_service.analyze(sample_transcript)

            assert isinstance(result, AnalysisResult)
            assert result.success is True

    def test_analyze_extracts_summary(self, analyzer_service, sample_transcript, mock_llm_response):
        """Should extract summary from LLM response."""
        with patch.object(analyzer_service._provider, 'generate') as mock_generate:
            mock_generate.return_value = mock_llm_response

            result = analyzer_service.analyze(sample_transcript)

            assert "deployment" in result.summary.lower() or "database" in result.summary.lower()

    def test_analyze_extracts_action_items(self, analyzer_service, sample_transcript, mock_llm_response):
        """Should extract action items with speaker attribution."""
        with patch.object(analyzer_service._provider, 'generate') as mock_generate:
            mock_generate.return_value = mock_llm_response

            result = analyzer_service.analyze(sample_transcript)

            assert len(result.action_items) >= 2
            # Check structure
            action = result.action_items[0]
            assert action.speaker is not None
            assert action.task is not None

    def test_analyze_extracts_decisions(self, analyzer_service, sample_transcript, mock_llm_response):
        """Should extract decisions made."""
        with patch.object(analyzer_service._provider, 'generate') as mock_generate:
            mock_generate.return_value = mock_llm_response

            result = analyzer_service.analyze(sample_transcript)

            assert len(result.decisions) >= 1
            assert any("postgresql" in d.lower() for d in result.decisions)

    def test_analyze_extracts_key_topics(self, analyzer_service, sample_transcript, mock_llm_response):
        """Should extract key topics discussed."""
        with patch.object(analyzer_service._provider, 'generate') as mock_generate:
            mock_generate.return_value = mock_llm_response

            result = analyzer_service.analyze(sample_transcript)

            assert len(result.key_topics) >= 1

    def test_analyze_includes_provider_info(self, analyzer_service, sample_transcript, mock_llm_response):
        """Should include provider and model info in result."""
        with patch.object(analyzer_service._provider, 'generate') as mock_generate:
            mock_generate.return_value = mock_llm_response

            result = analyzer_service.analyze(sample_transcript)

            assert result.provider == "ollama"
            assert result.model is not None


# -----------------------------------------------------------------------------
# Response Parsing Tests
# -----------------------------------------------------------------------------

class TestResponseParsing:
    """Tests for LLM response parsing."""

    def test_parse_valid_json(self, analyzer_service):
        """Should parse valid JSON response."""
        json_response = json.dumps({
            "summary": "Test summary",
            "action_items": [{"speaker": "A", "task": "Do X"}],
            "decisions": ["Decision 1"],
            "key_topics": ["Topic 1"]
        })

        result = analyzer_service._parse_response(json_response)

        assert result.success is True
        assert result.summary == "Test summary"
        assert len(result.action_items) == 1

    def test_parse_json_with_markdown(self, analyzer_service):
        """Should parse JSON wrapped in markdown code blocks."""
        json_response = """```json
{
    "summary": "Test summary",
    "action_items": [],
    "decisions": [],
    "key_topics": []
}
```"""
        result = analyzer_service._parse_response(json_response)

        assert result.success is True
        assert result.summary == "Test summary"

    def test_parse_invalid_json_fallback(self, analyzer_service):
        """Should handle non-JSON response gracefully."""
        freeform_response = """
This is a meeting about deployment.
Action items include preparing the PR.
"""
        result = analyzer_service._parse_response(freeform_response)

        # Should still succeed but with limited data
        assert result.success is True

    def test_parse_empty_action_items(self, analyzer_service):
        """Should handle empty action items array."""
        json_response = json.dumps({
            "summary": "Brief meeting with no action items",
            "action_items": [],
            "decisions": [],
            "key_topics": []
        })

        result = analyzer_service._parse_response(json_response)

        assert result.success is True
        assert result.action_items == []


# -----------------------------------------------------------------------------
# Error Handling Tests
# -----------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for error handling."""

    def test_analyze_handles_empty_transcript(self, analyzer_service):
        """Should handle empty transcript gracefully."""
        result = analyzer_service.analyze("")

        assert result.success is True
        assert "no content" in result.summary.lower()
        assert result.action_items == []

    def test_analyze_handles_whitespace_transcript(self, analyzer_service):
        """Should handle whitespace-only transcript."""
        result = analyzer_service.analyze("   \n\n   ")

        assert result.success is True
        assert result.action_items == []

    def test_analyze_handles_connection_error(self, analyzer_service, sample_transcript):
        """Should handle LLM connection errors."""
        with patch.object(analyzer_service._provider, 'generate') as mock_generate:
            mock_generate.side_effect = ServiceUnavailableError("Cannot connect")

            result = analyzer_service.analyze(sample_transcript)

            assert result.success is False
            assert "connect" in result.error_message.lower()

    def test_analyze_handles_timeout(self, analyzer_service, sample_transcript):
        """Should handle analysis timeout."""
        with patch.object(analyzer_service._provider, 'generate') as mock_generate:
            mock_generate.side_effect = AnalysisTimeoutError("Timed out")

            result = analyzer_service.analyze(sample_transcript)

            assert result.success is False
            assert "timed" in result.error_message.lower() or "timeout" in result.error_message.lower()


# -----------------------------------------------------------------------------
# Utility Method Tests
# -----------------------------------------------------------------------------

class TestUtilityMethods:
    """Tests for utility methods."""

    def test_action_items_to_dict(self):
        """Should convert action items to dictionary format."""
        items = [
            ActionItem(speaker="A", task="Task 1", due_date="Friday"),
            ActionItem(speaker="B", task="Task 2", priority="high")
        ]

        result = AnalyzerService.action_items_to_dict(items)

        assert len(result) == 2
        assert result[0]["speaker"] == "A"
        assert result[0]["task"] == "Task 1"
        assert result[0]["due_date"] == "Friday"
        assert result[1]["priority"] == "high"

    def test_list_models_mocked(self, analyzer_service):
        """Should list available models."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "mistral:latest"},
                {"name": "llama2:latest"}
            ]
        }

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            models = analyzer_service.list_models()

            assert "mistral:latest" in models
            assert "llama2:latest" in models


# -----------------------------------------------------------------------------
# Availability Check Tests
# -----------------------------------------------------------------------------

class TestAvailabilityCheck:
    """Tests for LLM availability checking."""

    def test_is_available_when_running(self, analyzer_service):
        """Should return True when Ollama is running with model."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "mistral:latest"}]
        }

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            assert analyzer_service.is_available() is True

    def test_is_available_when_not_running(self, analyzer_service):
        """Should return False when Ollama is not running."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = Exception("Connection refused")

            assert analyzer_service.is_available() is False

    def test_is_available_model_not_found(self, analyzer_service):
        """Should return False when model is not available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "other-model:latest"}]
        }

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            # Use a model that isn't in the list
            service = AnalyzerService(provider="ollama", model="nonexistent")
            assert service.is_available() is False


# -----------------------------------------------------------------------------
# OpenAI Provider Tests
# -----------------------------------------------------------------------------

class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_openai_not_available_without_key(self):
        """Should not be available without API key."""
        provider = OpenAIProvider(api_key="")
        assert provider.is_available() is False

    def test_openai_available_with_key(self):
        """Should be available with API key (mocked)."""
        provider = OpenAIProvider(api_key="test-key")

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.models.list.return_value = []
            assert provider.is_available() is True

    def test_openai_generate_requires_key(self):
        """Should raise error when generating without key."""
        provider = OpenAIProvider(api_key="")

        with pytest.raises(ServiceUnavailableError, match="API key not configured"):
            provider.generate("test prompt")


# -----------------------------------------------------------------------------
# Anthropic Provider Tests
# -----------------------------------------------------------------------------

class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    def test_anthropic_not_available_without_key(self):
        """Should not be available without API key."""
        provider = AnthropicProvider(api_key="")
        assert provider.is_available() is False

    def test_anthropic_available_with_key(self):
        """Should be available with API key."""
        provider = AnthropicProvider(api_key="test-key")
        # Anthropic just checks if key is set (doesn't make API call)
        assert provider.is_available() is True

    def test_anthropic_generate_requires_key(self):
        """Should raise error when generating without key."""
        provider = AnthropicProvider(api_key="")

        with pytest.raises(ServiceUnavailableError, match="API key not configured"):
            provider.generate("test prompt")


# -----------------------------------------------------------------------------
# Integration Tests (require LLM provider running)
# -----------------------------------------------------------------------------

@pytest.mark.slow
class TestIntegration:
    """
    Integration tests that use actual LLM providers.

    These tests require:
    1. Ollama to be installed and running: ollama serve
    2. A model to be pulled: ollama pull mistral

    Or for cloud providers:
    - OPENAI_API_KEY environment variable set
    - ANTHROPIC_API_KEY environment variable set

    Run with: pytest tests/test_analyzer.py -v -m slow
    """

    @pytest.fixture
    def real_service(self):
        """Create service for integration tests."""
        return AnalyzerService(provider="ollama")

    def test_ollama_connection(self, real_service):
        """Should connect to Ollama if running."""
        if not real_service.is_available():
            pytest.skip("Ollama not available")

        models = real_service.list_models()
        assert len(models) > 0

    def test_actual_analysis(self, real_service, sample_transcript):
        """Test actual analysis with Ollama."""
        if not real_service.is_available():
            pytest.skip("Ollama not available")

        result = real_service.analyze(sample_transcript)

        assert result.success is True
        assert len(result.summary) > 0
        assert result.provider == "ollama"
        # Should extract at least some action items from the sample
        assert isinstance(result.action_items, list)
        assert isinstance(result.decisions, list)
