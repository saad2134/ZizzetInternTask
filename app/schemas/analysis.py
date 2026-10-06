from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class RecoveryRecommendation(BaseModel):
    """
    Structured AI output model for lead recovery recommendations.
    Matches the exact schema specified in the screening task.
    """
    lead_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Predicted lead purchase/conversion likelihood score from 0 to 100",
        examples=[86]
    )
    priority: Literal["high", "medium", "low"] = Field(
        ...,
        description="Urgency priority bucket for sales team action",
        examples=["high"]
    )
    intent: str = Field(
        ...,
        description="Classified user intent (e.g. purchase, pricing_inquiry, general_query, demo_request, opt_out)",
        examples=["purchase"]
    )
    stage: str = Field(
        ...,
        description="CRM pipeline lifecycle stage (e.g. pricing_interest, discovery, demo_scheduled, cold, opted_out)",
        examples=["pricing_interest"]
    )
    summary: str = Field(
        ...,
        description="Concise executive summary of customer needs and conversation context",
        examples=["Customer is evaluating a CRM for a 25-member team."]
    )
    next_best_action: str = Field(
        ...,
        description="Recommended next step for sales agent or automated pipeline",
        examples=["Send pricing and schedule a demo"]
    )
    follow_up_channel: str = Field(
        default="whatsapp",
        description="Preferred communication channel for next outreach",
        examples=["whatsapp"]
    )
    follow_up_message: Optional[str] = Field(
        default=None,
        description="Hyper-personalized follow-up message ready to send. Must be None/null if do_not_contact is True.",
        examples=["Hi Arun! Just following up on your CRM requirement..."]
    )
    do_not_contact: bool = Field(
        default=False,
        description="Flag indicating if customer opted out (e.g. STOP, unsubscribe, don't message me)",
        examples=[False]
    )

    @field_validator("follow_up_message")
    @classmethod
    def validate_opt_out_message(cls, v: Optional[str], info) -> Optional[str]:
        # If do_not_contact is True, follow_up_message must be None or empty
        if info.data.get("do_not_contact") is True:
            return None
        return v


class AnalysisResponseSchema(RecoveryRecommendation):
    """
    Extended response schema returned by the API including tenant and persistence metadata.
    """
    tenant_id: str = Field(..., description="Tenant identifier")
    lead_id: str = Field(..., description="Lead identifier")
    prompt_version: Optional[str] = Field(None, description="Prompt version used for LLM inference")
    model_used: Optional[str] = Field(None, description="LLM model name used for inference")
    created_at: Optional[datetime] = Field(None, description="Timestamp when analysis was generated")
