from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
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

# Initialize both models
# Whisper model (8 emotions)
whisper_model_id = "firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3"
whisper_model = AutoModelForAudioClassification.from_pretrained(whisper_model_id)
whisper_feature_extractor = AutoFeatureExtractor.from_pretrained(whisper_model_id, do_normalize=True)
whisper_id2label = whisper_model.config.id2label

# SpeechBrain model (4 emotions)
speechbrain_model = EncoderClassifier.from_hparams(
    source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
    savedir="pretrained_models/emotion-recognition-wav2vec2-IEMOCAP",
    run_opts={"device": "cpu"},
    use_auth_token="***REMOVED***"
)

def preprocess_audio_whisper(audio_array, sampling_rate, max_duration=30.0):
    max_length = int(whisper_feature_extractor.sampling_rate * max_duration)
    if len(audio_array) > max_length:
        audio_array = audio_array[:max_length]
    else:
        audio_array = np.pad(audio_array, (0, max_length - len(audio_array)))

    inputs = whisper_feature_extractor(
        audio_array,
        sampling_rate=whisper_feature_extractor.sampling_rate,
        max_length=max_length,
        truncation=True,
        return_tensors="pt",
    )
    return inputs

@app.post("/analyze/")
async def analyze(file: UploadFile = File(...)):
    # Create a temporary file to store the uploaded audio
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()
        
        try:
            # Load audio using librosa
            audio_array, sampling_rate = librosa.load(temp_file.name, sr=16000)
            
            # Whisper model prediction
            whisper_inputs = preprocess_audio_whisper(audio_array, sampling_rate)
            with torch.no_grad():
                whisper_outputs = whisper_model(**whisper_inputs)
            whisper_probs = torch.nn.functional.softmax(whisper_outputs.logits, dim=-1).squeeze().tolist()
            top_k_whisper = min(5, len(whisper_probs))
            top_k_idx_whisper = torch.topk(torch.tensor(whisper_probs), top_k_whisper).indices.tolist()
            
            whisper_emotions = [
                {
                    "emotion": whisper_id2label[idx],
                    "confidence": float(whisper_probs[idx]) * 100
                }
                for idx in top_k_idx_whisper
            ]
            
            # SpeechBrain model prediction
            waveform = torch.FloatTensor(audio_array)
            waveform = waveform / waveform.abs().max()
            if waveform.ndim > 1:
                waveform = waveform.mean(dim=1)
            waveform = waveform.unsqueeze(0)
            
            wav_lens = torch.tensor([1.0])
            feats = speechbrain_model.mods.wav2vec2(waveform, wav_lens)
            outputs = speechbrain_model.mods.output_mlp(feats)
            probs = torch.nn.functional.softmax(outputs, dim=-1)
            probs = probs.mean(dim=1).squeeze().tolist()
            
            top_k_speechbrain = min(5, len(probs))
            top_k_idx_speechbrain = torch.topk(torch.tensor(probs), top_k_speechbrain).indices.tolist()
            valid_indices = [idx for idx in top_k_idx_speechbrain if idx in speechbrain_model.hparams.label_encoder.ind2lab]
            
            speechbrain_emotions = [
                {
                    "emotion": speechbrain_model.hparams.label_encoder.ind2lab[idx],
                    "confidence": float(probs[idx]) * 100
                }
                for idx in valid_indices
            ]
            
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
            # Clean up the temporary file
            os.unlink(temp_file.name) 