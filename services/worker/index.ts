import { Worker, Job } from 'bullmq';
import { Redis } from 'ioredis';
import admin from 'firebase-admin';
import { getStorage } from 'firebase-admin/storage';
import { getFirestore } from 'firebase-admin/firestore';
import axios from 'axios';
import * as dotenv from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import FormData from 'form-data';

// ESM __dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env or .env.local
dotenv.config(); // Loads .env
dotenv.config({ path: path.join(__dirname, '.env.local') }); // Also try .env.local

// Initialize Firebase Admin
const serviceAccountKey = process.env.FIREBASE_SERVICE_ACCOUNT_KEY;
const serviceAccountPath = process.env.FIREBASE_SERVICE_ACCOUNT_PATH;

let app: admin.app.App;

if (serviceAccountKey || serviceAccountPath) {
  try {
    let serviceAccount;
    if (serviceAccountKey) {
      serviceAccount = JSON.parse(serviceAccountKey);
    } else if (serviceAccountPath) {
      const absolutePath = path.isAbsolute(serviceAccountPath)
        ? serviceAccountPath
        : path.join(process.cwd(), serviceAccountPath);
      serviceAccount = JSON.parse(fs.readFileSync(absolutePath, 'utf8'));
    }

    app = admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      storageBucket: process.env.FIREBASE_STORAGE_BUCKET || '',
    });
    console.log('Firebase Admin initialized.');
  } catch (err) {
    console.error('Failed to initialize Firebase Admin:', err);
    process.exit(1);
  }
} else {
  console.warn('Firebase configuration missing (FIREBASE_SERVICE_ACCOUNT_KEY or FIREBASE_SERVICE_ACCOUNT_PATH).');
}

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const connection = new Redis(REDIS_URL, { maxRetriesPerRequest: null }) as any;

interface AudioAnalysisJob {
  fileUrl: string;
  fileName: string;
  userId?: string;
  docId: string;
  duration?: number;
}

const worker = new Worker('audio-analysis', async (job: Job<AudioAnalysisJob>) => {
  console.log(`Processing job ${job.id} for file: ${job.data.fileName}`);

  try {
    // 1. Download file from Firebase Storage
    const bucket = getStorage().bucket();
    const file = bucket.file(`audio_uploads/${job.data.fileName}`);

    // Create temp path
    const tempDir = path.join(__dirname, 'temp');
    if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir);

    const tempFilePath = path.join(tempDir, job.data.fileName);

    console.log(`Downloading ${job.data.fileName} from Firebase...`);
    await file.download({ destination: tempFilePath });

    console.log(`File downloaded to ${tempFilePath}. Sending to emotion-engine...`);

    // 2. Send to emotion-engine
    const form = new FormData();
    form.append('file', fs.createReadStream(tempFilePath));

    const engineUrl = process.env.EMOTION_ENGINE_URL || 'http://localhost:8000/api/audio/analyze';

    const response = await axios.post(engineUrl, form, {
      headers: { ...(form as any).getHeaders() }
    });

    console.log(`Analysis complete for job ${job.id}.`);

    // 3. Cleanup temp file
    fs.unlinkSync(tempFilePath);

    console.log(response.data)

    // 4. Update results in Firestore
    const db = getFirestore();
    const updateData = {
      duration: response.data.duration || job.data.duration || 0, // Fallback to provided duration if backend doesn't return
      emotions: response.data.emotions || {},
      transcript: response.data.transcription || '',
      language: response.data.language || '',
      status: 'completed'
    };

    if (job.data.docId) {
      await db.collection('voice_notes').doc(job.data.docId).update(updateData);
      console.log(`Updated Firestore doc: ${job.data.docId}`);
      return { ...response.data, firestoreId: job.data.docId };
    } else {
      // Fallback for old queued jobs without docId
      const voiceNoteData = {
        fileName: job.data.fileName,
        fileUrl: job.data.fileUrl,
        userId: job.data.userId || 'anonymous',
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        ...updateData
      };
      const docRef = await db.collection('voice_notes').add(voiceNoteData);
      console.log(`Saved new analysis to Firestore with ID: ${docRef.id}`);
      return { ...response.data, firestoreId: docRef.id };
    }
  } catch (error) {
    console.error(`Failed to process job ${job.id}:`, error);
    throw error;
  }
}, { connection });

worker.on('completed', (job: Job) => {
  console.log(`Job ${job.id} has completed!`);
});

worker.on('failed', (job: Job | undefined, err: Error) => {
  console.log(`Job ${job?.id} has failed with ${err.message}`);
});

console.log('Worker started and listening on audio-analysis queue.');
