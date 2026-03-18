# New Feature Setup

The Voice Recording feature has been entirely built out. 

## Requirements to Run
1. Start the Redis Queue:
   Run `docker-compose up -d` in the root folder.
2. Prepare your Firebase Account:
   - Go to the Firebase Console, create a new Web project.
   - Enable Firebase Storage and create a bucket.
   - For `services/web`: Fill in your `.env.local` using those web Firebase config properties (`NEXT_PUBLIC_FIREBASE_API_KEY`, etc.).
   - For `services/worker`: Generate a new Private Key from Firebase Project Settings > Service Accounts. Put the JSON as a string inside `FIREBASE_SERVICE_ACCOUNT_KEY` inside `.env`.
3. Start the Next.js web application:
   `cd services/web && npm run dev`
4. Start the Node.js worker:
   `cd services/worker && npm run dev`
5. Ensure the Python `emotion-engine` is running.

When you record audio and hit stop, it will upload to Firebase, then queue a Redis task, where the worker downloads and dispatches it to the Python engine.
