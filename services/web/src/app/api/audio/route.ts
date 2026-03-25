import { NextResponse } from 'next/server';
import { audioQueue } from '../../../lib/redis';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { fileName, fileUrl, docId, duration } = body;

    if (!fileName || !fileUrl) {
      return NextResponse.json(
        { success: false, error: 'Missing fileName or fileUrl' },
        { status: 400 }
      );
    }

    // Enqueue the job for the worker
    const job = await audioQueue.add('analyze-audio', {
      fileName,
      fileUrl,
      docId,
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
