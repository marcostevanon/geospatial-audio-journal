import axios from 'axios';
import * as fs from 'fs';
import FormData from 'form-data';
import { EmotionAnalysis, AudioAnalysis, TextAnalysis } from './types';

const SERAAS_URL = 'http://127.0.0.1:8000';

/**
 * Sends an audio file to the local FastAPI SERaaS microservice and returns emotion analysis results.
 * @param audioPath Path to the audio file (ogg or wav)
 * @returns Object containing emotion analysis from both Whisper and SpeechBrain models
 */
export async function getEmotionsFromPython(audioPath: string): Promise<AudioAnalysis> {
  // Check if file exists
  if (!fs.existsSync(audioPath)) {
    throw new Error(`Audio file not found: ${audioPath}`);
  }

  const formData = new FormData();
  formData.append('file', fs.createReadStream(audioPath));

  console.log("Sending audio file for analysis...");
  try {
    const response = await axios.post(`${SERAAS_URL}/analyze/audio`, formData, {
      headers: formData.getHeaders(),
      timeout: 220000, // 2 minute timeout
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
        console.log(`Upload progress: ${percentCompleted}%`);
      },
    });

    console.log("Analysis completed successfully");
    return response.data as AudioAnalysis;
  } catch (error) {
    if (error instanceof Error && error.message.includes('timeout')) {
      throw new Error('Audio analysis is taking longer than expected. Please try again with a shorter audio file or wait longer.');
    }
    throw new Error(`Failed to analyze audio: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Sends text to the local FastAPI SERaaS microservice and returns emotion analysis results.
 * @param text Text to analyze
 * @returns Object containing text emotion analysis
 */
export async function getTextEmotionsFromPython(text: string): Promise<TextAnalysis> {
  console.log("Sending text for analysis...");
  try {
    const response = await axios.post(`${SERAAS_URL}/analyze/text`, {
      text: text
    }, {
      timeout: 10000, // 10 second timeout
    });

    console.log("Text analysis completed successfully");
    return response.data as TextAnalysis;
  } catch (error) {
    throw new Error(`Failed to analyze text: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
} 