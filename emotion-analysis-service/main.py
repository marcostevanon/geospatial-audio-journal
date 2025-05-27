from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from typing import Dict, List, Any
import torch
import librosa
import numpy as np
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
from speechbrain.inference.classifiers import EncoderClassifier

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def initialize_models() -> tuple[AutoModelForAudioClassification, AutoFeatureExtractor, EncoderClassifier]:
    """Initialize and return both emotion recognition models."""
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

    return whisper_model, whisper_feature_extractor, speechbrain_model

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

# Initialize models
whisper_model, whisper_feature_extractor, speechbrain_model = initialize_models()

@app.post("/analyze/")
async def analyze(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Analyze audio file for emotions using both models."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()
        
        try:
            # Load audio
            audio_array, sampling_rate = librosa.load(temp_file.name, sr=16000)
            
            # Get predictions from both models
            whisper_emotions = get_whisper_emotions(
                whisper_model,
                whisper_feature_extractor,
                audio_array,
                sampling_rate
            )
            
            speechbrain_emotions = get_speechbrain_emotions(
                speechbrain_model,
                audio_array
            )
            
            return {
                "whisper_model": {
                    "model": "Whisper Large V3",
                    "emotions": whisper_emotions
                },
                "speechbrain_model": {
                    "model": "SpeechBrain IEMOCAP",
                    "emotions": speechbrain_emotions
                }
            }
            
        finally:
            os.unlink(temp_file.name) 