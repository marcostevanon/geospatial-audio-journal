'use client';

import { collection as fsCollection, onSnapshot as fsOnSnapshot, orderBy as fsOrderBy, query as fsQuery, Timestamp } from 'firebase/firestore';
import { AnimatePresence } from 'framer-motion';
import { Clock, FileText, Loader2, Pause, Play, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { db } from '../lib/firebase';
import { VoiceNote } from '../types';

export default function VoiceNotesList() {
  const [notes, setNotes] = useState<VoiceNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTranscript, setSelectedTranscript] = useState<string | null>(null);

  useEffect(() => {
    const q = fsQuery(
      fsCollection(db, 'voice_notes'),
      fsOrderBy('createdAt', 'desc')
    );

    const unsubscribe = fsOnSnapshot(q, (snapshot) => {
      const fetchedNotes: VoiceNote[] = [];
      snapshot.forEach((doc) => {
        const data = doc.data();
        fetchedNotes.push({
          id: doc.id,
          fileName: data.fileName || '',
          fileUrl: data.fileUrl || '',
          userId: data.userId || '',
          createdAt: data.createdAt instanceof Timestamp ? data.createdAt : null,
          duration: data.duration || 0,
          emotions: data.emotions || {},
          transcript: data.transcript || '',
          status: data.status || 'pending',
          language: data.language || '',
        });
      });
      setNotes(fetchedNotes);
      setLoading(false);
    }, (error) => {
      console.error("Error fetching voice notes: ", error);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col gap-4 w-full">
        {[1, 2].map((i) => (
          <div key={i} className="animate-pulse bg-white/60 border border-slate-200 h-20 rounded-xl w-full"></div>
        ))}
      </div>
    );
  }

  if (notes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6 bg-white border border-slate-200 border-dashed rounded-3xl text-center">
        <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
          <Clock className="w-8 h-8 text-slate-300" />
        </div>
        <h3 className="text-lg font-bold text-slate-700 mb-1">No recordings yet</h3>
        <p className="text-slate-500 text-sm max-w-xs">Your voice notes and emotional analysis will appear here.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 w-full">
      <AnimatePresence>
        {notes.map((note) => (
          <VoiceNoteItem
            key={note.id}
            note={note}
            onOpenTranscript={() => setSelectedTranscript(note.transcript)}
          />
        ))}
      </AnimatePresence>

      {/* Transcript Modal */}
      {selectedTranscript && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-slate-900/20"
            onClick={() => setSelectedTranscript(null)}
          />
          <div className="relative w-full max-w-lg bg-white rounded-md shadow border border-slate-200 flex flex-col max-h-[70vh]">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50 rounded-t-md">
              <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-500" />
                Full Transcript
              </h3>
              <button
                onClick={() => setSelectedTranscript(null)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto bg-white rounded-b-md">
              <p className="text-sm text-slate-700 whitespace-pre-wrap">
                {selectedTranscript || 'No transcript available.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function VoiceNoteItem({ note, onOpenTranscript }: { note: VoiceNote; onOpenTranscript: () => void }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const formatDate = (note: VoiceNote): string => {
    if (!note.createdAt) return 'Just now';
    try {
      if (note.createdAt instanceof Timestamp) {
        return note.createdAt.toDate().toLocaleDateString(undefined, {
          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
      }
      if (note.createdAt instanceof Date) {
        return note.createdAt.toLocaleDateString(undefined, {
          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
      }
    } catch {
      return 'Just now';
    }
    return 'Just now';
  };

  // Extract top 3 emotions
  let topEmotions: { label: string; score: number }[] = [];
  if (Array.isArray(note.emotions)) {
    topEmotions = note.emotions.slice(0, 3);
  } else if (note.emotions && typeof note.emotions === 'object') {
    topEmotions = Object.entries(note.emotions)
      .map(([label, score]) => ({ label, score: Number(score) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
  }

  return (
    <div className="bg-white rounded-md p-3 border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 md:items-center">
      {/* Audio File Player & Basic Info */}
      <div className="flex items-center gap-3 md:w-1/4 shrink-0">
        <button
          onClick={togglePlay}
          className="w-8 h-8 shrink-0 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-700 transition-colors"
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" fill="currentColor" /> : <Play className="w-3.5 h-3.5 translate-x-0.5" fill="currentColor" />}
        </button>
        <div>
          <div className="text-sm font-medium text-slate-800">{formatDate(note)}</div>
          <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatDuration(note.duration)}
            </span>
            {note.language && typeof note.language === 'string' && (
              <span className="uppercase font-bold tracking-wider text-[9px] bg-slate-200 px-1 py-0.5 rounded text-slate-600">
                {note.language.slice(0, 2)}
              </span>
            )}
          </div>
        </div>
        <audio
          ref={audioRef}
          src={note.fileUrl}
          onEnded={() => setIsPlaying(false)}
          className="hidden"
        />
      </div>

      {/* Emotions */}
      <div className="flex flex-wrap gap-1.5 md:w-[30%] shrink-0">
        {topEmotions.length > 0 ? topEmotions.map((emotion, i) => (
          <span
            key={i}
            className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 whitespace-nowrap"
          >
            {emotion.label.charAt(0).toUpperCase() + emotion.label.slice(1)}
            <span className="opacity-75 ml-1">{Math.round(emotion.score)}%</span>
          </span>
        )) : (
          <span className="text-xs text-slate-400 italic">
            {note.status === 'processing' ? 'Analyzing...' : 'No emotions'}
          </span>
        )}
      </div>

      {/* Transcript snippet */}
      <div className="flex-1 flex items-center justify-between gap-2 border-l-2 border-slate-100 pl-3">
        <p className="text-sm text-slate-600 line-clamp-1 flex-1">
          {note.transcript ? `"${note.transcript}"` : (
            <span className="italic text-slate-400 flex items-center gap-1.5">
              {note.status === 'processing' ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Processing...
                </>
              ) : 'Pending...'}
            </span>
          )}
        </p>
        {note.transcript && (
          <button
            onClick={onOpenTranscript}
            className="shrink-0 text-slate-400 hover:text-slate-700 p-1"
            title="Read full transcript"
          >
            <FileText className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
