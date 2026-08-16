import stripe
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Tenant, ProcessedWebhookEvent
from app.config import settings

stripe.api_key = settings.stripe_secret_key
router = APIRouter()

@router.post("/billing/checkout")
def create_checkout(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).get(tenant_id)
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    if not tenant.stripe_customer_id:
        customer = stripe.Customer.create(name=tenant.name, metadata={"tenant_id": tenant.id})
        tenant.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=tenant.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id_pro, "quantity": 1}],
        success_url="http://localhost:8000/success",
        cancel_url="http://localhost:8000/cancel",
        metadata={"tenant_id": tenant.id},
    )
    return {"checkout_url": session.url}

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(400, "Invalid signature")

    # dedup by Stripe event ID — replay of a real event is ignored
    if db.query(ProcessedWebhookEvent).get(event["id"]):
        return {"status": "already_processed"}

    _handle_event(db, event)

    db.add(ProcessedWebhookEvent(stripe_event_id=event["id"], event_type=event["type"]))
    db.commit()
    return {"status": "ok"}

def _handle_event(db: Session, event: dict):
    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        tenant_id = obj["metadata"]["tenant_id"]
        tenant = db.query(Tenant).get(tenant_id)
        tenant.plan = "pro"
        tenant.status = "active"
        tenant.stripe_subscription_id = obj.get("subscription")
        db.commit()

    elif etype == "customer.subscription.updated":
        tenant = db.query(Tenant).filter_by(stripe_subscription_id=obj["id"]).first()
        if tenant:
            tenant.status = "active" if obj["status"] == "active" else "past_due"
            db.commit()

    elif etype == "customer.subscription.deleted":
        tenant = db.query(Tenant).filter_by(stripe_subscription_id=obj["id"]).first()
        if tenant:
            tenant.plan = "free"
            tenant.status = "canceled"
            db.commit()