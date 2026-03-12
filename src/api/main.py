from openai import OpenAI
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from typing import Dict, List, Any
import torch
import librosa
import numpy as np
from transformers import (
    AutoModelForAudioClassification, 
    AutoFeatureExtractor, 
    AutoModelForSequenceClassification, 
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline
)
from speechbrain.inference.classifiers import EncoderClassifier
import whisper
from pydantic import BaseModel
import json
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def initialize_models() -> tuple[AutoModelForAudioClassification, AutoFeatureExtractor, EncoderClassifier, whisper.Whisper, AutoModelForSequenceClassification, AutoTokenizer, pipeline]:
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

    # MilaNLProc/feel-it-italian-emotion
    # bhadresh-savani/bert-base-uncased-emotion
    text_emotion_model_id = "bhadresh-savani/bert-base-uncased-emotion"
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

    # Initialize local GPT model
    # Using a smaller model that can run efficiently on CPU
    gpt_model_id = "facebook/opt-125m"  # 125M parameters instead of 7B
    logger.info(f"Loading local GPT model: {gpt_model_id}")
    
    # Initialize tokenizer and model separately for better control
    tokenizer = AutoTokenizer.from_pretrained(gpt_model_id)
    
    # Check if CUDA is available
    if torch.cuda.is_available():
        logger.info("GPU found. Loading model with GPU optimizations.")
        model = AutoModelForCausalLM.from_pretrained(
            gpt_model_id,
            device_map="auto",
            torch_dtype=torch.float16
        )
    else:
        logger.info("No GPU found. Loading model in CPU mode with optimizations.")
        model = AutoModelForCausalLM.from_pretrained(
            gpt_model_id,
            device_map="auto",
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )
        # Enable model optimizations for CPU
        model.eval()  # Set to evaluation mode
        torch.set_num_threads(4)  # Limit CPU threads to prevent overload
    
    gpt_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device_map="auto",
        max_new_tokens=128,  # Even shorter responses for faster processing
        do_sample=False,  # Disable sampling for faster inference
        num_beams=1,  # Use greedy decoding
        temperature=1.0,  # Disable temperature scaling
        top_p=1.0,  # Disable top-p sampling
        repetition_penalty=1.0  # Disable repetition penalty
    )
    logger.info("Local GPT model loaded successfully")

    return whisper_model, whisper_feature_extractor, speechbrain_model, transcription_model, text_emotion_model, text_emotion_tokenizer, gpt_pipeline

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
whisper_model, whisper_feature_extractor, speechbrain_model, transcription_model, text_emotion_model, text_emotion_tokenizer, gpt_pipeline = initialize_models()

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

