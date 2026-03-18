'use client';

import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Mic, Square, UploadCloud, Loader2 } from 'lucide-react';
import { ref, uploadBytesResumable, getDownloadURL } from 'firebase/storage';
import { storage } from '../lib/firebase';

export default function AudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Microphone access denied or not available.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
        setIsRecording(false);
        // Automatically start upload
        await handleUpload(audioBlob);
      };
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  const handleUpload = async (audioBlob: Blob) => {
    setIsUploading(true);
    setProgress(0);
    setAnalysisResult(null);

    const fileName = `recording-${Date.now()}.webm`;
    const storageRef = ref(storage, `audio_uploads/${fileName}`);

    const uploadTask = uploadBytesResumable(storageRef, audioBlob);

    uploadTask.on(
      'state_changed',
      (snapshot) => {
        const prog = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        setProgress(prog);
      },
      (error) => {
        console.error('Upload failed:', error);
        setIsUploading(false);
        alert('Upload to Firebase failed.');
      },
      async () => {
        const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);
        setIsUploading(false);

        // Notify API backend to enqueue the job
        await enqueueJob(fileName, downloadURL);
      }
    );
  };

  const enqueueJob = async (fileName: string, fileUrl: string) => {
    try {
      const response = await fetch('/api/audio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fileName, fileUrl }),
      });

      const data = await response.json();
      if (data.success) {
        setAnalysisResult({ status: 'Processing...', jobId: data.jobId });
      } else {
        alert('Failed to queue analysis.');
      }
    } catch (err) {
      console.error('API Error:', err);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl w-full max-w-md mx-auto">
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-semibold text-white mb-2">Voice Emotion Analysis</h2>
        <p className="text-white/60 text-sm">Record your thoughts and analyze the emotional tone.</p>
      </div>

      <div className="relative flex justify-center items-center w-full mb-8">
        {isRecording && (
          <motion.div
            initial={{ scale: 1, opacity: 0.5 }}
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute w-32 h-32 bg-red-500/30 rounded-full z-0"
          />
        )}
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isUploading}
          className={`relative z-10 flex items-center justify-center w-24 h-24 rounded-full shadow-lg transition-all duration-300 ${isRecording
            ? 'bg-red-500 hover:bg-red-600 shadow-red-500/50'
            : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-600/50'
            } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {isRecording ? (
            <Square fill="white" className="w-8 h-8 text-white" />
          ) : (
            <Mic className="w-10 h-10 text-white" />
          )}
        </button>
      </div>

      <div className="w-full text-center min-h-[60px]">
        {isUploading && (
          <div className="w-full">
            <div className="flex items-center justify-center text-indigo-400 text-sm mb-2 font-medium">
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Uploading to Cloud... {Math.round(progress)}%
            </div>
            <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
              <motion.div
                className="bg-indigo-500 h-1.5 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {analysisResult && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 bg-white/5 border border-white/10 rounded-xl"
          >
            <p className="text-white text-sm font-medium">Analysis Job Queued</p>
            <p className="text-white/50 text-xs mt-1 font-mono">ID: {analysisResult.jobId}</p>
          </motion.div>
        )}
      </div>

      {audioUrl && !isRecording && (
        <div className="mt-6 w-full">
          <audio controls src={audioUrl} className="w-full h-10 rounded-full" />
        </div>
      )}
    </div>
  );
}
