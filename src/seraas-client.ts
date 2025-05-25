import axios from 'axios';
import * as fs from 'fs';
import FormData from 'form-data';

interface EmotionAnalysis {
  whisper_model: {
    model: string;
    emotions: {
      emotion: string;
      confidence: number;
    }[];
  };
  speechbrain_model: {
    model: string;
    emotions: {
      emotion: string;
      confidence: number;
    }[];
  };
}

/**
 * Sends an audio file to the local FastAPI SERaaS microservice and returns emotion analysis results.
 * @param audioPath Path to the audio file (ogg or wav)
 * @returns Object containing emotion analysis from both Whisper and SpeechBrain models
 */
export async function getEmotionsFromPython(audioPath: string): Promise<EmotionAnalysis> {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(audioPath));
  const response = await axios.post('http://127.0.0.1:8000/analyze/', formData, {
    headers: formData.getHeaders(),
  });
  return response.data;
} 