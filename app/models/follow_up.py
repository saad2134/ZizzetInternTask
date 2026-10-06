import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.db.base import Base


class FollowUpLog(Base):
    __tablename__ = "follow_up_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), index=True, nullable=False)
    lead_id = Column(String(64), index=True, nullable=False)
    channel = Column(String(32), default="whatsapp", nullable=False)
    recipient_phone = Column(String(64), nullable=True)
    recipient_name = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String(32), default="SENT", nullable=False)  # SENT, FAILED, BLOCKED_DNC
    provider = Column(String(64), default="mock_whatsapp", nullable=False)
    provider_message_id = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
