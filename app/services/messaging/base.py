from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class MessageDeliveryResult(BaseModel):
    success: bool
    message_id: str
    recipient: str
    channel: str
    status: str
    provider: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseMessagingProvider(ABC):
    @abstractmethod
    async def send_message(
        self,
        recipient_phone: str,
        message: str,
        tenant_id: str,
        lead_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageDeliveryResult:
        """Sends an outbound message to a customer."""
        pass
