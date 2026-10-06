import hashlib
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import TenantMismatchError, WebhookJobNotFoundError
from app.core.logging import logger
from app.core.security import get_tenant_id
from app.db.session import get_db
from app.models.webhook import WebhookJob
from app.schemas.webhook import WebhookLeadPayloadSchema, WebhookResponseSchema
from app.services.lead_service import LeadService
from app.workers.queue import job_queue

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Async Processing"])


@router.post(
    "/leads",
    response_model=WebhookResponseSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive Lead Webhook Event",
    description="Asynchronously receives lead event webhook, validates payload, enforces idempotency, and schedules background AI processing."
)
async def receive_lead_webhook(
    payload: WebhookLeadPayloadSchema,
    idempotency_header: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    header_tenant_id: Optional[str] = Depends(get_tenant_id)
):
    if header_tenant_id and header_tenant_id != payload.tenant_id:
        raise TenantMismatchError(requested_tenant=header_tenant_id, target_tenant=payload.tenant_id)

    # 1. Compute idempotency key and payload hash
    content_hash = LeadService.compute_conversation_hash(payload)
    idempotency_key = payload.event_id or idempotency_header or f"hash_{content_hash}"

    logger.info(
        f"[Webhook] Received webhook event for lead '{payload.lead_id}' (tenant: {payload.tenant_id}, key: {idempotency_key})"
    )

    # 2. Check for duplicate event (Evaluation Case E)
    stmt = select(WebhookJob).where(
        WebhookJob.tenant_id == payload.tenant_id,
        WebhookJob.idempotency_key == idempotency_key
    )
    existing_job = (await db.execute(stmt)).scalar_one_or_none()

    if existing_job:
        logger.info(
            f"[Webhook] Idempotent duplicate detected for key '{idempotency_key}', job_id='{existing_job.id}', status='{existing_job.status}'"
        )
        parsed_result = None
        if existing_job.result_data:
            try:
                parsed_result = json.loads(existing_job.result_data)
            except Exception:
                parsed_result = existing_job.result_data

        return WebhookResponseSchema(
            success=True,
            job_id=existing_job.id,
            tenant_id=existing_job.tenant_id,
            lead_id=existing_job.lead_id,
            status=existing_job.status,
            is_duplicate=True,
            message="Duplicate webhook event detected. Returning existing job record without re-processing.",
            result=parsed_result
        )

    # 3. Create new WebhookJob
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    new_job = WebhookJob(
        id=job_id,
        tenant_id=payload.tenant_id,
        lead_id=payload.lead_id,
        idempotency_key=idempotency_key,
        payload_hash=content_hash,
        status="PENDING"
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    # 4. Enqueue background processing
    await job_queue.enqueue(
        "process_webhook_lead",
        job_id=job_id,
        payload_dict=payload.model_dump()
    )

    return WebhookResponseSchema(
        success=True,
        job_id=job_id,
        tenant_id=payload.tenant_id,
        lead_id=payload.lead_id,
        status="PENDING",
        is_duplicate=False,
        message="Webhook event accepted and queued for background AI recovery analysis.",
        result=None
    )


@router.get(
    "/jobs/{job_id}",
    response_model=WebhookResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get Webhook Job Status",
    description="Poll or check the status and structured AI result of a background webhook job."
)
async def get_webhook_job_status(
    job_id: str,
    tenant_id: Optional[str] = Query(None, description="Tenant ID (or use X-Tenant-ID header)"),
    db: AsyncSession = Depends(get_db),
    header_tenant_id: Optional[str] = Depends(get_tenant_id)
):
    effective_tenant = header_tenant_id or tenant_id

    stmt = select(WebhookJob).where(WebhookJob.id == job_id)
    job = (await db.execute(stmt)).scalar_one_or_none()

    if not job:
        raise WebhookJobNotFoundError(job_id=job_id)

    if effective_tenant and job.tenant_id != effective_tenant:
        raise TenantMismatchError(requested_tenant=effective_tenant, target_tenant=job.tenant_id)

    parsed_result = None
    if job.result_data:
        try:
            parsed_result = json.loads(job.result_data)
        except Exception:
            parsed_result = job.result_data

    return WebhookResponseSchema(
        success=True,
        job_id=job.id,
        tenant_id=job.tenant_id,
        lead_id=job.lead_id,
        status=job.status,
        is_duplicate=False,
        message=job.error_message or f"Job status is {job.status}",
        result=parsed_result
    )
