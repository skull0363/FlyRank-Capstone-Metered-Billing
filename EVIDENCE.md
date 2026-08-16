# EVIDENCE.md

One pasted proof per Definition-of-Done checkbox (brief §6). Replace every `<PASTE HERE>` with a real test name + output, a curl transcript, or a log line. Claims without evidence score as not done — do not leave placeholders in your final submission.

---

## METERING

### ✅ A billable action creates exactly one usage event, even under retries — deduplicated by idempotency key

### ✅ A test proves double-counting cannot happen

---

## QUOTAS

### ✅ Usage is checked against the tenant's plan; requests over the limit are rejected

### ✅ Responses carry the correct status codes (429/402) and a message explaining why

---

## COST CALCULATION

### ✅ Monthly usage rolls up into a cost figure per tenant

### ✅ AI token pricing handles cached input tokens, reasoning tokens, and output pricing correctly

### ✅ Pricing constants are pinned and covered by tests

---

## STRIPE INTEGRATION

### ✅ Subscription checkout works end-to-end in Stripe test mode

### ✅ Webhooks verify signatures, ignore duplicate events, and update tenant plan/status

---

## DATA MODEL, TESTS & DOCUMENTATION

### ✅ Database includes tenants, plans, subscriptions, and usage events; customer data isolated per tenant

### ✅ Tests cover: duplicate usage prevention, quota boundary cases (at / just under / over), cost calculations, invalid-webhook rejection, duplicate-webhook handling

### ✅ README + architecture diagram + setup instructions; submission-pack files present
