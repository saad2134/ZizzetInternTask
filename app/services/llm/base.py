from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.analysis import RecoveryRecommendation
from app.schemas.lead import LeadAnalysisInputSchema


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM providers.
    Every LLM provider must implement generate_analysis returning a validated RecoveryRecommendation.
    """
    @abstractmethod
    async def generate_analysis(
        self,
        lead_input: LeadAnalysisInputSchema,
        prompt_version: str = "v1.0.0"
    ) -> RecoveryRecommendation:
        """
        Analyzes lead data and conversation transcript and returns a validated structured RecoveryRecommendation.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider, e.g., 'openai', 'gemini', 'ollama', 'mock'."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier, e.g., 'gpt-4o-mini', 'gemini-1.5-flash', 'mock-rule-engine-v1'."""
        pass
