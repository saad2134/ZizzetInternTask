import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(64), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    leads = relationship("Lead", back_populates="customer")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(64), primary_key=True, index=True)  # e.g. "lead_1024"
    tenant_id = Column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    source = Column(String(64), default="whatsapp", nullable=False)
    status = Column(String(64), default="new", nullable=False)
    lead_created_at = Column(String(64), nullable=True)  # string or date from input e.g. "2026-09-20"
    last_contacted_at = Column(String(64), nullable=True)
    do_not_contact = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="leads")
    customer = relationship("Customer", back_populates="leads")
    conversations = relationship(
        "ConversationMessage",
        primaryjoin="and_(Lead.id==ConversationMessage.lead_id, Lead.tenant_id==ConversationMessage.tenant_id)",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    analyses = relationship(
        "LeadAnalysis",
        primaryjoin="and_(Lead.id==LeadAnalysis.lead_id, Lead.tenant_id==LeadAnalysis.tenant_id)",
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="desc(LeadAnalysis.created_at)"
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), index=True, nullable=False)
    lead_id = Column(String(64), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # "customer", "agent", "system"
    message = Column(Text, nullable=False)
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
        primaryjoin="and_(ConversationMessage.lead_id==Lead.id, ConversationMessage.tenant_id==Lead.tenant_id)",
        back_populates="conversations"
    )
