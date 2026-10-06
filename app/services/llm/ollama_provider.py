import json
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from app.core.exceptions import LLMGenerationError
from app.core.logging import logger
from app.schemas.analysis import RecoveryRecommendation
from app.schemas.lead import LeadAnalysisInputSchema
from app.services.llm.base import BaseLLMProvider
from app.services.llm.prompts import PromptRegistry


class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = None, model: str = None):
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = model or settings.OLLAMA_MODEL

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.LLM_BACKOFF_FACTOR, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _call_api_with_retry(self, payload: dict) -> dict:
        url = f"{self._base_url}/api/chat"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def generate_analysis(
        self,
        lead_input: LeadAnalysisInputSchema,
        prompt_version: str = "v1.0.0"
    ) -> RecoveryRecommendation:
        system_prompt = PromptRegistry.get_system_prompt(prompt_version)
        user_prompt = PromptRegistry.format_user_prompt(lead_input)

        payload = {
            "model": self._model,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }

        try:
            logger.info(f"Invoking Ollama model '{self._model}' at '{self._base_url}' for lead '{lead_input.lead_id}'")
            res = await self._call_api_with_retry(payload)
            content = res.get("message", {}).get("content", "")
            parsed_json = json.loads(content)
            return RecoveryRecommendation.model_validate(parsed_json)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse Ollama JSON response: {str(exc)}")
            raise LLMGenerationError(f"Malformed JSON from Ollama: {str(exc)}")
        except Exception as exc:
            logger.error(f"Ollama API call failed: {str(exc)}")
            raise LLMGenerationError(f"Ollama error: {str(exc)}")
