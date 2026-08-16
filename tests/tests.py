# tests/test_metering.py
def test_duplicate_idempotency_key_creates_one_event(client, tenant):
    r1 = client.post("/generate", json={"tenant_id": tenant.id},
                      headers={"idempotency-key": "abc123"})
    r2 = client.post("/generate", json={"tenant_id": tenant.id},
                      headers={"idempotency-key": "abc123"})
    assert r1.json()["usage_event_id"] == r2.json()["usage_event_id"]

# tests/test_quota.py
def test_at_limit_allowed_over_limit_rejected(client, tenant_at_999_calls):
    ok = client.post("/generate", json={"tenant_id": tenant_at_999_calls.id},
                      headers={"idempotency-key": "call-1000"})
    assert ok.status_code == 200
    blocked = client.post("/generate", json={"tenant_id": tenant_at_999_calls.id},
                           headers={"idempotency-key": "call-1001"})
    assert blocked.status_code == 429

# tests/test_pricing.py
def test_cached_input_cheaper_than_fresh_input():
    from app.pricing import calculate_cost
    fresh = calculate_cost({"input_tokens": 1000, "cached_input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0})
    cached = calculate_cost({"input_tokens": 0, "cached_input_tokens": 1000, "output_tokens": 0, "reasoning_tokens": 0})
    assert cached < fresh

def test_reasoning_tokens_priced_as_output():
    from app.pricing import calculate_cost
    a = calculate_cost({"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 1000, "reasoning_tokens": 0})
    b = calculate_cost({"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 1000})
    assert a == b

# tests/test_webhooks.py
def test_forged_signature_rejected(client):
    r = client.post("/webhooks/stripe", data=b"{}", headers={"stripe-signature": "bad"})
    assert r.status_code == 400

def test_duplicate_webhook_processed_once(client, valid_stripe_event_payload_and_sig):
    payload, sig = valid_stripe_event_payload_and_sig
    r1 = client.post("/webhooks/stripe", data=payload, headers={"stripe-signature": sig})
    r2 = client.post("/webhooks/stripe", data=payload, headers={"stripe-signature": sig})
    assert r1.status_code == 200 and r2.json()["status"] == "already_processed"