import dotenv from 'dotenv';
import { Config } from './types';

dotenv.config();

const requiredEnvVars = ['API_ID', 'API_HASH', 'PHONE_NUMBER', 'TARGET_CHAT_ID'] as const;

function validateConfig(): void {
  for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
      throw new Error(`Missing required environment variable: ${envVar}`);
    }
  }

  // Validate API_ID is a number
  const apiId = Number(process.env.API_ID);
  if (isNaN(apiId)) {
    throw new Error('API_ID must be a number');
  }
}

export const config: Config = {
  apiId: Number(process.env.API_ID),
  apiHash: process.env.API_HASH as string,
  phoneNumber: process.env.PHONE_NUMBER as string,
  password: process.env.PASSWORD,
  sessionString: process.env.SESSION_STRING,
  targetChatId: process.env.TARGET_CHAT_ID as string,
};

// Validate configuration on startup
validateConfig(); 