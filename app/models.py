import uuid
from datetime import datetime
from sqlalchemy import (Column, String, Integer, DateTime, ForeignKey,
                         UniqueConstraint, Boolean)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def gen_id():
    return str(uuid.uuid4())

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    plan = Column(String, nullable=False, default="free")   # "free" | "pro"
    status = Column(String, nullable=False, default="active")  # active/past_due/canceled
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Plan(Base):
    __tablename__ = "plans"
    name = Column(String, primary_key=True)      # "free" | "pro"
    api_call_limit = Column(Integer, nullable=False)
    token_limit = Column(Integer, nullable=False)

class UsageEvent(Base):
    __tablename__ = "usage_events"
    id = Column(String, primary_key=True, default=gen_id)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    usage_type = Column(String, nullable=False)   # "api_call" | "tokens"
    quantity = Column(Integer, nullable=False)
    # token breakdown, only used when usage_type == "tokens"
    input_tokens = Column(Integer, default=0)
    cached_input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    reasoning_tokens = Column(Integer, default=0)
    idempotency_key = Column(String, nullable=False)
    response_snapshot = Column(String, nullable=True)  # JSON string of the response we returned
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_tenant_idem_key"),
    )

class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"
    stripe_event_id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)