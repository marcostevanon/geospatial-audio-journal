export interface EmotionAnalysis {
  whisper_model: {
    model: string;
    emotions: Emotion[];
  };
  speechbrain_model: {
    model: string;
    emotions: Emotion[];
  };
}

export interface Emotion {
  emotion: string;
  confidence: number;
}

export interface AudioAnalysis {
  duration: number;
  bitrate: number;
  sampleRate: number;
  channels: number;
  codec: string;
  format: string;
  size: number;
  waveform?: number[];
  emotions?: EmotionAnalysis;
}

export interface Config {
  apiId: number;
  apiHash: string;
  phoneNumber: string;
  password?: string;
  sessionString?: string;
  targetChatId: string;
} 