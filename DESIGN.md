app/
  __init__.py
  main.py              # FastAPI app + routes
  config.py            # settings from .env
  db.py                # engine/session
  models.py            # SQLAlchemy models
  schemas.py           # Pydantic request/response models
  meter_service.py      # idempotent recording
  quota_service.py      # quota checks
  pricing.py            # token/cost math + constants
  stripe_routes.py      # checkout + webhook
  seed.py               # demo data seeding
tests/
  test_metering.py
  test_quota.py
  test_pricing.py
  test_webhooks.py

Known limitations (see also README.md)
Running on SQLite locally, the row lock in meter_service.py (with_for_update()) is a no-op — real concurrent-write protection at the quota boundary requires Postgres, which is the documented $0-stack recommendation for anything beyond local dev.

AI token counts are simulated inputs to /generate, not real model calls — this service meters and prices numbers, it does not call an LLM.

No proration, invoicing, or overage billing in the core; these remain optional stretch goals.