from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class CustomerSchema(BaseModel):
    name: str = Field(..., description="Customer full name", examples=["Arun Kumar"])
    phone: Optional[str] = Field(None, description="Customer phone number in international format", examples=["+919876543210"])
    email: Optional[str] = Field(None, description="Customer email address", examples=["arun@example.com"])


class LeadDetailsSchema(BaseModel):
    source: str = Field(default="whatsapp", description="Lead source channel", examples=["whatsapp"])
    status: str = Field(default="contacted", description="Current CRM lead status", examples=["contacted"])
    created_at: Optional[str] = Field(None, description="Creation timestamp or date string", examples=["2026-09-20"])
    last_contacted_at: Optional[str] = Field(None, description="Last contact timestamp or date string", examples=["2026-09-25"])


class ConversationMessageSchema(BaseModel):
    role: Literal["customer", "agent", "system"] = Field(..., description="Speaker role in the conversation")
    message: str = Field(..., description="Text content of the message", min_length=1)


class LeadAnalysisInputSchema(BaseModel):
    tenant_id: str = Field(..., description="Identifier of the business tenant", examples=["business_001"])
    lead_id: str = Field(..., description="Unique lead identifier within the tenant", examples=["lead_1024"])
    customer: CustomerSchema = Field(..., description="Customer profile information")
    lead: LeadDetailsSchema = Field(..., description="Lead metadata")
    conversation: List[ConversationMessageSchema] = Field(
        ...,
        description="Chronological transcript of conversation messages",
        min_length=1
    )
