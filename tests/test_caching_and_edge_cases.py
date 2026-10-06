import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analysis_caching_behavior(client: AsyncClient):
    """
    Verifies that calling /leads/analyze twice with identical conversation returns the cached analysis quickly.
    """
    payload = {
        "tenant_id": "business_001",
        "lead_id": "lead_cache_test_1",
        "customer": {"name": "Alex Mercer", "phone": "+1555444333"},
        "lead": {"source": "whatsapp", "status": "contacted"},
        "conversation": [
            {"role": "customer", "message": "Can you provide pricing details?"}
        ]
    }

    # Call 1
    res1 = await client.post("/api/v1/leads/analyze", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()

    # Call 2
    res2 = await client.post("/api/v1/leads/analyze", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()

    assert data1["lead_score"] == data2["lead_score"]
    assert data1["summary"] == data2["summary"]
    assert data1["created_at"] == data2["created_at"]  # Exact same record from cache!


@pytest.mark.asyncio
async def test_get_nonexistent_lead_analysis(client: AsyncClient):
    """
    Verifies 404 response when querying analysis for a nonexistent lead.
    """
    res = await client.get("/api/v1/leads/lead_does_not_exist_9999/analysis?tenant_id=business_001")
    assert res.status_code == 404
    data = res.json()
    assert data["success"] is False
    assert "no analysis found" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_health_and_info_endpoints(client: AsyncClient):
    """
    Verifies /api/v1/health and /api/v1/info endpoints.
    """
    health_res = await client.get("/api/v1/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    info_res = await client.get("/api/v1/info")
    assert info_res.status_code == 200
    assert "prompt_version" in info_res.json()
