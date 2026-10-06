import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class LeadAnalysis(Base):
    __tablename__ = "lead_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), index=True, nullable=False)
    lead_id = Column(String(64), index=True, nullable=False)

    lead_score = Column(Integer, nullable=False)  # 0 to 100
    priority = Column(String(32), nullable=False)  # "high", "medium", "low"
    intent = Column(String(64), nullable=False)  # "purchase", "information", "support", etc.
    stage = Column(String(64), nullable=False)  # "pricing_interest", "discovery", etc.
    summary = Column(Text, nullable=False)
    next_best_action = Column(Text, nullable=False)
    follow_up_channel = Column(String(32), default="whatsapp", nullable=False)
    follow_up_message = Column(Text, nullable=True)
    do_not_contact = Column(Boolean, default=False, nullable=False)

    # Observability & Versioning metadata
    prompt_version = Column(String(32), default="v1.0.0", nullable=False)
    model_used = Column(String(64), default="mock", nullable=False)
    raw_llm_response = Column(Text, nullable=True)
    content_hash = Column(String(64), index=True, nullable=True)  # SHA-256 hash of conversation for caching

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["lead_id", "tenant_id"],
            ["leads.id", "leads.tenant_id"],
            ondelete="CASCADE"
        ),
    )

    lead = relationship(
        "Lead",
        primaryjoin="and_(LeadAnalysis.lead_id==Lead.id, LeadAnalysis.tenant_id==Lead.tenant_id)",
        foreign_keys=[lead_id, tenant_id],
        back_populates="analyses"
    )
