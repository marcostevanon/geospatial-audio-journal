import os
import requests
import logging

logger = logging.getLogger(__name__)

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")


def correct_text_with_ollama(text: str, model: str = "llama3") -> str:
    """
    Call a local Ollama model to correct spelling, grammar, and punctuation.
    The model name can be customized.
    """
    prompt = (
        "You are an expert audio transcription proofreader. Correct only transcription errors (misheard words, spelling, grammar, or punctuation) in the following text. "
        "- Do not change the meaning, style, or structure.\n"
        "- Keep all foreign words, names, and technical terms exactly as they appear.\n"
        "- Do not modify the text to make it more idiomatic or natural.\n"
        "- If you are not sure, keep it as is.\n"
        "- Do not add, omit, or paraphrase any part of the text.\n"
        "Text to correct:\n"
        f"{text}\n\n"
        "Return only the corrected text, nothing else."
    )
    logger.info(f"Calling Ollama model '{model}' for text correction.")
    response = requests.post(
        OLLAMA_API_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0},
        },
        timeout=30,
    )
    result = response.json()
    return result.get("response", "").strip()


def generate_with_ollama(text: str, model: str = "llama3") -> str:
    """
    Send the input text directly to the Ollama model and return the response.
    """
    logger.info(f"Calling Ollama model '{model}' for direct generation.")
    response = requests.post(
        OLLAMA_API_URL,
        json={"model": model, "prompt": text, "stream": False},
        timeout=30,
    )
    result = response.json()
    return result.get("response", "").strip()
