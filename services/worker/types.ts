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