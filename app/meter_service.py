import json
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import UsageEvent

class QuotaExceeded(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail

def record_usage(db: Session, tenant_id: str, usage_type: str, quantity: int,
                  idempotency_key: str, token_breakdown: dict | None = None,
                  response_payload: dict | None = None) -> UsageEvent:
    existing = db.query(UsageEvent).filter_by(
        tenant_id=tenant_id, idempotency_key=idempotency_key
    ).first()
    if existing:
        return existing   # exact-same retry: return the ORIGINAL event, no new row

    event = UsageEvent(
        tenant_id=tenant_id,
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
        # race: two concurrent requests with the same key — re-read the winner
        db.rollback()
        existing = db.query(UsageEvent).filter_by(
            tenant_id=tenant_id, idempotency_key=idempotency_key
        ).first()
        return existing
    db.refresh(event)
    return event