from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import UsageEvent, Tenant
from app.meter_service import QuotaExceeded
from app.pricing import PLAN_QUOTAS

def current_usage(db: Session, tenant_id: str, usage_type: str) -> int:
    total = db.query(func.coalesce(func.sum(UsageEvent.quantity), 0)).filter_by(
        tenant_id=tenant_id, usage_type=usage_type
    ).scalar()
    return total or 0

def check_quota(db: Session, tenant: Tenant, usage_type: str, requested_qty: int):
    quotas = PLAN_QUOTAS[tenant.plan]
    limit_key = "api_call_limit" if usage_type == "api_call" else "token_limit"
    limit = quotas[limit_key]

    if tenant.status != "active":
        raise QuotaExceeded(402, f"Subscription status is '{tenant.status}'. Payment required to continue.")

    used = current_usage(db, tenant.id, usage_type)
    if used + requested_qty > limit:
        raise QuotaExceeded(
            429,
            f"Quota exceeded for {usage_type}: {used}/{limit} used, "
            f"requested {requested_qty} would exceed the {tenant.plan} plan limit."
        )