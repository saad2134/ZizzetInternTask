from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FollowUpRequestSchema(BaseModel):
    channel: Optional[str] = Field("whatsapp", description="Channel to generate/send follow-up for (e.g. whatsapp, email, sms)")
    send_immediately: bool = Field(False, description="If True, dispatches the message immediately via the mock messaging provider")
    custom_tone: Optional[str] = Field(None, description="Optional custom instruction/tone override for the follow-up message generation")


class FollowUpResponseSchema(BaseModel):
    success: bool = Field(..., description="Whether the follow-up generation/dispatch was successful")
    lead_id: str = Field(..., description="Lead identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    channel: str = Field(..., description="Follow-up channel")
    recipient_name: Optional[str] = Field(None, description="Customer name")
    recipient_phone: Optional[str] = Field(None, description="Customer phone number")
    follow_up_message: Optional[str] = Field(None, description="Generated follow-up message text")
    do_not_contact: bool = Field(False, description="Whether customer has opted out")
    status: str = Field(..., description="Status: GENERATED, SENT, or BLOCKED_DNC")
    provider_message_id: Optional[str] = Field(None, description="Mock provider transaction/message ID if dispatched")
    created_at: Optional[datetime] = Field(None, description="Timestamp")
