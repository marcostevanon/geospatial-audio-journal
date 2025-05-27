import { TelegramClient } from "telegram";
import { StringSession } from "telegram/sessions";
import { config } from "./config";
import { exec } from "child_process";
import { promisify } from "util";
import * as fs from "fs";
import * as path from "path";
import { pipeline } from "@xenova/transformers";
import { getEmotionsFromPython, getTextEmotionsFromPython } from "./seraas-client";
import { AudioAnalysis, TextAnalysis, Emotion } from "./types";

const execAsync = promisify(exec);

async function analyzeAudio(buffer: Buffer): Promise<AudioAnalysis> {
  console.log("Analyzing audio...");
  const tempFile = `temp_${Date.now()}.ogg`;
  
  try {
    // Save buffer to temporary file
    fs.writeFileSync(tempFile, buffer);

    // Get audio information using ffprobe
    // const { stdout } = await execAsync(
    //   `ffprobe -v quiet -print_format json -show_format -show_streams ${tempFile}`
    // );
    // const info = JSON.parse(stdout);

    // Extract audio stream info
    // const audioStream = info.streams.find((s: any) => s.codec_type === "audio");
    // const format = info.format;

    // Generate waveform data
    // await execAsync(
    //   `ffmpeg -i ${tempFile} -filter_complex "showwavespic=s=640x120:colors=white" -frames:v 1 waveform.png`
    // );

    // Read waveform data
    // const waveform = fs.existsSync("waveform.png")
    //   ? fs.readFileSync("waveform.png")
    //   : undefined;

    console.log("Using Python microservice...");

    // Analyze emotions using the Python microservice
    const emotions = await getEmotionsFromPython(tempFile);
    console.log("Emotions:", emotions);

    return emotions;
  } finally {
    // Cleanup temporary files
    if (fs.existsSync(tempFile)) fs.unlinkSync(tempFile);
    if (fs.existsSync("waveform.png")) fs.unlinkSync("waveform.png");
  }
}

function printEmotionAnalysis(emotions: Emotion[]): void {
  emotions.forEach(({ emotion, confidence }) => {
    console.log(`${emotion}: ${confidence.toFixed(2)}%`);
  });
}

function printAudioAnalysis(analysis: AudioAnalysis): void {
  console.log("\nAudio Analysis:");
  
  console.log("\nWhisper Model (8 emotions):");
  printEmotionAnalysis(analysis.whisper_model.emotions);
  
  console.log("\nSpeechBrain Model (4 emotions):");
  printEmotionAnalysis(analysis.speechbrain_model.emotions);

  console.log("\nTranscription:");
  console.log(`Language: ${analysis.transcription.language}`);
  console.log(`Full Text: ${analysis.transcription.transcription}`);
  console.log("\nSegments:");
  analysis.transcription.segments.forEach((segment, index) => {
    console.log(`\nSegment ${index + 1}:`);
    console.log(`Time: ${segment.start.toFixed(2)}s - ${segment.end.toFixed(2)}s`);
    console.log(`Text: ${segment.text}`);
    if (segment.confidence !== null) {
      console.log(`Confidence: ${(segment.confidence * 100).toFixed(2)}%`);
    }
  });
}

function printTextAnalysis(analysis: TextAnalysis): void {
  console.log("\nText Emotion Analysis:");
  console.log(`Model: ${analysis.text_emotions.model}`);
  printEmotionAnalysis(analysis.text_emotions.emotions);
}

async function main() {
  try {
    // Create a new Telegram client
    const client = new TelegramClient(
      new StringSession(config.sessionString || ""),
      config.apiId,
      config.apiHash,
      { connectionRetries: 5 }
    );

    // Login (will use saved session if available)
    await client.start({
      phoneNumber: () => Promise.resolve(config.phoneNumber),
      password: () => Promise.resolve(config.password || ""),
      phoneCode: async () => {
        console.log("Please enter the code you received:");
        return new Promise((resolve) => {
          process.stdin.once("data", (data) => {
            resolve(data.toString().trim());
          });
        });
      },
      onError: (err) => console.error("Login error:", err),
    });

    // Save the session string for future use
    console.log("Session string:", client.session.save());

    // Get last message from the configured chat
    const messages = await client.getMessages(config.targetChatId, { limit: 1 });

    // Process messages
    for (const msg of messages) {
      if (msg.media && "document" in msg.media && msg.media.document) {
        console.log("\nVoice Message Details:");
        console.log("---------------------");

        // Download and analyze the audio
        const buffer = await client.downloadMedia(msg.media);
        if (buffer && Buffer.isBuffer(buffer)) {
          const analysis = await analyzeAudio(buffer);
          printAudioAnalysis(analysis);

          // Also analyze the transcribed text
          const textAnalysis = await getTextEmotionsFromPython(analysis.transcription.transcription);
          printTextAnalysis(textAnalysis);
        }
      } else if (msg.message) {
        console.log(`- ${msg.senderId}: ${msg.message}`);
        // Analyze text message
        const textAnalysis = await getTextEmotionsFromPython(msg.message);
        printTextAnalysis(textAnalysis);
      }
    }
  } catch (error) {
    console.error("Error in main process:", error);
    process.exit(1);
  }

  process.exit(0);
}

// Start the application
main();
