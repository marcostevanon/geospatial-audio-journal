import { NextResponse } from 'next/server';
import { audioQueue } from '../../../lib/redis';
import type { AudioAnalysisJob } from '../../../types';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { fileName, fileUrl, docId, duration } = body as Partial<AudioAnalysisJob>;

    if (!fileName || !fileUrl) {
      return NextResponse.json(
        { success: false, error: 'Missing fileName or fileUrl' },
        { status: 400 }
      );
    }

    const job = await audioQueue.add('analyze-audio', {
      fileName,
      fileUrl,
      docId: docId || '',
      duration,
      userId: 'anonymous',
    });

    return NextResponse.json({
      success: true,
      jobId: job.id,
      message: 'Job enqueued successfully',
    });
  } catch (error) {
    console.error('Error enqueuing job:', error);
    return NextResponse.json(
      { success: false, error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
