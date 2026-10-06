import json
from sqlalchemy import select
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models.webhook import WebhookJob
from app.schemas.lead import LeadAnalysisInputSchema
from app.services.analysis_service import AnalysisService


async def process_webhook_lead_task(job_id: str, payload_dict: dict) -> None:
    """
    Background worker task to process a webhook lead event asynchronously:
    1. Updates WebhookJob status to PROCESSING
    2. Runs AI analysis and database persistence
    3. Updates WebhookJob status to COMPLETED and stores structured result
    """
    logger.info(f"[LeadWorker] Started processing webhook job '{job_id}'")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Update job to PROCESSING
            stmt = select(WebhookJob).where(WebhookJob.id == job_id)
            job = (await session.execute(stmt)).scalar_one_or_none()

            if not job:
                logger.error(f"[LeadWorker] WebhookJob '{job_id}' not found in database.")
                return

            job.status = "PROCESSING"
            await session.commit()

            # 2. Parse payload schema
            lead_input = LeadAnalysisInputSchema.model_validate(payload_dict)

            # 3. Run analysis
            analysis = await AnalysisService.analyze_and_persist(
                session=session,
                lead_input=lead_input,
                use_cache=False  # Direct processing
            )

            # 4. Update job to COMPLETED
            job.status = "COMPLETED"
            job.result_data = json.dumps(analysis.model_dump(), default=str)
            job.error_message = None
            await session.commit()

            logger.info(f"[LeadWorker] Successfully completed webhook job '{job_id}' for lead '{lead_input.lead_id}'")

        except Exception as exc:
            logger.error(f"[LeadWorker] Failed processing webhook job '{job_id}': {str(exc)}", exc_info=True)
            try:
                # Update job to FAILED
                stmt = select(WebhookJob).where(WebhookJob.id == job_id)
                job = (await session.execute(stmt)).scalar_one_or_none()
                if job:
                    job.status = "FAILED"
                    job.error_message = str(exc)
                    await session.commit()
            except Exception as inner_exc:
                logger.error(f"[LeadWorker] Failed saving job failure state: {str(inner_exc)}")
