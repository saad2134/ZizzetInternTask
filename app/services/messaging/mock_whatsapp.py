import uuid
from typing import Any, Dict, List, Optional
from app.core.logging import logger
from app.services.messaging.base import BaseMessagingProvider, MessageDeliveryResult


class MockWhatsAppProvider(BaseMessagingProvider):
    """
    Mock WhatsApp provider that simulates WhatsApp Cloud API/Twilio delivery
    and keeps an in-memory outbox log for inspection and automated tests.
    """
    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    async def send_message(
        self,
        recipient_phone: str,
        message: str,
        tenant_id: str,
        lead_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageDeliveryResult:
        if not recipient_phone:
            logger.error(f"[MockWhatsApp] Delivery failed: Missing recipient phone for lead {lead_id}")
            return MessageDeliveryResult(
                success=False,
                message_id="",
                recipient=recipient_phone or "",
                channel="whatsapp",
                status="FAILED",
                provider="mock_whatsapp",
                error="Recipient phone is required"
            )

        msg_id = f"wamid.{uuid.uuid4().hex[:16]}"
        record = {
            "message_id": msg_id,
            "tenant_id": tenant_id,
            "lead_id": lead_id,
            "recipient_phone": recipient_phone,
            "message": message,
            "channel": "whatsapp",
            "status": "DELIVERED",
            "metadata": metadata or {}
        }
        self.sent_messages.append(record)

        logger.info(
            f"[MockWhatsApp] Outbound message dispatched successfully: id={msg_id} to={recipient_phone} tenant={tenant_id} lead={lead_id}",
            extra={"message_id": msg_id, "recipient": recipient_phone, "tenant_id": tenant_id, "lead_id": lead_id}
        )

        return MessageDeliveryResult(
            success=True,
            message_id=msg_id,
            recipient=recipient_phone,
            channel="whatsapp",
            status="DELIVERED",
            provider="mock_whatsapp",
            metadata={"simulated_timestamp": "now"}
        )

    def get_outbox(self) -> List[Dict[str, Any]]:
        return self.sent_messages

    def clear_outbox(self) -> None:
        self.sent_messages.clear()


# Global mock provider instance
mock_whatsapp_provider = MockWhatsAppProvider()
