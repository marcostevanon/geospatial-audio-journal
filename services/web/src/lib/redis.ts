import { Queue } from 'bullmq';
import { Redis } from 'ioredis';

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

// We pass the connection URL directly to BullMQ options.
// This avoids type mismatches between multiple versions of ioredis in node_modules.
export const audioQueue = new Queue('audio-analysis', {
  connection: new Redis(REDIS_URL, {
    maxRetriesPerRequest: null,
  }) as any
});
