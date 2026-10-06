from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import TenantMismatchError
from app.core.logging import logger
from app.core.security import get_tenant_id
from app.db.session import get_db
from app.schemas.analysis import AnalysisResponseSchema
from app.schemas.follow_up import FollowUpRequestSchema, FollowUpResponseSchema
from app.schemas.lead import LeadAnalysisInputSchema
from app.services.analysis_service import AnalysisService
from app.services.follow_up_service import FollowUpService

router = APIRouter(prefix="/leads", tags=["Leads & AI Recovery"])


@router.post(
    "/analyze",
    response_model=AnalysisResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Analyze Lead + Conversation",
    description="Synchronously analyzes customer conversation transcript and lead details using the LLM engine to produce a structured recovery recommendation."
)
async def analyze_lead(
    payload: LeadAnalysisInputSchema,
    db: AsyncSession = Depends(get_db),
    header_tenant_id: Optional[str] = Depends(get_tenant_id)
):
    # Enforce tenant isolation if header is present
    if header_tenant_id and header_tenant_id != payload.tenant_id:
        raise TenantMismatchError(requested_tenant=header_tenant_id, target_tenant=payload.tenant_id)

    logger.info(f"API /leads/analyze request for lead '{payload.lead_id}' (tenant: {payload.tenant_id})")

    analysis = await AnalysisService.analyze_and_persist(
        session=db,
        lead_input=payload,
        use_cache=True
    )
    return analysis


@router.get(
    "/{lead_id}/analysis",
    response_model=AnalysisResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Latest Lead Analysis",
    description="Retrieves the most recent AI recovery analysis recommendation for a specific lead. Enforces tenant isolation."
)
async def get_lead_analysis(
    lead_id: str,
    tenant_id: Optional[str] = Query(None, description="Tenant identifier (or use X-Tenant-ID header)"),
    db: AsyncSession = Depends(get_db),
    header_tenant_id: Optional[str] = Depends(get_tenant_id)
):
    effective_tenant = header_tenant_id or tenant_id or "business_001"
    logger.info(f"API /leads/{lead_id}/analysis retrieval requested for tenant '{effective_tenant}'")

    analysis = await AnalysisService.get_latest_analysis(
        session=db,
        tenant_id=effective_tenant,
        lead_id=lead_id
    )
    return analysis


@router.post(
    "/{lead_id}/follow-up",
    response_model=FollowUpResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Generate or Send Follow-Up",
    description="Generates a tailored follow-up message or dispatches it via mock WhatsApp provider. Strictly respects do_not_contact opt-out settings."
)
async def generate_lead_follow_up(
    lead_id: str,
    request: FollowUpRequestSchema = FollowUpRequestSchema(),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier (or use X-Tenant-ID header)"),
    db: AsyncSession = Depends(get_db),
    header_tenant_id: Optional[str] = Depends(get_tenant_id)
):
    effective_tenant = header_tenant_id or tenant_id or "business_001"
    logger.info(f"API /leads/{lead_id}/follow-up requested for tenant '{effective_tenant}', send_immediately={request.send_immediately}")

    result = await FollowUpService.process_follow_up(
        session=db,
        tenant_id=effective_tenant,
        lead_id=lead_id,
        request=request
    )
    return result
