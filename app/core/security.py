from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings
from app.core.logging import tenant_id_ctx


async def get_tenant_id(
    x_tenant_id: Optional[str] = Header(
        None,
        alias="X-Tenant-ID",
        description="Tenant identifier for multi-tenant isolation"
    )
) -> Optional[str]:
    """
    Extracts the tenant ID from the X-Tenant-ID header.
    Sets the contextual tenant variable for structured logging.
    """
    tenant_id = x_tenant_id or settings.DEFAULT_TENANT_ID
    if settings.REQUIRE_TENANT_HEADER and not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Tenant-ID' is required for this operation."
        )

    if tenant_id:
        tenant_id_ctx.set(tenant_id)

    return tenant_id
