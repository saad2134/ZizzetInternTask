import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analyze_lead_pdf_example(client: AsyncClient):
    """
    Validates the exact example input from Page 1 of the PDF screening document.
    """
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_1024",
        "customer": {
            "name": "Arun Kumar",
            "phone": "+919876543210"
        },
        "lead": {
            "source": "whatsapp",
            "status": "contacted",
            "created_at": "2026-09-20",
            "last_contacted_at": "2026-09-25"
        },
        "conversation": [
            {"role": "customer", "message": "I am interested in your CRM."},
            {"role": "agent", "message": "How many users do you need?"},
            {"role": "customer", "message": "Around 25 users. What is the pricing?"}
        ]
    }

    response = await client.post("/api/v1/leads/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["lead_score"] >= 80
    assert data["priority"] == "high"
    assert data["intent"] == "purchase"
    assert data["stage"] == "pricing_interest"
    assert "25" in data["summary"] or "CRM" in data["summary"]
    assert "pricing" in data["next_best_action"].lower() or "demo" in data["next_best_action"].lower()
    assert data["follow_up_channel"] == "whatsapp"
    assert "Arun" in data["follow_up_message"]
    assert data["do_not_contact"] is False


@pytest.mark.asyncio
async def test_case_a_50_employees_pricing(client: AsyncClient):
    """
    Evaluation Case A:
    Scenario: 50 employees + asks for pricing
    Expected: High priority / purchase intent
    """
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_case_a",
        "customer": {"name": "Sara Chen", "phone": "+14155552671"},
        "lead": {"source": "whatsapp", "status": "contacted"},
        "conversation": [
            {"role": "customer", "message": "We have 50 employees and need a solution. What is your pricing?"}
        ]
    }

    response = await client.post("/api/v1/leads/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["priority"] == "high"
    assert data["intent"] == "purchase"
    assert data["lead_score"] >= 85
    assert data["do_not_contact"] is False
    assert data["follow_up_message"] is not None


@pytest.mark.asyncio
async def test_case_b_only_asks_what_product_does(client: AsyncClient):
    """
    Evaluation Case B:
    Scenario: Only asks what the product does
    Expected: Low priority
    """
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_case_b",
        "customer": {"name": "Bob Smith", "phone": "+12025550143"},
        "lead": {"source": "whatsapp", "status": "new"},
        "conversation": [
            {"role": "customer", "message": "Hi, what does the product do?"}
        ]
    }

    response = await client.post("/api/v1/leads/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["priority"] == "low"
    assert data["intent"] == "information"
    assert data["lead_score"] < 50
    assert data["do_not_contact"] is False


@pytest.mark.asyncio
async def test_case_c_requests_demo_call_tomorrow(client: AsyncClient):
    """
    Evaluation Case C:
    Scenario: Requests a demo/call tomorrow
    Expected: Demo/call as next action
    """
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_case_c",
        "customer": {"name": "Priya Sharma", "phone": "+919811223344"},
        "lead": {"source": "whatsapp", "status": "contacted"},
        "conversation": [
            {"role": "customer", "message": "Can we schedule a demo/call tomorrow to discuss our workflow?"}
        ]
    }

    response = await client.post("/api/v1/leads/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "demo" in data["next_best_action"].lower() or "call" in data["next_best_action"].lower()
    assert data["do_not_contact"] is False
    assert data["follow_up_message"] is not None


@pytest.mark.asyncio
async def test_case_d_opt_out_stop(client: AsyncClient):
    """
    Evaluation Case D:
    Scenario: Customer says: "STOP. Don't message me again."
    Expected: do_not_contact=true; no follow-up
    """
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_case_d",
        "customer": {"name": "John Doe", "phone": "+15551234567"},
        "lead": {"source": "whatsapp", "status": "contacted"},
        "conversation": [
            {"role": "agent", "message": "Hi John, checking in on your inquiry."},
            {"role": "customer", "message": "STOP. Don't message me again."}
        ]
    }

    response = await client.post("/api/v1/leads/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["do_not_contact"] is True
    assert data["follow_up_message"] is None
    assert data["intent"] == "opt_out"
    assert data["stage"] == "opted_out"


@pytest.mark.asyncio
async def test_analyze_invalid_payload_validation(client: AsyncClient):
    """
    Validates error handling on missing fields and invalid structures.
    """
    # Missing conversation
    invalid_payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_invalid",
        "customer": {"name": "Invalid Lead"}
    }
    response = await client.post("/api/v1/leads/analyze", json=invalid_payload)
    assert response.status_code == 422
