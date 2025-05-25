import dotenv from 'dotenv';

dotenv.config();

export const config = {
  apiId: process.env.API_ID,
  apiHash: process.env.API_HASH,
  phoneNumber: process.env.PHONE_NUMBER,
  password: process.env.PASSWORD,
  sessionString: process.env.SESSION_STRING,
  targetChatId: process.env.TARGET_CHAT_ID,
};

// Validate required environment variables
const requiredEnvVars = ['API_ID', 'API_HASH', 'PHONE_NUMBER'];
for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(`Missing required environment variable: ${envVar}`);
  }
} 