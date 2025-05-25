import { TelegramClient } from "telegram";
import { StringSession } from "telegram/sessions";
import { config } from "./config";
import { exec } from "child_process";
import { promisify } from "util";
import * as fs from "fs";
import * as path from "path";
import { pipeline } from "@xenova/transformers";
import { getEmotionsFromPython } from "./seraas-client";

const execAsync = promisify(exec);

interface AudioAnalysis {
  duration: number;
  bitrate: number;
  sampleRate: number;
  channels: number;
  codec: string;
  format: string;
  size: number;
  waveform?: number[];
  emotions?: {
    whisper_model: {
      model: string;
      emotions: {
        emotion: string;
        confidence: number;
      }[];
    };
    speechbrain_model: {
      model: string;
      emotions: {
        emotion: string;
        confidence: number;
      }[];
    };
  };
}

async function analyzeEmotions(
  audioPath: string
): Promise<{ emotion: string; confidence: number }[]> {
  try {
    // Load the emotion recognition model
    const classifier = await pipeline(
      "audio-classification",
      "jonatasgrosman/wav2vec2-large-xlsr-53-english"
    );

    // Convert audio to the right format if needed
    const wavPath = audioPath.replace(".ogg", ".wav");
    await execAsync(
      `ffmpeg -i ${audioPath} -acodec pcm_s16le -ar 16000 -ac 1 ${wavPath}`
    );

    // Classify the audio
    const result = await classifier(wavPath, {
      topk: 5, // Get top 5 emotions
    });

    // Clean up the temporary wav file
    if (fs.existsSync(wavPath)) {
      fs.unlinkSync(wavPath);
    }

    // Map the results to our expected format
    return result.map((r: any) => ({
      emotion: r.label,
      confidence: r.score,
    }));
  } catch (error) {
    console.error("Error analyzing emotions:", error);
    return [];
  }
}

async function analyzeAudio(buffer: Buffer): Promise<AudioAnalysis> {
  console.log("Analyzing audio...");
  // Save buffer to temporary file
  const tempFile = `temp_${Date.now()}.ogg`;
  fs.writeFileSync(tempFile, buffer);

  try {
    // Get audio information using ffprobe
    const { stdout } = await execAsync(
      `ffprobe -v quiet -print_format json -show_format -show_streams ${tempFile}`
    );
    const info = JSON.parse(stdout);

    // Extract audio stream info
    const audioStream = info.streams.find((s: any) => s.codec_type === "audio");
    const format = info.format;

    // Generate waveform data
    const { stdout: waveformData } = await execAsync(
      `ffmpeg -i ${tempFile} -filter_complex "showwavespic=s=640x120:colors=white" -frames:v 1 waveform.png`
    );

    // Read waveform data
    const waveform = fs.existsSync("waveform.png")
      ? fs.readFileSync("waveform.png")
      : undefined;

    console.log("Using Python microservice...");

    // Analyze emotions using the Python microservice
    const emotions = await getEmotionsFromPython(tempFile);
    console.log("Emotions:", emotions);

    const analysis: AudioAnalysis = {
      duration: parseFloat(format.duration),
      bitrate: parseInt(format.bit_rate),
      sampleRate: parseInt(audioStream.sample_rate),
      channels: audioStream.channels,
      codec: audioStream.codec_name,
      format: format.format_name,
      size: buffer.length,
      waveform: waveform ? Array.from(waveform) : undefined,
      emotions,
    };

    return analysis;
  } finally {
    // Cleanup temporary files
    if (fs.existsSync(tempFile)) fs.unlinkSync(tempFile);
    if (fs.existsSync("waveform.png")) fs.unlinkSync("waveform.png");
  }
}

async function main() {
  // Create a new Telegram client
  const client = new TelegramClient(
    new StringSession(config.sessionString || ""), // Use saved session if available
    Number(config.apiId),
    config.apiHash as string,
    { connectionRetries: 5 }
  );

  // Login (will use saved session if available)
  await client.start({
    phoneNumber: () => Promise.resolve(config.phoneNumber as string),
    password: () => Promise.resolve(config.password || ""),
    phoneCode: async () => {
      console.log("Please enter the code you received:");
      return new Promise((resolve) => {
        process.stdin.once("data", (data) => {
          resolve(data.toString().trim());
        });
      });
    },
    onError: (err) => console.log(err),
  });

  // Save the session string for future use
  console.log("Session string:", client.session.save());

  // Get last 10 messages from the configured chat
  const messages = await client.getMessages(config.targetChatId, { limit: 1 });

  // Print messages
  for (const msg of messages) {
    if (msg.media && "document" in msg.media && msg.media.document) {
      const doc = msg.media.document;

      // Download the file first
      const buffer = await client.downloadMedia(msg.media);
      if (buffer && Buffer.isBuffer(buffer)) {
        console.log("\nVoice Message Details:");
        console.log("---------------------");

        // Analyze the audio
        const analysis = await analyzeAudio(buffer);
        console.log("Audio Analysis:");
        console.log(`Duration: ${analysis.duration.toFixed(2)} seconds`);
        console.log(`Bitrate: ${(analysis.bitrate / 1000).toFixed(2)} kbps`);
        console.log(`Sample Rate: ${analysis.sampleRate} Hz`);
        console.log(`Channels: ${analysis.channels}`);
        console.log(`Codec: ${analysis.codec}`);
        console.log(`Format: ${analysis.format}`);
        console.log(`Size: ${(analysis.size / 1024).toFixed(2)} KB`);

        if (analysis.emotions) {
          console.log("\nEmotion Analysis:");
          
          console.log("\nWhisper Model (8 emotions):");
          analysis.emotions.whisper_model.emotions.forEach(({ emotion, confidence }) => {
            console.log(`${emotion}: ${confidence.toFixed(2)}%`);
          });
          
          console.log("\nSpeechBrain Model (4 emotions):");
          analysis.emotions.speechbrain_model.emotions.forEach(({ emotion, confidence }) => {
            console.log(`${emotion}: ${confidence.toFixed(2)}%`);
          });
        }

        if (analysis.waveform) {
          console.log("Waveform data available");
        }
      }
    } else if (msg.message) {
      console.log(`- ${msg.senderId}: ${msg.message}`);
    }
  }

  process.exit(0);
}

main();
