import { Queue, QueueOptions } from "bullmq";
import Redis from "ioredis";

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";

const redisConnection = new Redis(REDIS_URL, { maxRetriesPerRequest: null });

export const audioQueue = new Queue("audio-analysis", {
  connection: redisConnection,
} as QueueOptions);
