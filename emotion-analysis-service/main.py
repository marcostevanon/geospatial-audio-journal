from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from typing import Dict, List, Any
import torch
import librosa
import numpy as np
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor, AutoModelForSequenceClassification, AutoTokenizer
from speechbrain.inference.classifiers import EncoderClassifier
import whisper
from pydantic import BaseModel

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextAnalysisRequest(BaseModel):
    text: str

def initialize_models() -> tuple[AutoModelForAudioClassification, AutoFeatureExtractor, EncoderClassifier, whisper.Whisper, AutoModelForSequenceClassification, AutoTokenizer]:
    """Initialize and return all models."""
    # Whisper model (8 emotions)
    whisper_model_id = "firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3"
    whisper_model = AutoModelForAudioClassification.from_pretrained(
        whisper_model_id,
        force_download=False,
        local_files_only=False
    )
    whisper_model.gradient_checkpointing_enable()
    whisper_feature_extractor = AutoFeatureExtractor.from_pretrained(
        whisper_model_id,
        force_download=False,
        local_files_only=False
    )

    # SpeechBrain model (4 emotions)
    speechbrain_model = EncoderClassifier.from_hparams(
        source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
        savedir="pretrained_models/emotion-recognition-wav2vec2-IEMOCAP",
        run_opts={"device": "cpu"},
        use_auth_token="***REMOVED***"
    )

    # Transcription model - using large-v3 for better accuracy
    # "tiny" - 39M parameters (fastest, least accurate)
    # "base" - 74M parameters
    # "small" - 244M parameters
    # "medium" - 769M parameters
    # "large" - 1.5B parameters
    # "large-v2" - 1.5B parameters (improved version)
    # "large-v3" - 1.5B parameters (latest version)
    transcription_model = whisper.load_model("medium")

    # Text emotion analysis model - using MilaNLProc/feel-it for Italian text
    text_emotion_model_id = "MilaNLProc/feel-it-italian-emotion"
    text_emotion_model = AutoModelForSequenceClassification.from_pretrained(
        text_emotion_model_id,
        force_download=False,
        local_files_only=False
    )
    text_emotion_tokenizer = AutoTokenizer.from_pretrained(
        text_emotion_model_id,
        force_download=False,
        local_files_only=False
    )

    return whisper_model, whisper_feature_extractor, speechbrain_model, transcription_model, text_emotion_model, text_emotion_tokenizer

def get_whisper_emotions(
    model: AutoModelForAudioClassification,
    feature_extractor: AutoFeatureExtractor,
    audio_array: np.ndarray,
    sampling_rate: int,
    max_duration: float = 30.0
) -> List[Dict[str, Any]]:
    """Get emotion predictions from Whisper model."""
    # Preprocess audio
    max_length = int(feature_extractor.sampling_rate * max_duration)
    if len(audio_array) > max_length:
        audio_array = audio_array[:max_length]
    else:
        audio_array = np.pad(audio_array, (0, max_length - len(audio_array)))

    inputs = feature_extractor(
        audio_array,
        sampling_rate=feature_extractor.sampling_rate,
        max_length=max_length,
        truncation=True,
        return_tensors="pt",
    )

    # Get predictions
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze().tolist()
    
    # Get top 5 emotions
    top_k = min(5, len(probs))
    top_k_idx = torch.topk(torch.tensor(probs), top_k).indices.tolist()
    
    return [
        {
            "emotion": model.config.id2label[idx],
            "confidence": float(probs[idx]) * 100
        }
        for idx in top_k_idx
    ]

def get_speechbrain_emotions(
    model: EncoderClassifier,
    audio_array: np.ndarray
) -> List[Dict[str, Any]]:
    """Get emotion predictions from SpeechBrain model."""
    # Preprocess audio
    waveform = torch.FloatTensor(audio_array)
    waveform = waveform / waveform.abs().max()
    if waveform.ndim > 1:
        waveform = waveform.mean(dim=1)
    waveform = waveform.unsqueeze(0)
    
    # Get predictions
    wav_lens = torch.tensor([1.0])
    feats = model.mods.wav2vec2(waveform, wav_lens)
    outputs = model.mods.output_mlp(feats)
    probs = torch.nn.functional.softmax(outputs, dim=-1)
    probs = probs.mean(dim=1).squeeze().tolist()
    
    # Get top 5 emotions
    top_k = min(5, len(probs))
    top_k_idx = torch.topk(torch.tensor(probs), top_k).indices.tolist()
    valid_indices = [idx for idx in top_k_idx if idx in model.hparams.label_encoder.ind2lab]
    
    return [
        {
            "emotion": model.hparams.label_encoder.ind2lab[idx],
            "confidence": float(probs[idx]) * 100
        }
        for idx in valid_indices
    ]

