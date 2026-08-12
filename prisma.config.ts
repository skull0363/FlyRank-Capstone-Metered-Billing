import { defineConfig } from '@prisma/config';
import 'dotenv/config'; // Ensures .env is loaded

export default defineConfig({
  datasource: {
    url: process.env.DATABASE_URL,
  },
  migrations: {
    seed: 'npx tsx prisma/seed.ts',
  },
});