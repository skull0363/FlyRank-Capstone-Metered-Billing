import { PrismaClient } from '@prisma/client';
import { PLAN_LIMITS } from '../config/pricing.js';

const prisma = new PrismaClient();

export async function recordUsage({ tenantId, type, quantity, idempotencyKey }) {
  // 1. Idempotency Check: Return existing record if key exists
  const existingEvent = await prisma.usageEvent.findUnique({
    where: { idempotencyKey }
  });
  if (existingEvent) {
    return { status: 'DUPLICATE', event: existingEvent };
  }

  // 2. Fetch Tenant Subscription & Limits
  const sub = await prisma.subscription.findUnique({ where: { tenantId } });
  const plan = sub ? sub.plan : 'FREE';
  const limits = PLAN_LIMITS[plan];

  // 3. Quota Enforcement Check
  const startOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
  const aggregate = await prisma.usageEvent.aggregate({
    _sum: { quantity: true },
    where: { tenantId, type, createdAt: { gte: startOfMonth } }
  });
  
  const currentUsage = aggregate._sum.quantity || 0;
  const maxAllowed = type === 'API_CALL' ? limits.apiCalls : limits.aiTokens;

  if (currentUsage + quantity > maxAllowed) {
    const error = new Error(`Quota limit reached for ${type}. Limit: ${maxAllowed}`);
    error.statusCode = plan === 'FREE' ? 429 : 402; // 429 Too Many Requests or 402 Payment Required
    throw error;
  }

  // 4. Record Usage Event Safely
  const event = await prisma.usageEvent.create({
    data: { tenantId, type, quantity, idempotencyKey }
  });

  return { status: 'CREATED', event };
}