'use client';

import { addDoc, collection as fsCollection, serverTimestamp } from 'firebase/firestore';
import { getDownloadURL, ref, uploadBytesResumable } from 'firebase/storage';
import { AnimatePresence, motion } from 'framer-motion';
import { Loader2, Mic, Square } from 'lucide-react';
import { useRef, useState } from 'react';
import { db, storage } from '../lib/firebase';

export default function AudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [recordStart, setRecordStart] = useState<number | null>(null);

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
      setRecordStart(Date.now());
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Microphone access denied or not available.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.onstop = async () => {
        const durationMs = recordStart ? Date.now() - recordStart : 0;
        const durationSec = Math.round(durationMs / 1000);

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setIsRecording(false);
        setRecordStart(null);
        await handleUpload(audioBlob, durationSec);
      };
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  const handleUpload = async (audioBlob: Blob, duration: number) => {
    setIsUploading(true);
    setProgress(0);

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

        // Save placeholder in Firestore so it appears immediately
        try {
          const docRef = await addDoc(fsCollection(db, 'voice_notes'), {
            fileName,
            fileUrl: downloadURL,
            userId: 'anonymous',
            createdAt: serverTimestamp(),
            duration: duration,
            emotions: {},
            transcript: '',
            status: 'processing'
          });

          console.log('docRef', docRef)

          await enqueueJob(fileName, downloadURL, docRef.id, duration);
        } catch (e) {
          console.error("Error creating Firestore doc:", e);
        }

        setIsUploading(false);
      }
    );
  };

  const enqueueJob = async (fileName: string, fileUrl: string, docId: string, duration: number) => {
    try {
      const response = await fetch('/api/audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileName, fileUrl, docId, duration }),
      });
      const data = await response.json();
      if (!data.success) {
        alert('Failed to queue analysis.');
      }
    } catch (err) {
      console.error('API Error:', err);
    }
  };

  return (
    <div className="flex flex-col items-start transition-all">
      <div className="flex items-center flex-col w-full">
        <div className="relative">
          <AnimatePresence>
            {isRecording && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: [1, 1.4, 1], opacity: [0.3, 0, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="absolute inset-0 bg-red-400 rounded-full z-0 pointer-events-none"
              />
            )}
          </AnimatePresence>
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isUploading}
            className={`relative z-10 cursor-pointer flex items-center justify-center w-14 h-14 rounded-full shadow-sm transition-all duration-300 transform hover:scale-105 active:scale-95 ${isRecording
              ? 'bg-red-500 text-white hover:bg-red-600 shadow-red-200'
              : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-200'
              } ${isUploading ? 'opacity-50 cursor-not-allowed scale-100 hover:scale-100' : ''}`}
          >
            {isRecording ? (
              <Square fill="currentColor" className="w-5 h-5" />
            ) : (
              <Mic className="w-6 h-6" />
            )}
          </button>
        </div>

        <div className="flex-1 flex flex-col justify-center min-h-[56px]">
          {!isRecording && !isUploading && (
            <span className="text-sm font-medium text-slate-600">Tap to record</span>
          )}
          {isRecording && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              <span className="text-sm font-bold text-red-500">Recording...</span>
            </motion.div>
          )}
          {isUploading && (
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
        </div>
      </div>
    </div>
  );
}
