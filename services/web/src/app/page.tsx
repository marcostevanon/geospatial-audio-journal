import AudioRecorder from '../components/AudioRecorder';
import VoiceNotesList from '../components/VoiceNotesList';

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      <div className="max-w-5xl mx-auto p-6 md:p-12">
        <div className="flex flex-col items-start gap-12 w-full">
          <section className="w-full mx-auto max-w-sm">
            <AudioRecorder />
          </section>
          <section className="w-full">
            <VoiceNotesList />
          </section>
        </div>
      </div>
    </main>
  );
}
