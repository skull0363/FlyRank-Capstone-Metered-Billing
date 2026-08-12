import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding initial capstone data...');

  // Create test tenant
  const tenant = await prisma.tenant.upsert({
    where: { id: 'test-tenant-1' },
    update: {},
    create: {
      id: 'test-tenant-1',
      name: 'Acme Corp',
      subscription: {
        create: {
          plan: 'FREE',
          status: 'active',
        },
      },
    },
  });

  console.log(`Seeded tenant: ${tenant.name} (${tenant.id})`);
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });