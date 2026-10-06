import asyncio
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_case_e_webhook_idempotency_duplicate_submission(client: AsyncClient):
    """
    Evaluation Case E:
    Scenario: Same webhook event submitted twice
    Expected: One job / one processing result (idempotency triggered, duplicate skipped)
    """
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_webhook_case_e",
        "event_id": "evt_unique_1001",
        "customer": {"name": "David Miller", "phone": "+13125550198"},
        "lead": {"source": "whatsapp", "status": "contacted"},
        "conversation": [
            {"role": "customer", "message": "Hi, we have 30 team members. Can you share pricing?"}
        ]
    }

    # 1. First submission
    response_1 = await client.post("/api/v1/webhooks/leads", json=payload)
    assert response_1.status_code == 202
    data_1 = response_1.json()
    assert data_1["success"] is True
    assert data_1["is_duplicate"] is False
    job_id_1 = data_1["job_id"]

    # 2. Second submission with the exact same event
    response_2 = await client.post("/api/v1/webhooks/leads", json=payload)
    assert response_2.status_code == 202
    data_2 = response_2.json()
    assert data_2["success"] is True
    assert data_2["is_duplicate"] is True  # Idempotent match!
    assert data_2["job_id"] == job_id_1    # Same job referenced, no duplicate job created!


@pytest.mark.asyncio
async def test_webhook_idempotency_via_header(client: AsyncClient):
    """
    Validates idempotency when using the standard 'Idempotency-Key' HTTP header.
    """
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_header_idemp",
        "customer": {"name": "Emma Watson", "phone": "+447700900077"},
        "lead": {"source": "whatsapp", "status": "new"},
        "conversation": [
            {"role": "customer", "message": "Hello, tell me about your pricing."}
        ]
    }

    headers = {"Idempotency-Key": "idemp_custom_key_777"}

    # First call
    res_1 = await client.post("/api/v1/webhooks/leads", json=payload, headers=headers)
    assert res_1.status_code == 202
    data_1 = res_1.json()
    assert data_1["is_duplicate"] is False

    # Second call with same header
    res_2 = await client.post("/api/v1/webhooks/leads", json=payload, headers=headers)
    assert res_2.status_code == 202
    data_2 = res_2.json()
    assert data_2["is_duplicate"] is True
    assert data_2["job_id"] == data_1["job_id"]


@pytest.mark.asyncio
async def test_get_webhook_job_status(client: AsyncClient):
    """
    Checks retrieval of webhook job status.
    """
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_status_check",
        "customer": {"name": "Grace Hopper"},
        "lead": {"source": "whatsapp", "status": "new"},
        "conversation": [{"role": "customer", "message": "Demo request."}]
    }

    res = await client.post("/api/v1/webhooks/leads", json=payload)
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    # Poll status endpoint
    status_res = await client.get(f"/api/v1/webhooks/jobs/{job_id}?tenant_id=business_001")
    assert status_res.status_code == 200
    assert status_res.json()["job_id"] == job_id
