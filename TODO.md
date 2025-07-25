- emotion_trend: Andamento emotivo per segmenti temporali all’interno dello stesso messaggio
- vector_embedding: Rappresentazione vettoriale del testo/audio per ricerca semantica o clustering


Summary Table
NoSQL Database, MongoDB Atlas, Flexible, native Vercel integration, free tier
Node.js Backend, Vercel Serverless Fn, Seamless, scalable, easy DB integration
Audio Storage, Vercel Blob Storage, Native, fast, no setup, perfect for media files

# Ensemble averaging
final_score = (whisper_score['happy'] + speechbrain_score['hap']) / 2

# Smoothing
smoothed = moving_average(emotion_scores, window=3)

# Thresholding
if score < 5%: ignore_emotion()