from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db, init_db
from app.models import Tenant, UsageEvent
from app.meter_service import record_usage_with_quota_check
from app.exceptions import QuotaExceeded
from app.quota_service import current_usage
from app.pricing import PLAN_QUOTAS, calculate_cost_micro_cents
from app.schemas import GenerateRequest

app = FastAPI(title="Usage Metering & Billing Engine")
init_db()

from app.stripe_routes import router as stripe_router
app.include_router(stripe_router)


@app.post("/generate")
def generate(req: GenerateRequest, idempotency_key: str = Header(...), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).get(req.tenant_id)
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    usage_type = "tokens" if req.tokens else "api_call"
    quantity = req.tokens.output_tokens + req.tokens.input_tokens if req.tokens else 1

    token_breakdown = None
    if req.tokens:
        token_breakdown = {
            "input_tokens": req.tokens.input_tokens,
            "cached_input_tokens": req.tokens.cached_input_tokens,
            "output_tokens": req.tokens.output_tokens,
            "reasoning_tokens": req.tokens.reasoning_tokens,
        }

    cost_micro_cents = calculate_cost_micro_cents(token_breakdown) if req.tokens else 0

    # FIX: quota check + usage insert now run inside one function that holds
    # a row lock across both steps (see meter_service.py), instead of being
    # two separate, non-atomic calls as before.
    try:
        event = record_usage_with_quota_check(
            db, tenant, usage_type, quantity, idempotency_key,
            token_breakdown=token_breakdown,
            response_payload={"cost_micro_cents": cost_micro_cents, "usage_type": usage_type},
        )
    except QuotaExceeded as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return {"usage_event_id": event.id, "cost_micro_cents": cost_micro_cents, "usage_type": usage_type}


@app.get("/usage")
def get_usage(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    quotas = PLAN_QUOTAS[tenant.plan]
    api_used = current_usage(db, tenant.id, "api_call")
    token_used = current_usage(db, tenant.id, "tokens")

    events = db.query(UsageEvent).filter_by(tenant_id=tenant.id, usage_type="tokens").all()
    total_cost_micro_cents = sum(
        calculate_cost_micro_cents({
            "input_tokens": e.input_tokens,
            "cached_input_tokens": e.cached_input_tokens,
            "output_tokens": e.output_tokens,
            "reasoning_tokens": e.reasoning_tokens,
        }) for e in events
    )

    return {
        "tenant_id": tenant.id,
        "plan": tenant.plan,
        "api_calls": {"used": api_used, "limit": quotas["api_call_limit"]},
        "tokens": {"used": token_used, "limit": quotas["token_limit"]},
        "cost_micro_cents": total_cost_micro_cents,
    }