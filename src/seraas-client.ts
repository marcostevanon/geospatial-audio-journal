import axios from 'axios';
import * as fs from 'fs';
import FormData from 'form-data';
import { EmotionAnalysis } from './types';

const SERAAS_URL = 'http://127.0.0.1:8000/analyze/';

/**
 * Sends an audio file to the local FastAPI SERaaS microservice and returns emotion analysis results.
 * @param audioPath Path to the audio file (ogg or wav)
 * @returns Object containing emotion analysis from both Whisper and SpeechBrain models
 */
export async function getEmotionsFromPython(audioPath: string): Promise<EmotionAnalysis> {
  // Check if file exists
  if (!fs.existsSync(audioPath)) {
    throw new Error(`Audio file not found: ${audioPath}`);
  }

  const formData = new FormData();
  formData.append('file', fs.createReadStream(audioPath));

  try {
    const response = await axios.post(SERAAS_URL, formData, {
      headers: formData.getHeaders(),
      timeout: 30000, // 30 second timeout
    });

    return response.data as EmotionAnalysis;
  } catch (error) {
    // Simple error handling - just pass through the error message
    throw new Error(`Failed to analyze emotions: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
} 