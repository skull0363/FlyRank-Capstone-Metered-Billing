from app.db import SessionLocal, init_db
from app.models import Tenant, UsageEvent

def seed():
    init_db()
    db = SessionLocal()
    tenant = Tenant(name="Acme Corp", plan="free", status="active")
    db.add(tenant)
    db.commit()
    for i in range(999):
        db.add(UsageEvent(tenant_id=tenant.id, usage_type="api_call", quantity=1,
                           idempotency_key=f"seed-{i}"))
    db.commit()
    print(f"Seeded tenant {tenant.id} at 999/1000 API calls")

if __name__ == "__main__":
    seed()