def get_local_gpt_response(prompt: str, max_length: int = 128) -> str:
    """Get response from local GPT model."""
    logger.info("Generating response from local GPT model")
    try:
        # Format the prompt for the model
        formatted_prompt = f"User: {prompt}\nAssistant:"
        
        # Generate response with optimized parameters
        response = gpt_pipeline(
            formatted_prompt,
            max_new_tokens=max_length,
            num_return_sequences=1,
            do_sample=False,  # Use greedy decoding for speed
            num_beams=1,  # Disable beam search
            temperature=1.0,  # Disable temperature scaling
            top_p=1.0,  # Disable top-p sampling
            repetition_penalty=1.0,  # Disable repetition penalty
            pad_token_id=gpt_pipeline.tokenizer.eos_token_id,
            eos_token_id=gpt_pipeline.tokenizer.eos_token_id
        )
        
        # Extract and clean the response
        generated_text = response[0]['generated_text']
        # Remove the prompt from the response
        response_text = generated_text[len(formatted_prompt):].strip()
        
        logger.info("Successfully generated response from local GPT model")
        return response_text
    except Exception as e:
        logger.error(f"Error generating response from local GPT model: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def correct_transcription_gpt4(transcription: str) -> str:
    """Correct transcription errors using local GPT model."""
    logger.info("Starting transcription correction")
    prompt = (
        "You are an expert audio transcription proofreader. Your task is to correct only transcription errors "
        "in the following text. Rules:\n"
        "1. Only fix obvious transcription errors (misheard words, spelling, grammar, or punctuation)\n"
        "2. Keep all foreign words, names, and technical terms exactly as they appear\n"
        "3. Do not modify the text to make it more idiomatic\n"
        "4. If a word is unclear, keep it as is\n"
        "5. Do not add, omit, or paraphrase parts of the text\n\n"
        f"Text to correct:\n{transcription}\n\n"
        "Corrected text:"
    )
    
    try:
        response = get_local_gpt_response(prompt)
        logger.info(f"Raw response: {response}")
        
        # Clean up the response
        corrected_text = response.strip()
        # Remove any potential JSON formatting if present
        if corrected_text.startswith('{') and corrected_text.endswith('}'):
            try:
                json_response = json.loads(corrected_text)
                if isinstance(json_response, dict) and "corrected_text" in json_response:
                    corrected_text = json_response["corrected_text"]
            except json.JSONDecodeError:
                pass
        
        # If the response is empty or just contains the example, return original
        if not corrected_text or corrected_text == "<corrected text here>":
            logger.warning("Model returned empty or example response, using original text")
            return transcription
            
        return corrected_text
    except Exception as e:
        logger.error(f"Error in transcription correction: {str(e)}")
        logger.error(traceback.format_exc())
        return transcription

def get_text_emotions_gpt4(text: str) -> dict:
    """Get emotion analysis using local GPT model."""
    logger.info("Starting emotion analysis")
    prompt = (
        "Analyze the emotions in this text and provide a single JSON response with percentages for each emotion. "
        "The emotions to analyze are: sadness, joy, love, surprise, fear, and anger. "
        "The percentages should sum to 100.\n\n"
        f"Text to analyze:\n{text}\n\n"
        "Respond with ONLY a JSON object in this exact format, with no additional text:\n"
        '{"sadness": 20, "joy": 30, "love": 10, "surprise": 15, "fear": 15, "anger": 10}'
    )
    
    try:
        response = get_local_gpt_response(prompt)
        logger.info(f"Raw response: {response}")
        
        # Parse JSON response
        try:
            # Clean up the response to ensure it's valid JSON
            response = response.strip()
            # Find the first { and last }
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                response = response[start_idx:end_idx]
                
            response_content = json.loads(response)
            if not isinstance(response_content, dict):
                raise ValueError("Response is not a dictionary")
                
            # Validate required emotions
            required_emotions = ["sadness", "joy", "love", "surprise", "fear", "anger"]
            missing_emotions = [emotion for emotion in required_emotions if emotion not in response_content]
            if missing_emotions:
                raise ValueError(f"Missing emotions: {missing_emotions}")
                
            # Ensure all values are numbers and sum to 100
            total = 0
            for emotion in required_emotions:
                if not isinstance(response_content[emotion], (int, float)):
                    response_content[emotion] = 0
                total += response_content[emotion]
            
            # Normalize to sum to 100 if needed
            if total != 100 and total > 0:
                for emotion in required_emotions:
                    response_content[emotion] = round((response_content[emotion] / total) * 100)
                    
            return response_content
        except json.JSONDecodeError:
            # If JSON parsing fails, return default values
            logger.warning("Failed to parse emotion analysis response, using default values")
            return {
                "sadness": 20, "joy": 20, "love": 20,
                "surprise": 20, "fear": 10, "anger": 10
            }
    except Exception as e:
        logger.error(f"Error in emotion analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "sadness": 20, "joy": 20, "love": 20,
            "surprise": 20, "fear": 10, "anger": 10
        }

def correct_and_analyze_emotions(transcription: str) -> dict:
    """Correct transcription and analyze emotions."""
    logger.info("Starting combined transcription correction and emotion analysis")
    try:
        corrected_text = correct_transcription_gpt4(transcription)
        logger.info("Transcription correction completed")
        
        emotions = get_text_emotions_gpt4(corrected_text)
        logger.info("Emotion analysis completed")
        
        return {
            "corrected_text": corrected_text,
            "emotions": emotions
        }
    except Exception as e:
        logger.error(f"Error in combined analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.post("/analyze/text/gpt4")
async def analyze_text_gpt4(request: TextAnalysisRequest) -> Dict[str, Any]:
    """Analyze text for emotions using GPT-4."""
    logger.info(f"Received GPT-4 analysis request for text: {request.text[:100]}...")
    try:
        result = correct_and_analyze_emotions(request.text)
        logger.info("Successfully completed GPT-4 analysis")
        return {
            "gpt4_analysis": {
                "model": "GPT-4",
                "emotions": result["emotions"]
            }
        }
    except Exception as e:
        logger.error(f"Error in GPT-4 analysis endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )