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


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model or settings.GEMINI_MODEL

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.LLM_BACKOFF_FACTOR, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def _call_api_with_retry(self, prompt_text: str) -> dict:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text}
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def generate_analysis(
        self,
        lead_input: LeadAnalysisInputSchema,
        prompt_version: str = "v1.0.0"
    ) -> RecoveryRecommendation:
        if not self._api_key:
            raise LLMGenerationError("Gemini API key is missing. Set GEMINI_API_KEY in environment.")

        system_prompt = PromptRegistry.get_system_prompt(prompt_version)
        user_prompt = PromptRegistry.format_user_prompt(lead_input)
        combined_prompt = f"{system_prompt}\n\nTask:\n{user_prompt}"

        try:
            logger.info(f"Invoking Gemini model '{self._model}' for lead '{lead_input.lead_id}'")
            res = await self._call_api_with_retry(combined_prompt)
            candidates = res.get("candidates", [])
            if not candidates:
                raise LLMGenerationError("No candidates returned from Gemini API")

            content_text = candidates[0]["content"]["parts"][0]["text"]
            parsed_json = json.loads(content_text)
            return RecoveryRecommendation.model_validate(parsed_json)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse Gemini JSON response: {str(exc)}")
            raise LLMGenerationError(f"Malformed JSON from Gemini: {str(exc)}")
        except Exception as exc:
            logger.error(f"Gemini API call failed: {str(exc)}")
            raise LLMGenerationError(f"Gemini error: {str(exc)}")
