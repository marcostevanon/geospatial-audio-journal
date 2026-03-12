# Architecture Decision Record: Dual-Model Audio Analysis

## Status
Accepted

## Context
We need to analyze emotions expressed in voice messages. A single approach (e.g., text only) misses critical acoustic context (tone of voice, pitch).

## Decision
We will employ a dual-model approach:
1.  **Whisper V3**: Transcribe the audio to text, which is then fed into text-based sentiment/emotion models (local or via GPT-4).
2.  **SpeechBrain**: Process the raw audio to analyze acoustic emotional markers directly from the sound.

## Consequences
- Requires a Python environment capable of running heavy ML models.
- Better overall emotion detection accuracy by combining semantic meaning + vocal tone.
- Increased CPU/GPU overhead when processing messages.
