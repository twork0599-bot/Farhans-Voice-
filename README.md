# Farhan's Voice Studio

A self-hosted voice-cloning starter with a simple web interface and FastAPI backend. It runs the open-source Chatterbox model locally; no paid voice-generation API is used.

## Run it

1. Install Docker Desktop (Windows/macOS) or Docker Engine (Linux). For GPU use, install compatible NVIDIA drivers and the NVIDIA Container Toolkit.
2. Clone this repository.
3. From the repository folder, run `docker compose up --build`.
4. Open http://localhost:8000.

The first generation downloads model weights and can take several minutes. A CUDA-capable NVIDIA GPU is strongly recommended. CPU mode may be very slow; if Docker cannot access an NVIDIA GPU, remove the `gpus: all` line from docker-compose.yml.

## What is included

- Upload a reference voice sample (WAV, MP3, M4A, or FLAC; up to 20 MB).
- Enter text and generate a WAV file.
- Download and play the generated audio.
- Health endpoint at `/health`.

## Limitations

This starter uses Chatterbox's supported model/language capabilities. Do not assume Bengali output quality or Bengali support without testing the selected model. It does not yet include user accounts, an admin dashboard, persistent voice profiles, training/fine-tuning, job queues, or production-grade storage. GitHub stores the source; a GPU-capable host is needed to run inference. Vercel/Netlify alone cannot run this GPU model.

## Consent and safety

Only upload a voice sample when you have the speaker's informed permission. Do not use the system to impersonate, defraud, or mislead others. Add authentication, rate limits, private storage, and abuse monitoring before exposing it publicly.
