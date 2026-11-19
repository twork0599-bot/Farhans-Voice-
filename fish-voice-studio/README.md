# Farhan Voice Studio

A Next.js app using the official Fish Audio TypeScript SDK.

## Features
- Fish Audio text-to-speech with MP3 output
- Saved Voice IDs with custom names
- Speech speed control from 0.5x to 2.0x
- Saved speed and model preferences
- API key stays server-side in Vercel environment variables
- No studio password/login

## Environment
Add `FISH_API_KEY` in Vercel Project Settings → Environment Variables for Production, Preview and Development.

## Local development
```bash
npm install
npm run dev
```

Voice IDs and settings are stored in browser localStorage on the current device/browser. They do not sync between devices.

The API route has a lightweight in-memory request limit. For a public production app, configure Vercel Firewall or another durable rate limiter because serverless instances may not share memory.
