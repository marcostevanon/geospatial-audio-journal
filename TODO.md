# Backlog & TODO

## AI & Emotion Engine
- [ ] `emotion_trend`: Emotional trend for time segments within the same message.
- [ ] `vector_embedding`: Vector representation of text/audio for semantic search or clustering.
- [ ] Implement ensemble averaging: `final_score = (whisper_score['happy'] + speechbrain_score['hap']) / 2`
- [ ] Smoothing: `smoothed = moving_average(emotion_scores, window=3)`
- [ ] Thresholding: `if score < 5%: ignore_emotion()`

## Project & APIs
- [ ] Consolidate project names, API names, route names to better reflect the Geospatial Audio Journal.
- [ ] Add a new API for state of mind evaluation.

## Integrations & Data
- [ ] Health Metrics: Use health metric/mind state import, build API for mental state, and adapt Notion integration.
- [ ] Aggregate Data: Save daily specific metrics as a whole measurement for the day to better measure stress over time.
- [ ] Parse Polarsteps location history to correlate audio with places.
- [ ] Import and process historical Córdoba voice messages (saved messages).

## Infrastructure Sync
- [ ] Setup a proper database (SQL, NoSQL, etc. - decision pending) to store analysis results and metrics.
- [ ] Move Node.js backend to Vercel Serverless Functions.
- [ ] Use Vercel Blob Storage for audio file retention (if implementing).