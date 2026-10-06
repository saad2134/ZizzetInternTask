import pytest
from httpx import AsyncClient
from app.services.messaging.mock_whatsapp import mock_whatsapp_provider


@pytest.mark.asyncio
async def test_follow_up_generation_and_dispatch(client: AsyncClient):
    """
    Tests generating a follow-up and sending it via mock WhatsApp provider.
    """
    # 1. Create and analyze lead
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_followup_test",
        "customer": {"name": "Ravi Patel", "phone": "+919988776655"},
        "lead": {"source": "whatsapp", "status": "contacted"},
        "conversation": [
            {"role": "customer", "message": "What is the price for 20 users?"}
        ]
    }
    await client.post("/api/v1/leads/analyze", json=payload)

    # 2. Trigger follow-up with send_immediately=True
    follow_req = {
        "channel": "whatsapp",
        "send_immediately": True
    }
    res = await client.post(
        "/api/v1/leads/lead_followup_test/follow-up?tenant_id=business_001",
        json=follow_req
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "SENT"
    assert data["provider_message_id"] is not None
    assert data["recipient_phone"] == "+919988776655"
    assert "Ravi" in data["follow_up_message"]

    # 3. Verify mock WhatsApp outbox received the message
    outbox = mock_whatsapp_provider.get_outbox()
    assert len(outbox) == 1
    assert outbox[0]["lead_id"] == "lead_followup_test"
    assert outbox[0]["recipient_phone"] == "+919988776655"


@pytest.mark.asyncio
async def test_follow_up_blocked_on_opt_out_lead(client: AsyncClient):
    """
    Guarantees that follow-ups are blocked if a lead has opted out (do_not_contact=true).
    """
    # Create lead with STOP opt-out
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_opted_out_user",
        "customer": {"name": "Opted Out User", "phone": "+1999111222"},
        "lead": {"source": "whatsapp", "status": "contacted"},
        "conversation": [
            {"role": "customer", "message": "STOP. Don't contact me again."}
        ]
    }
    await client.post("/api/v1/leads/analyze", json=payload)

    # Attempt to send follow-up
    res = await client.post(
        "/api/v1/leads/lead_opted_out_user/follow-up?tenant_id=business_001",
        json={"send_immediately": True}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert "opted out" in data["error"]["message"].lower()

    # Verify no message was dispatched to outbox
    assert len(mock_whatsapp_provider.get_outbox()) == 0
