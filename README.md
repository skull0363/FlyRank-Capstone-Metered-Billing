# Usage Metering & Billing Engine

A backend service that answers the three questions every SaaS product must answer: how much has this customer used, what does it cost, and have they hit their limit. Built for the FlyRank Internship Backend Track capstone.

It meters usage idempotently, enforces per-plan quotas with honest `429`/`402` responses, calculates cost using real-world AI token pricing rules (cached input tokens, reasoning tokens, non-additive categories), and syncs subscription state from Stripe via signature-verified, deduplicated webhooks.

## What it does

- **Meters usage** for two billable types — API calls and AI tokens — attributed per tenant, with exactly-once recording under retries via an idempotency key.
- **Enforces quotas** before allowing a billable action: `429 Too Many Requests` when a usage limit is exceeded, `402 Payment Required` when the tenant's subscription itself is not active.
- **Calculates cost** for token usage using pinned pricing constants: cached input tokens are billed cheaper than fresh input, reasoning tokens are billed as output tokens, and categories are never simply summed together.
- **Integrates Stripe (test mode only)** for subscription checkout and keeps the tenant's plan/status in sync purely through verified webhook events — no real money ever moves.

## Architecture

**Layers:** HTTP routes (`app/main.py`, `app/stripe_routes.py`) → services (`meter_service.py`, `quota_service.py`, `pricing.py`) → persistence (`models.py`, `db.py`). Business logic never talks to Stripe or the DB driver directly — swapping SQLite for Postgres or adding a new payment provider should not touch `meter_service.py` or `quota_service.py`.

## Data model

| Table | Purpose |
|---|---|
| `tenants` | One row per customer org: current plan, subscription status, Stripe customer/subscription IDs |
| `plans` | Plan name → quota limits (API calls / month, tokens / month) |
| `usage_events` | One row per billable action: tenant, type, quantity, token breakdown, idempotency key (unique per tenant) |
| `processed_webhook_events` | Stripe event IDs already applied, so replays are ignored |

## Setup — runs on a clean machine

```bash
git clone <this-repo-url>
cd flyrank-capstone-metering-billing
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in your own Stripe TEST secret key, webhook secret, and price ID
```

Run the service:
```bash
uvicorn app.main:app --reload
```

Seed a demo tenant sitting one call away from its quota:
```bash
python -m app.seed
```

Run the test suite:
```bash
pytest -q
```

Forward Stripe webhooks locally (needs the free Stripe CLI, no tunnel or public URL required):
```bash
stripe login
stripe listen --forward-to localhost:8000/webhooks/stripe
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/generate` | Dummy billable action — records usage, checks quota, returns cost |
| GET | `/usage?tenant_id=` | Rollup: used / limit / cost for a tenant |
| POST | `/billing/checkout?tenant_id=` | Creates a Stripe Checkout session (test mode) |
| POST | `/webhooks/stripe` | Receives and verifies Stripe webhook events |

## Try it

```bash
# Hit quota boundary
curl -X POST http://localhost:8000/generate -H "idempotency-key: k1" -d '{"tenant_id":"<id>"}'

# Retry with same key — no double count
curl -X POST http://localhost:8000/generate -H "idempotency-key: k1" -d '{"tenant_id":"<id>"}'

# Check rollup
curl http://localhost:8000/usage?tenant_id=<id>
```

Test card for Checkout: `4242 4242 4242 4242`, any future expiry, any CVC. Test mode moves no real money and requires no card on your Stripe account.

## Limitations (honest, by design)

- No proration, invoicing, or overage billing in the core — these are documented stretch goals only.
- AI token counts are simulated; the service meters numbers, it does not call a real model.
- Single-region, single-process design — no distributed idempotency lock beyond the database's unique constraint, which is sufficient at this scale but would need revisiting under high concurrent write volume.
- Quota check and usage recording are not wrapped in a single DB transaction with row-level locking, so a very tight race at the exact boundary could theoretically admit one extra event; the idempotency-key constraint still guarantees no *duplicate* event from retries.

## Evidence and AI usage

See `EVIDENCE.md` for a pasted proof per Definition-of-Done checkbox, and `BUILDLOG.md` for an honest log of where AI tools helped during the build and what was changed.