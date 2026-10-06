from app.core.config import settings
from app.core.logging import logger
from app.services.llm.base import BaseLLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.mock_provider import MockLLMProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider


class LLMFactory:
    """Factory to instantiate configured LLM provider with fallback handling."""

    @staticmethod
    def get_provider(provider_type: str = None) -> BaseLLMProvider:
        selected = (provider_type or settings.LLM_PROVIDER).lower()

        if selected == "openai":
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI API key not found in environment, falling back to mock provider.")
                return MockLLMProvider()
            return OpenAIProvider()

        elif selected == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.warning("Gemini API key not found in environment, falling back to mock provider.")
                return MockLLMProvider()
            return GeminiProvider()

        elif selected == "ollama":
            return OllamaProvider()

        elif selected == "mock":
            return MockLLMProvider()

        else:
            logger.warning(f"Unknown LLM provider '{selected}', defaulting to MockLLMProvider.")
            return MockLLMProvider()


# Global default provider
default_llm_provider = LLMFactory.get_provider()