def get_transcription(
    model: whisper.Whisper,
    audio_path: str
) -> Dict[str, Any]:
    """Get transcription and language from audio file."""
    # Transcribe audio with improved parameters
    result = model.transcribe(
        audio_path,
        language=None,  # Auto-detect language
        task="transcribe",  # Focus on transcription
        fp16=False,  # Use full precision for better accuracy
        temperature=0.0,  # Reduce randomness
        best_of=5,  # Try multiple samples and pick the best
        beam_size=5,  # Use beam search for better results
        condition_on_previous_text=True,  # Consider previous context
        no_speech_threshold=0.6,  # Higher threshold to avoid false positives
        compression_ratio_threshold=2.4,  # Higher threshold to avoid repetition
        logprob_threshold=-1.0,  # Lower threshold to include more words
    )
    
    return {
        "transcription": result["text"],
        "language": result["language"],
        "segments": [
            {
                "text": segment["text"],
                "start": segment["start"],
                "end": segment["end"],
                "confidence": segment.get("confidence", None)
            }
            for segment in result["segments"]
        ]
    }

def get_text_emotions(
    model: AutoModelForSequenceClassification,
    tokenizer: AutoTokenizer,
    text: str,
    max_length: int = 512
) -> List[Dict[str, Any]]:
    """Get emotion predictions from text using the text emotion model."""
    # Tokenize text
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
        padding=True
    )

    # Get predictions
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze().tolist()
    
    # Get all emotions with their probabilities
    emotions = [
        {
            "emotion": model.config.id2label[i],
            "confidence": float(prob) * 100
        }
        for i, prob in enumerate(probs)
    ]
    
    # Sort by confidence
    emotions.sort(key=lambda x: x["confidence"], reverse=True)
    
    return emotions

# Initialize models
whisper_model, whisper_feature_extractor, speechbrain_model, transcription_model, text_emotion_model, text_emotion_tokenizer = initialize_models()

@app.post("/analyze/audio")
async def analyze_audio(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Analyze audio file for emotions and transcribe it."""
    print("Received audio file for analysis")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()
        
        try:
            print("Loading audio file...")
            # Load audio
            audio_array, sampling_rate = librosa.load(temp_file.name, sr=16000)
            print("Audio file loaded successfully")
            
            print("Analyzing emotions with Whisper model...")
            # Get predictions from both models
            whisper_emotions = get_whisper_emotions(
                whisper_model,
                whisper_feature_extractor,
                audio_array,
                sampling_rate
            )
            print("Whisper emotions analysis completed")
            
            print("Analyzing emotions with SpeechBrain model...")
            speechbrain_emotions = get_speechbrain_emotions(
                speechbrain_model,
                audio_array
            )
            print("SpeechBrain emotions analysis completed")

            print("Starting transcription...")
            # Get transcription
            transcription = get_transcription(
                transcription_model,
                temp_file.name
            )
            print("Transcription completed")
            
            return {
                "whisper_model": {
                    "model": "Whisper Large V3",
                    "emotions": whisper_emotions
                },
                "speechbrain_model": {
                    "model": "SpeechBrain IEMOCAP",
                    "emotions": speechbrain_emotions
                },
                "transcription": transcription
            }
            
        finally:
            os.unlink(temp_file.name)

@app.post("/analyze/text")
async def analyze_text(request: TextAnalysisRequest) -> Dict[str, Any]:
    """Analyze text for emotions."""
    # Get text-based emotions
    text_emotions = get_text_emotions(
        text_emotion_model,
        text_emotion_tokenizer,
        request.text
    )
    
    return {
        "text_emotions": {
            "model": "Feel-It Italian Emotion",
            "emotions": text_emotions
        }
    }