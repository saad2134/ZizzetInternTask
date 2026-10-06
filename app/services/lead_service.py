import hashlib
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import TenantMismatchError
from app.core.logging import logger
from app.models.lead import ConversationMessage, Customer, Lead, Tenant
from app.schemas.lead import LeadAnalysisInputSchema


class LeadService:
    @staticmethod
    def compute_conversation_hash(lead_input: LeadAnalysisInputSchema) -> str:
        """Computes a deterministic hash of lead conversation to support caching and deduplication."""
        items = [f"{m.role}:{m.message}" for m in lead_input.conversation]
        combined = f"{lead_input.tenant_id}|{lead_input.lead_id}|" + "|".join(items)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @staticmethod
    async def get_or_create_tenant(session: AsyncSession, tenant_id: str) -> Tenant:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await session.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(id=tenant_id, name=f"Tenant {tenant_id}")
            session.add(tenant)
            await session.flush()
        return tenant

    @staticmethod
    async def get_or_create_customer(
        session: AsyncSession,
        tenant_id: str,
        name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None
    ) -> Customer:
        stmt = select(Customer).where(
            Customer.tenant_id == tenant_id,
            Customer.name == name
        )
        if phone:
            stmt = select(Customer).where(
                Customer.tenant_id == tenant_id,
                (Customer.phone == phone) | (Customer.name == name)
            )
        result = await session.execute(stmt)
        customer = result.scalars().first()
        if not customer:
            customer = Customer(
                tenant_id=tenant_id,
                name=name,
                phone=phone,
                email=email
            )
            session.add(customer)
            await session.flush()
        else:
            if phone and not customer.phone:
                customer.phone = phone
            if email and not customer.email:
                customer.email = email
            await session.flush()
        return customer

    @staticmethod
    async def upsert_lead_and_conversations(
        session: AsyncSession,
        lead_input: LeadAnalysisInputSchema
    ) -> Lead:
        """
        Creates or updates lead, customer, and appends conversation messages.
        Enforces tenant isolation checks.
        """
        # Ensure tenant exists
        await LeadService.get_or_create_tenant(session, lead_input.tenant_id)

        # Get or create customer
        customer = await LeadService.get_or_create_customer(
            session=session,
            tenant_id=lead_input.tenant_id,
            name=lead_input.customer.name,
            phone=lead_input.customer.phone,
            email=lead_input.customer.email
        )

        # Check existing lead
        stmt = select(Lead).where(
            Lead.id == lead_input.lead_id,
            Lead.tenant_id == lead_input.tenant_id
        )
        result = await session.execute(stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            # Check if lead ID exists under another tenant (tenant conflict check)
            cross_check = select(Lead).where(Lead.id == lead_input.lead_id)
            cross_result = await session.execute(cross_check)
            existing_cross = cross_result.scalar_one_or_none()
            if existing_cross and existing_cross.tenant_id != lead_input.tenant_id:
                raise TenantMismatchError(
                    requested_tenant=lead_input.tenant_id,
                    target_tenant=existing_cross.tenant_id
                )

            lead = Lead(
                id=lead_input.lead_id,
                tenant_id=lead_input.tenant_id,
                customer_id=customer.id,
                source=lead_input.lead.source or "whatsapp",
                status=lead_input.lead.status or "new",
                lead_created_at=lead_input.lead.created_at,
                last_contacted_at=lead_input.lead.last_contacted_at,
                do_not_contact=False
            )
            session.add(lead)
            await session.flush()
        else:
            lead.customer_id = customer.id
            lead.source = lead_input.lead.source or lead.source
            lead.status = lead_input.lead.status or lead.status
            if lead_input.lead.created_at:
                lead.lead_created_at = lead_input.lead.created_at
            if lead_input.lead.last_contacted_at:
                lead.last_contacted_at = lead_input.lead.last_contacted_at
            await session.flush()

        # Delete existing messages and replace with latest conversation transcript
        # (or sync idempotently)
        stmt_del = select(ConversationMessage).where(
            ConversationMessage.tenant_id == lead_input.tenant_id,
            ConversationMessage.lead_id == lead_input.lead_id
        )
        existing_msgs = (await session.execute(stmt_del)).scalars().all()
        for em in existing_msgs:
            await session.delete(em)

        for msg in lead_input.conversation:
            convo_msg = ConversationMessage(
                tenant_id=lead_input.tenant_id,
                lead_id=lead_input.lead_id,
                role=msg.role,
                message=msg.message
            )
            session.add(convo_msg)

        await session.flush()
        return lead
