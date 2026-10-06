from typing import Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import AnalysisNotFoundError, LeadNotFoundError, OptOutError, TenantMismatchError
from app.core.logging import logger
from app.models.analysis import LeadAnalysis
from app.models.follow_up import FollowUpLog
from app.models.lead import Customer, Lead
from app.schemas.follow_up import FollowUpRequestSchema, FollowUpResponseSchema
from app.services.messaging.mock_whatsapp import mock_whatsapp_provider


class FollowUpService:
    @staticmethod
    async def process_follow_up(
        session: AsyncSession,
        tenant_id: str,
        lead_id: str,
        request: FollowUpRequestSchema
    ) -> FollowUpResponseSchema:
        """
        Generates or dispatches a personalized follow-up for a lead.
        Enforces tenant isolation and do_not_contact guardrails.
        """
        # Fetch lead with tenant check
        stmt_lead = select(Lead).where(
            Lead.id == lead_id,
            Lead.tenant_id == tenant_id
        )
        lead = (await session.execute(stmt_lead)).scalar_one_or_none()

        if not lead:
            cross_lead = (await session.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
            if cross_lead and cross_lead.tenant_id != tenant_id:
                raise TenantMismatchError(requested_tenant=tenant_id, target_tenant=cross_lead.tenant_id)
            raise LeadNotFoundError(lead_id=lead_id, tenant_id=tenant_id)

        # Check opt-out on lead record
        if lead.do_not_contact:
            # Log blocked attempt
            log_entry = FollowUpLog(
                tenant_id=tenant_id,
                lead_id=lead_id,
                channel=request.channel or "whatsapp",
                status="BLOCKED_DNC",
                error_message="Customer previously opted out (do_not_contact=True)"
            )
            session.add(log_entry)
            await session.commit()
            raise OptOutError(lead_id=lead_id)

        # Fetch latest analysis
        stmt_analysis = select(LeadAnalysis).where(
            LeadAnalysis.tenant_id == tenant_id,
            LeadAnalysis.lead_id == lead_id
        ).order_by(desc(LeadAnalysis.created_at))
        analysis = (await session.execute(stmt_analysis)).scalars().first()

        if not analysis:
            raise AnalysisNotFoundError(lead_id=lead_id, tenant_id=tenant_id)

        if analysis.do_not_contact:
            raise OptOutError(lead_id=lead_id)

        # Customer information
        customer = None
        if lead.customer_id:
            customer = (await session.execute(select(Customer).where(Customer.id == lead.customer_id))).scalar_one_or_none()

        recipient_phone = customer.phone if customer else None
        recipient_name = customer.name if customer else "Customer"
        follow_up_msg = analysis.follow_up_message

        if not follow_up_msg:
            follow_up_msg = f"Hi {recipient_name}! Just following up to see if you have any questions or need assistance."

        status_text = "GENERATED"
        provider_msg_id = None

        if request.send_immediately:
            # Dispatch via Mock WhatsApp Provider
            delivery = await mock_whatsapp_provider.send_message(
                recipient_phone=recipient_phone or "+0000000000",
                message=follow_up_msg,
                tenant_id=tenant_id,
                lead_id=lead_id,
                metadata={"source": "api_follow_up"}
            )
            status_text = "SENT" if delivery.success else "FAILED"
            provider_msg_id = delivery.message_id

            # Persist FollowUpLog
            log_entry = FollowUpLog(
                tenant_id=tenant_id,
                lead_id=lead_id,
                channel=request.channel or "whatsapp",
                recipient_phone=recipient_phone,
                recipient_name=recipient_name,
                message=follow_up_msg,
                status=status_text,
                provider="mock_whatsapp",
                provider_message_id=provider_msg_id
            )
            session.add(log_entry)
            await session.commit()

        return FollowUpResponseSchema(
            success=True,
            lead_id=lead_id,
            tenant_id=tenant_id,
            channel=request.channel or "whatsapp",
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            follow_up_message=follow_up_msg,
            do_not_contact=False,
            status=status_text,
            provider_message_id=provider_msg_id
        )
