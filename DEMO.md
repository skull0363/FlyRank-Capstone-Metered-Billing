Call /generate repeatedly until the seeded tenant hits its quota → show the clean 429 with an explanatory message.

Retry the same request with the same idempotency key → show only one row in usage_events for that key.

Run stripe listen in one terminal, hit /billing/checkout, complete the test Checkout with card 4242 4242 4242 4242 → watch the webhook flip the tenant to pro.

Send a forged signature to /webhooks/stripe → 400. Run stripe trigger checkout.session.completed twice → second one logs already_processed.

Finish on GET /usage showing used/limit/cost, with pytest green on screen.

Close with: "usage, money, and customer access stay correct under retries, failures, and real-world conditions."

uvicorn app.main:app --reload          # run
python -m app.seed                     # seed demo tenant near quota
pytest -q                              # run tests
stripe listen --forward-to localhost:8000/webhooks/stripe
stripe trigger checkout.session.completed