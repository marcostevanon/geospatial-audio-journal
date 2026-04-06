import { Timestamp } from 'firebase/firestore';

export interface VoiceNote {
  id: string;
  fileName: string;
  fileUrl: string;
  userId: string;
  createdAt: Timestamp | Date | null;
  duration: number;
  emotions: Record<string, number>;
  transcript: string;
  language: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

export interface AudioAnalysisJob {
  fileUrl: string;
  fileName: string;
  userId?: string;
  docId: string;
  duration?: number;
}

export interface AudioAnalysisResponse {
  duration?: number;
  emotions?: Record<string, number>;
  transcription?: string;
  language?: string;
  error?: string;
}