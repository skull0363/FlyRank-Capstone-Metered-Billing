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