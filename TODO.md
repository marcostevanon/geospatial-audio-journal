- understand how to scaffold to project to deploy it on vercel 

telegram-emotion-app/
├── src/
│   ├── app/                    # Next.js 13+ app directory
│   │   ├── page.tsx           # Main page
│   │   └── layout.tsx         # Root layout
│   ├── api/                   # API routes
│   │   ├── telegram/          # Telegram-related endpoints
│   │   │   ├── route.ts       # Telegram API handler
│   │   │   └── client.ts      # Telegram client
│   │   └── analyze/           # Emotion analysis endpoint
│   │       └── route.ts       # Python service handler
│   └── lib/                   # Shared utilities
│       └── types.ts           # TypeScript types
├── public/                    # Static files
└── package.json

- emotion_trend: Andamento emotivo per segmenti temporali all’interno dello stesso messaggio
- vector_embedding: Rappresentazione vettoriale del testo/audio per ricerca semantica o clustering


Summary Table
NoSQL Database, MongoDB Atlas, Flexible, native Vercel integration, free tier
Node.js Backend, Vercel Serverless Fn, Seamless, scalable, easy DB integration
Audio Storage, Vercel Blob Storage, Native, fast, no setup, perfect for media files


