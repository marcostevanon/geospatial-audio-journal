'use client';

import { addDoc, collection as fsCollection, serverTimestamp } from 'firebase/firestore';
import { getDownloadURL, ref, uploadBytesResumable } from 'firebase/storage';
import { AnimatePresence, motion } from 'framer-motion';
import { Loader2, Mic, Square, AlertCircle, CheckCircle } from 'lucide-react';
import { useRef, useState } from 'react';
import { db, storage } from '../lib/firebase';
import { AudioAnalysisJob } from '../types';

type UploadStatus = 'idle' | 'recording' | 'uploading' | 'success' | 'error';

export default function AudioRecorder() {
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      setErrorMessage(null);
      setSuccessMessage(null);
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Set onstop callback BEFORE calling stop() - fixes race condition
      mediaRecorder.onstop = async () => {
        const durationSec = Math.round(performance.now() / 1000);
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        setStatus('uploading');
        await handleUpload(audioBlob, durationSec);
      };

      mediaRecorder.start();
      setStatus('recording');
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setErrorMessage('Microphone access denied or not available.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && status === 'recording') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  const handleUpload = async (audioBlob: Blob, duration: number) => {
    try {
      setProgress(0);
      setErrorMessage(null);

      const fileName = `recording-${Date.now()}.webm`;
      const storageRef = ref(storage, `audio_uploads/${fileName}`);
      const uploadTask = uploadBytesResumable(storageRef, audioBlob);

      await new Promise<void>((resolve, reject) => {
        uploadTask.on(
          'state_changed',
          (snapshot) => {
            const prog = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
            setProgress(prog);
          },
          (error) => {
            console.error('Upload failed:', error);
            reject(new Error('Upload to Firebase failed.'));
          },
          async () => {
            try {
              const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);

              const docRef = await addDoc(fsCollection(db, 'voice_notes'), {
                fileName,
                fileUrl: downloadURL,
                userId: 'anonymous',
                createdAt: serverTimestamp(),
                duration,
                emotions: {},
                transcript: '',
                status: 'processing'
              });

              await enqueueJob(fileName, downloadURL, docRef.id, duration);
              resolve();
            } catch (e) {
              console.error("Error creating Firestore doc:", e);
              reject(e);
            }
          }
        );
      });

      setStatus('success');
      setSuccessMessage('Recording uploaded successfully!');
      setTimeout(() => {
        setStatus('idle');
        setSuccessMessage(null);
      }, 3000);
    } catch (err) {
      console.error('Upload error:', err);
      setStatus('error');
      setErrorMessage(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setProgress(0);
    }
  };

  const enqueueJob = async (fileName: string, fileUrl: string, docId: string, duration: number) => {
    const jobPayload: AudioAnalysisJob = { fileName, fileUrl, docId, duration };
    
    const response = await fetch('/api/audio', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jobPayload),
    });

    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error('Failed to parse server response');
    }

    if (!response.ok || !data.success) {
      throw new Error(data.error || 'Failed to queue analysis');
    }
  };

  return (
    <div className="flex flex-col items-start transition-all">
      <div className="flex items-center flex-col w-full">
        <div className="relative">
          <AnimatePresence>
            {status === 'recording' && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: [1, 1.4, 1], opacity: [0.3, 0, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="absolute inset-0 bg-red-400 rounded-full z-0 pointer-events-none"
              />
            )}
          </AnimatePresence>
          <button
            onClick={status === 'recording' ? stopRecording : startRecording}
            disabled={status === 'uploading'}
            className={`relative z-10 cursor-pointer flex items-center justify-center w-14 h-14 rounded-full shadow-sm transition-all duration-300 transform hover:scale-105 active:scale-95 ${status === 'recording'
              ? 'bg-red-500 text-white hover:bg-red-600 shadow-red-200'
              : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-200'
              } ${status === 'uploading' ? 'opacity-50 cursor-not-allowed scale-100 hover:scale-100' : ''}`}
          >
            {status === 'recording' ? (
              <Square fill="currentColor" className="w-5 h-5" />
            ) : (
              <Mic className="w-6 h-6" />
            )}
          </button>
        </div>

        <div className="flex-1 flex flex-col justify-center min-h-[56px]">
          {status === 'idle' && !errorMessage && !successMessage && (
            <span className="text-sm font-medium text-slate-600">Tap to record</span>
          )}
          {status === 'recording' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              <span className="text-sm font-bold text-red-500">Recording...</span>
            </motion.div>
          )}
          {status === 'uploading' && (
            <div className="w-full">
              <div className="flex items-center text-indigo-600 text-xs font-bold mb-1.5">
                <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
                Uploading {Math.round(progress)}%
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                <motion.div
                  className="bg-indigo-500 h-1.5 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
          {status === 'error' && errorMessage && (
            <div className="flex items-center gap-1.5 text-red-500 text-xs">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>{errorMessage}</span>
            </div>
          )}
          {status === 'success' && successMessage && (
            <div className="flex items-center gap-1.5 text-green-600 text-xs">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>{successMessage}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}