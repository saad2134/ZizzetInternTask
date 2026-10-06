from typing import Any, Optional
from pydantic import BaseModel, Field
from app.schemas.lead import LeadAnalysisInputSchema


class WebhookLeadPayloadSchema(LeadAnalysisInputSchema):
    event_id: Optional[str] = Field(
        None,
        description="Optional unique identifier for the webhook event to guarantee idempotency",
        examples=["evt_98374291823"]
    )
    event_type: Optional[str] = Field(
        "lead.updated",
        description="Event type name",
        examples=["lead.updated", "conversation.message_received"]
    )


class WebhookResponseSchema(BaseModel):
    success: bool = Field(..., description="Whether the webhook was received and scheduled successfully")
    job_id: str = Field(..., description="Background processing job ID")
    tenant_id: str = Field(..., description="Tenant identifier")
    lead_id: str = Field(..., description="Lead identifier")
    status: str = Field(..., description="Current job status: PENDING, PROCESSING, COMPLETED, or DUPLICATE")
    is_duplicate: bool = Field(False, description="True if this event was already processed or queued (idempotency triggered)")
    message: str = Field(..., description="Informative status message")
    result: Optional[Any] = Field(None, description="Result if already available / duplicate cached")
