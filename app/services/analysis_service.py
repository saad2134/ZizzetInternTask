import json
import re
from typing import Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import AnalysisNotFoundError, TenantMismatchError
from app.core.logging import logger
from app.models.analysis import LeadAnalysis
from app.models.lead import Lead
from app.schemas.analysis import AnalysisResponseSchema, RecoveryRecommendation
from app.schemas.lead import LeadAnalysisInputSchema
from app.services.lead_service import LeadService
from app.services.llm.base import BaseLLMProvider
from app.services.llm.factory import LLMFactory


class AnalysisService:
    @staticmethod
    def detect_opt_out_in_text(lead_input: LeadAnalysisInputSchema) -> bool:
        """
        Deterministic safety heuristic check across all conversation messages for opt-out keywords.
        Guarantees opt-outs are never missed even if an external LLM hallucinates.
        """
        opt_out_patterns = [
            r"\bstop\b",
            r"don'?t message (?:me )?again",
            r"do not message (?:me )?again",
            r"don'?t contact (?:me )?again",
            r"do not contact (?:me )?again",
            r"\bunsubscribe\b",
            r"\bopt out\b",
            r"\bleave me alone\b"
        ]
        for msg in lead_input.conversation:
            if msg.role == "customer":
                text = msg.message.lower()
                if any(re.search(pat, text) for pat in opt_out_patterns):
                    return True
        return False

    @staticmethod
    async def analyze_and_persist(
        session: AsyncSession,
        lead_input: LeadAnalysisInputSchema,
        provider: Optional[BaseLLMProvider] = None,
        prompt_version: Optional[str] = None,
        use_cache: bool = True
    ) -> AnalysisResponseSchema:
        """
        Coordinates full analysis pipeline:
        1. Lead & conversation persistence with tenant check
        2. Content hashing for caching / duplicate check
        3. LLM generation with retry / fallback
        4. Opt-out safety enforcement
        5. Analysis persistence
        """
        p_version = prompt_version or settings.PROMPT_VERSION
        llm_provider = provider or LLMFactory.get_provider()

        # Step 1: Upsert lead and store conversation history
        lead = await LeadService.upsert_lead_and_conversations(session, lead_input)

        # Step 2: Caching check
        content_hash = LeadService.compute_conversation_hash(lead_input)
        if use_cache:
            stmt_cache = select(LeadAnalysis).where(
                LeadAnalysis.tenant_id == lead_input.tenant_id,
                LeadAnalysis.lead_id == lead_input.lead_id,
                LeadAnalysis.content_hash == content_hash,
                LeadAnalysis.prompt_version == p_version
            ).order_by(desc(LeadAnalysis.created_at))

            cached_res = (await session.execute(stmt_cache)).scalars().first()
            if cached_res:
                logger.info(f"Returning cached analysis for lead '{lead_input.lead_id}' (hash={content_hash[:8]})")
                return AnalysisResponseSchema(
                    lead_score=cached_res.lead_score,
                    priority=cached_res.priority,
                    intent=cached_res.intent,
                    stage=cached_res.stage,
                    summary=cached_res.summary,
                    next_best_action=cached_res.next_best_action,
                    follow_up_channel=cached_res.follow_up_channel,
                    follow_up_message=cached_res.follow_up_message,
                    do_not_contact=cached_res.do_not_contact,
                    tenant_id=cached_res.tenant_id,
                    lead_id=cached_res.lead_id,
                    prompt_version=cached_res.prompt_version,
                    model_used=cached_res.model_used,
                    created_at=cached_res.created_at
                )

        # Step 3: Run LLM Inference
        recommendation: RecoveryRecommendation = await llm_provider.generate_analysis(
            lead_input=lead_input,
            prompt_version=p_version
        )

        # Step 4: Opt-out / DNC Safety Enforcement
        # If conversation contains opt-out signals, enforce do_not_contact=True & follow_up_message=None
        if AnalysisService.detect_opt_out_in_text(lead_input):
            recommendation.do_not_contact = True
            recommendation.follow_up_message = None
            recommendation.intent = "opt_out"
            recommendation.stage = "opted_out"
            recommendation.next_best_action = "Mark contact as opted-out and cease automated outreach"

        if recommendation.do_not_contact:
            recommendation.follow_up_message = None
            lead.do_not_contact = True
            await session.flush()

        # Step 5: Save Analysis Record
        analysis_record = LeadAnalysis(
            tenant_id=lead_input.tenant_id,
            lead_id=lead_input.lead_id,
            lead_score=recommendation.lead_score,
            priority=recommendation.priority,
            intent=recommendation.intent,
            stage=recommendation.stage,
            summary=recommendation.summary,
            next_best_action=recommendation.next_best_action,
            follow_up_channel=recommendation.follow_up_channel,
            follow_up_message=recommendation.follow_up_message,
            do_not_contact=recommendation.do_not_contact,
            prompt_version=p_version,
            model_used=f"{llm_provider.provider_name}:{llm_provider.model_name}",
            raw_llm_response=json.dumps(recommendation.model_dump()),
            content_hash=content_hash
        )
        session.add(analysis_record)
        await session.commit()
        await session.refresh(analysis_record)

        logger.info(
            f"Saved analysis for lead '{lead_input.lead_id}' (score={analysis_record.lead_score}, priority={analysis_record.priority})"
        )

        return AnalysisResponseSchema(
            lead_score=analysis_record.lead_score,
            priority=analysis_record.priority,
            intent=analysis_record.intent,
            stage=analysis_record.stage,
            summary=analysis_record.summary,
            next_best_action=analysis_record.next_best_action,
            follow_up_channel=analysis_record.follow_up_channel,
            follow_up_message=analysis_record.follow_up_message,
            do_not_contact=analysis_record.do_not_contact,
            tenant_id=analysis_record.tenant_id,
            lead_id=analysis_record.lead_id,
            prompt_version=analysis_record.prompt_version,
            model_used=analysis_record.model_used,
            created_at=analysis_record.created_at
        )

    @staticmethod
    async def get_latest_analysis(
        session: AsyncSession,
        tenant_id: str,
        lead_id: str
    ) -> AnalysisResponseSchema:
        """
        Retrieves the latest analysis for a lead while enforcing tenant isolation.
        """
        # Multi-tenancy check
        stmt = select(LeadAnalysis).where(
            LeadAnalysis.tenant_id == tenant_id,
            LeadAnalysis.lead_id == lead_id
        ).order_by(desc(LeadAnalysis.created_at))

        result = await session.execute(stmt)
        analysis = result.scalars().first()

        if not analysis:
            # Check if lead exists under another tenant to provide appropriate error
            cross_stmt = select(LeadAnalysis).where(LeadAnalysis.lead_id == lead_id)
            cross_res = (await session.execute(cross_stmt)).scalars().first()
            if cross_res and cross_res.tenant_id != tenant_id:
                raise TenantMismatchError(requested_tenant=tenant_id, target_tenant=cross_res.tenant_id)
            raise AnalysisNotFoundError(lead_id=lead_id, tenant_id=tenant_id)

        return AnalysisResponseSchema(
            lead_score=analysis.lead_score,
            priority=analysis.priority,
            intent=analysis.intent,
            stage=analysis.stage,
            summary=analysis.summary,
            next_best_action=analysis.next_best_action,
            follow_up_channel=analysis.follow_up_channel,
            follow_up_message=analysis.follow_up_message,
            do_not_contact=analysis.do_not_contact,
            tenant_id=analysis.tenant_id,
            lead_id=analysis.lead_id,
            prompt_version=analysis.prompt_version,
            model_used=analysis.model_used,
            created_at=analysis.created_at
        )
