import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tenant_isolation_get_analysis(client: AsyncClient):
    """
    Ensures that Tenant B cannot access Tenant A's lead analysis.
    """
    # 1. Create analysis for Tenant Alpha
    payload_a = {
        "tenant_id": "tenant_alpha",
        "lead_id": "lead_alpha_99",
        "customer": {"name": "Alice TenantA", "phone": "+1000000001"},
        "lead": {"source": "whatsapp", "status": "contacted"},
        "conversation": [
            {"role": "customer", "message": "We need 20 licenses for our team. What is the cost?"}
        ]
    }
    create_res = await client.post(
        "/api/v1/leads/analyze",
        json=payload_a,
        headers={"X-Tenant-ID": "tenant_alpha"}
    )
    assert create_res.status_code == 200

    # 2. Tenant Alpha can retrieve its analysis
    get_res_alpha = await client.get(
        "/api/v1/leads/lead_alpha_99/analysis",
        headers={"X-Tenant-ID": "tenant_alpha"}
    )
    assert get_res_alpha.status_code == 200
    assert get_res_alpha.json()["tenant_id"] == "tenant_alpha"

    # 3. Tenant Beta attempts to retrieve Tenant Alpha's lead analysis -> must be rejected (403 or 404)
    get_res_beta = await client.get(
        "/api/v1/leads/lead_alpha_99/analysis",
        headers={"X-Tenant-ID": "tenant_beta"}
    )
    assert get_res_beta.status_code in [403, 404]
    data_beta = get_res_beta.json()
    assert data_beta["success"] is False


@pytest.mark.asyncio
async def test_tenant_mismatch_header_and_payload(client: AsyncClient):
    """
    Verifies that passing a mismatched X-Tenant-ID header and payload tenant_id is rejected.
    """
    payload = {
        "tenant_id": "tenant_xyz",
        "lead_id": "lead_mismatch_1",
        "customer": {"name": "Mismatch User"},
        "lead": {"source": "whatsapp", "status": "new"},
        "conversation": [{"role": "customer", "message": "Hello!"}]
    }

    res = await client.post(
        "/api/v1/leads/analyze",
        json=payload,
        headers={"X-Tenant-ID": "tenant_abc"}  # Mismatch with payload's tenant_xyz
    )
    assert res.status_code == 403
    assert "Tenant mismatch" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_tenant_isolation_follow_up(client: AsyncClient):
    """
    Ensures that Tenant Beta cannot trigger follow-ups for Tenant Alpha's lead.
    """
    # Create lead in tenant Alpha
    payload_a = {
        "tenant_id": "tenant_alpha_2",
        "lead_id": "lead_alpha_follow",
        "customer": {"name": "Alpha Lead", "phone": "+1999888777"},
        "lead": {"source": "whatsapp", "status": "contacted"},
        "conversation": [{"role": "customer", "message": "Interested in demo."}]
    }
    await client.post("/api/v1/leads/analyze", json=payload_a)

    # Attempt follow-up from Tenant Beta
    res_beta = await client.post(
        "/api/v1/leads/lead_alpha_follow/follow-up",
        headers={"X-Tenant-ID": "tenant_beta_2"},
        json={"send_immediately": True}
    )
    assert res_beta.status_code in [403, 404]
