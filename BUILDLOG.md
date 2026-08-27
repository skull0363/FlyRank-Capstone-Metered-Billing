Where AI helped:

Learning FastAPI. I was new to fastAPI going into this capstone, so I used AI to understand core concepts: dependency injection with Depends(), how path/query/header parameters are declared, pydantic request models and how routers get mounted into the main app. AI walked me through small example snippets which I then adapted into main.py, schemas.py and stripe_routes.py

Connecting to Stripe. I had never integrated Stripe before. AI helped me understand the shape of the Stripe Python SDK — creating a Customer, creating a Checkout Session in subscription mode, and the general webhook-handling pattern stripe.Webhook.construct_event.

Documentation. AI helped me draft and structure README.md (architecture description, setup steps, endpoint table) and parts of DESIGN.md. I reviewed and edited this content against what my code actually does, rather than shipping it unread.

Checking my work. I used AI as a second pair of eyes to sanity-check my logic before considering a phase "done" — for example, walking through my idempotency handling in meter_service.py and my quota boundary logic in quota_service.py to see if the reasoning held up, and asking it to identify gaps against the capstone brief's Definition of Done.

Where AI was wrong, or where its suggestions needed correction:

The initial pricing logic AI helped me sketch used plain floats (0.15, 0.0375, 0.60 per 1,000 tokens) for token pricing. The capstone brief explicitly requires money to be stored as integers, never floats, to avoid rounding drift when many usage events are summed. I rewrote pricing.py to price in integer micro-cents per 1,000,000 tokens instead, and updated main.py to store and sum only integers.

My original quota-check and usage-insert ran as two separate, non-atomic steps, which left a real (if narrow) race condition at the exact quota boundary under concurrent requests. AI's first pass didn't flag this as an issue; I only found it by explicitly stress-testing the "what happens under retries and concurrency" angle the brief calls out, and fixed it by locking the tenant row and running both steps in one transaction in meter_service.py.