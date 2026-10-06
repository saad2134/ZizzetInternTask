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


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._model = model or settings.OPENAI_MODEL

    @property
    def provider_name(self) -> str:
        return "openai"

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
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def generate_analysis(
        self,
        lead_input: LeadAnalysisInputSchema,
        prompt_version: str = "v1.0.0"
    ) -> RecoveryRecommendation:
        if not self._api_key:
            raise LLMGenerationError("OpenAI API key is missing. Set OPENAI_API_KEY in environment.")

        system_prompt = PromptRegistry.get_system_prompt(prompt_version)
        user_prompt = PromptRegistry.format_user_prompt(lead_input)

        payload = {
            "model": self._model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }

        try:
            logger.info(f"Invoking OpenAI model '{self._model}' for lead '{lead_input.lead_id}'")
            res = await self._call_api_with_retry(payload)
            content = res["choices"][0]["message"]["content"]
            parsed_json = json.loads(content)
            return RecoveryRecommendation.model_validate(parsed_json)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse OpenAI JSON response: {str(exc)}")
            raise LLMGenerationError(f"Malformed JSON from OpenAI: {str(exc)}")
        except Exception as exc:
            logger.error(f"OpenAI API call failed: {str(exc)}")
            raise LLMGenerationError(f"OpenAI error: {str(exc)}")
