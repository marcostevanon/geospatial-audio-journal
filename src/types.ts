export interface EmotionAnalysis {
  whisper_model: {
    model: string;
    emotions: Emotion[];
  };
  speechbrain_model: {
    model: string;
    emotions: Emotion[];
  };
  transcription: Transcription;
}

export interface TextAnalysis {
  text_emotions: {
    model: string;
    emotions: Emotion[];
  };
}

export interface Emotion {
  emotion: string;
  confidence: number;
}

export interface Transcription {
  transcription: string;
  language: string;
  segments: TranscriptionSegment[];
}

export interface TranscriptionSegment {
  text: string;
  start: number;
  end: number;
  confidence: number | null;
}

export interface AudioAnalysis {
  whisper_model: {
    model: string;
    emotions: Emotion[];
  };
  speechbrain_model: {
    model: string;
    emotions: Emotion[];
  };
  transcription: Transcription;
}

export interface Config {
  apiId: number;
  apiHash: string;
  phoneNumber: string;
  password?: string;
  sessionString?: string;
  targetChatId: string;
} 