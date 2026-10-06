import datetime
from sqlalchemy import Column, DateTime, String, Text, UniqueConstraint
from app.db.base import Base


class WebhookJob(Base):
    __tablename__ = "webhook_jobs"

    id = Column(String(64), primary_key=True)  # UUID or job_id
    tenant_id = Column(String(64), index=True, nullable=False)
    lead_id = Column(String(64), index=True, nullable=False)
    idempotency_key = Column(String(128), index=True, nullable=False)
    payload_hash = Column(String(64), index=True, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    result_data = Column(Text, nullable=True)  # JSON serialized result
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_tenant_idempotency_key"),
    )
