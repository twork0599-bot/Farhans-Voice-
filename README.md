# Farhan's Voice Studio

A self-hosted voice-cloning workspace with a private admin dashboard, voice library, audio generation, generation history, and consented dataset collection. It uses the open-source Chatterbox model locally; no paid voice-generation API is used.

## Run locally

1. Install Docker Desktop or Docker Engine. For GPU inference, install compatible NVIDIA drivers and NVIDIA Container Toolkit.
2. Clone this repository.
3. Set a private admin token before starting:
   - Linux/macOS: `export ADMIN_TOKEN='your-long-random-secret'`
   - PowerShell: `$env:ADMIN_TOKEN='your-long-random-secret'`
4. Run `docker compose up --build`.
5. Open http://localhost:8000 and sign in with the token.

The first model load downloads model weights and can take several minutes. An NVIDIA GPU is strongly recommended. For CPU-only testing, remove `gpus: all` from docker-compose.yml; generation may be very slow.

## Included

- Admin dashboard with runtime status and generation counts.
- Voice library: upload, save, and delete reference voice profiles.
- Text-to-speech generation from a saved voice profile.
- WAV playback and download.
- Dataset collection with speaker labels and consent confirmation.
- Dataset manifest export endpoint.
- SQLite metadata database and persistent local data volume.

## Important limitations

The current engine is Chatterbox's reference-audio voice cloning path. It is not a fine-tuning/training pipeline. The dataset section collects consented recordings and produces a manifest; a model-specific training recipe, validation process, and GPU training job still need to be added separately. Bengali language support and quality must be verified against the selected model version before relying on it. This MVP is intended for private/local use; before public deployment add HTTPS, stronger user management, rate limits, storage cleanup, and audit logs. GitHub stores the code but does not run GPU inference; deploy the backend to a GPU-capable server.

## Safety

Only upload or clone voices when the speaker has given informed permission. Do not use the system for impersonation, fraud, or deception.
