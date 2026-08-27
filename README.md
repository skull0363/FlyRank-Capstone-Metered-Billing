Usage metering & billing engine

A backend service that answers the three questions every SaaS product must answer: how much has this customer used, what does it cost, and have they hit their limit. Built for the FlyRank Internship Backend Track capstone.

It meters usage idempotently, enforces per-plan quotas with honest 429/402 responses, calculates cost using real-world AI token pricing rules (cached input tokens, reasoning tokens, non-additive categories) stored entirely in integer micro-cents, and syncs subscription state from Stripe via signature-verified, deduplicated webhooks.

What it does
Meters usage for two billable types — API calls and AI tokens — attributed per tenant, with exactly-once recording under retries via an idempotency key.

Enforces quotas before allowing a billable action: 429 Too Many Requests when a usage limit is exceeded, 402 Payment Required when the tenant's subscription itself is not active. Quota-check and usage-recording run inside one transaction with a row lock, closing the race condition that a purely sequential check-then-write would leave open.

Calculates cost for token usage using pinned pricing constants stored as integers (micro-cents), never floats: cached input tokens are billed cheaper than fresh input, reasoning tokens are billed as output tokens, and categories are never simply summed together.

Integrates Stripe (test mode only) for subscription checkout and keeps the tenant's plan/status in sync purely through verified webhook events — no real money ever moves. Checkout requires the caller to confirm the tenant they're billing via an X-Tenant-Id header.


Setup for a clean machine: 

git clone <this-repo-url>
cd flyrank-capstone-metering-billing
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in your own Stripe TEST secret key, webhook secret, and price ID

Run the service:
uvicorn app.main:app --reload

Seed a demo tenant sitting one call away from its quota:
python -m app.seed


Run the test suite:
Pytest -q

Forward stripe webhooks locally (needs the free stripe CLI, no tunnel or public URL required):
stripe login
stripe listen --forward-to localhost:8000/webhooks/stripe

Example:
# Hit quota boundary
curl -X POST http://localhost:8000/generate \
  -H "idempotency-key: k1" -H "Content-Type: application/json" \
  -d '{"tenant_id":"<id>"}'

# Retry with same key — no double count
curl -X POST http://localhost:8000/generate \
  -H "idempotency-key: k1" -H "Content-Type: application/json" \
  -d '{"tenant_id":"<id>"}'

# Check rollup
curl http://localhost:8000/usage?tenant_id=<id>

# Start a Checkout session — X-Tenant-Id must match the tenant_id you're billing
curl -X POST "http://localhost:8000/billing/checkout?tenant_id=<id>" \
  -H "X-Tenant-Id: <id>"