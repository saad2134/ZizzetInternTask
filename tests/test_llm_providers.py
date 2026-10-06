import pytest
from app.schemas.lead import ConversationMessageSchema, CustomerSchema, LeadAnalysisInputSchema, LeadDetailsSchema
from app.services.llm.factory import LLMFactory
from app.services.llm.mock_provider import MockLLMProvider
from app.services.llm.prompts import PromptRegistry


@pytest.mark.asyncio
async def test_mock_llm_provider_direct():
    provider = MockLLMProvider()
    input_data = LeadAnalysisInputSchema(
        tenant_id="test_tenant",
        lead_id="lead_direct_test",
        customer=CustomerSchema(name="Test User", phone="+123456789"),
        lead=LeadDetailsSchema(source="whatsapp", status="contacted"),
        conversation=[
            ConversationMessageSchema(role="customer", message="I have 50 employees and need pricing.")
        ]
    )

    result = await provider.generate_analysis(input_data)
    assert result.lead_score >= 85
    assert result.priority == "high"
    assert result.intent == "purchase"
    assert result.do_not_contact is False


def test_llm_factory_fallback():
    # When provider is not found, defaults to MockLLMProvider
    provider = LLMFactory.get_provider("non_existent_provider")
    assert isinstance(provider, MockLLMProvider)


def test_prompt_registry_versioning():
    prompt_v1 = PromptRegistry.get_system_prompt("v1.0.0")
    prompt_v1_1 = PromptRegistry.get_system_prompt("v1.1.0")

    assert "OPT-OUT RULE" in prompt_v1
    assert "MULTI-LANGUAGE" in prompt_v1_1
