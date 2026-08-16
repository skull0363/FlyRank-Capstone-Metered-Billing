from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db, init_db
from app.models import Tenant
from app.meter_service import record_usage, QuotaExceeded
from app.quota_service import check_quota, current_usage
from app.pricing import PLAN_QUOTAS, calculate_cost
from app.schemas import GenerateRequest

app = FastAPI(title="Usage Metering & Billing Engine")
init_db()

@app.post("/generate")
def generate(req: GenerateRequest, idempotency_key: str = Header(...), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).get(req.tenant_id)
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    usage_type = "tokens" if req.tokens else "api_call"
    quantity = req.tokens.output_tokens + req.tokens.input_tokens if req.tokens else 1

    try:
        check_quota(db, tenant, usage_type, quantity)
    except QuotaExceeded as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    token_breakdown = None
    if req.tokens:
        token_breakdown = {
            "input_tokens": req.tokens.input_tokens,
            "cached_input_tokens": req.tokens.cached_input_tokens,
            "output_tokens": req.tokens.output_tokens,
            "reasoning_tokens": req.tokens.reasoning_tokens,
        }

    cost_cents = calculate_cost(token_breakdown) if req.tokens else 0

    event = record_usage(
        db, tenant.id, usage_type, quantity, idempotency_key,
        token_breakdown=token_breakdown,
        response_payload={"cost_cents": cost_cents, "usage_type": usage_type},
    )
    return {"usage_event_id": event.id, "cost_cents": cost_cents, "usage_type": usage_type}