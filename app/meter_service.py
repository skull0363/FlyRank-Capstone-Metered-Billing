import json
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import UsageEvent, Tenant
from app.exceptions import QuotaExceeded  # FIX: no longer defined here, see exceptions.py
from app.quota_service import check_quota


def record_usage_with_quota_check(
    db: Session, tenant: Tenant, usage_type: str, quantity: int,
    idempotency_key: str, token_breakdown: dict | None = None,
    response_payload: dict | None = None,
) -> UsageEvent:
    existing = db.query(UsageEvent).filter_by(
        tenant_id=tenant.id, idempotency_key=idempotency_key
    ).first()
    if existing:
        return existing

    db.query(Tenant).filter_by(id=tenant.id).with_for_update().first()

    check_quota(db, tenant, usage_type, quantity)

    event = UsageEvent(
        tenant_id=tenant.id,
        usage_type=usage_type,
        quantity=quantity,
        idempotency_key=idempotency_key,
        response_snapshot=json.dumps(response_payload) if response_payload else None,
        **(token_breakdown or {}),
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(UsageEvent).filter_by(
            tenant_id=tenant.id, idempotency_key=idempotency_key
        ).first()
        return existing
    db.refresh(event)
    return event