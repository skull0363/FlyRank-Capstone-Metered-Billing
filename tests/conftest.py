
import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_db
from app.models import Base, Tenant, UsageEvent

TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_WEBHOOK_SECRET = "whsec_test_secret_for_ci_only"


@pytest.fixture()
def db_session():
    """A fresh in-memory SQLite DB per test, so tests never leak state into each other."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """A TestClient with the real app, but get_db overridden to use the
    per-test in-memory database instead of the on-disk billing.db."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def tenant(db_session):
    """A plain Free-plan tenant with zero usage."""
    t = Tenant(name="Acme Corp", plan="free", status="active")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


@pytest.fixture()
def tenant_at_999_calls(db_session):
    """A Free-plan tenant sitting exactly one API call away from its 1,000/month quota."""
    t = Tenant(name="Boundary Corp", plan="free", status="active")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    for i in range(999):
        db_session.add(UsageEvent(
            tenant_id=t.id, usage_type="api_call", quantity=1,
            idempotency_key=f"seed-{i}",
        ))
    db_session.commit()
    return t


def _sign_stripe_payload(payload: bytes, secret: str, timestamp: int) -> str:
    """Replicates Stripe's webhook signing scheme: HMAC-SHA256 over
    '{timestamp}.{payload}', formatted as Stripe's Stripe-Signature header."""
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    signature = hmac.new(
        secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


@pytest.fixture()
def valid_stripe_event_payload_and_sig(tenant, monkeypatch):
    """A real (correctly-signed) checkout.session.completed payload, plus the
    matching Stripe-Signature header, so tests can prove the happy path and
    the duplicate-delivery path both work."""
    from app import config
    monkeypatch.setattr(config.settings, "stripe_webhook_secret", TEST_WEBHOOK_SECRET)

    event = {
        "id": "evt_test_12345",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_12345",
                "subscription": "sub_test_12345",
                "metadata": {"tenant_id": tenant.id},
            }
        },
    }
    payload = json.dumps(event).encode("utf-8")
    timestamp = int(time.time())
    sig_header = _sign_stripe_payload(payload, TEST_WEBHOOK_SECRET, timestamp)
    return payload, sig_header