import os
import tempfile
import uuid
from pathlib import Path

import torch
import torchaudio
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from chatterbox.tts import ChatterboxTTS

BASE = Path(__file__).parent
OUTPUTS = BASE / "outputs"
OUTPUTS.mkdir(exist_ok=True)
MAX_AUDIO_BYTES = 20 * 1024 * 1024
ALLOWED = {".wav", ".mp3", ".m4a", ".flac"}

app = FastAPI(title="Farhan's Voice Studio", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
_model = None

def load_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = ChatterboxTTS.from_pretrained(device=device)
    return _model

@app.get("/health")
def health():
    return {"status": "ok", "gpu_available": torch.cuda.is_available()}

@app.post("/generate")
async def generate(text: str = Form(...), reference_audio: UploadFile = File(...)):
    text = text.strip()
    if not text or len(text) > 1000:
        raise HTTPException(400, "Text must be 1–1000 characters.")
    suffix = Path(reference_audio.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "Use WAV, MP3, M4A, or FLAC.")
    raw = await reference_audio.read()
    if not raw or len(raw) > MAX_AUDIO_BYTES:
        raise HTTPException(400, "Audio must be non-empty and at most 20 MB.")

    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(raw)
            temp_name = temp.name
        engine = load_model()
        with torch.inference_mode():
            audio = engine.generate(text, audio_prompt_path=temp_name)
        out = OUTPUTS / f"{uuid.uuid4().hex}.wav"
        torchaudio.save(str(out), audio.cpu(), engine.sr)
        return FileResponse(out, media_type="audio/wav", filename="farhan-voice.wav")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Generation failed ({type(exc).__name__}); check server logs.")
    finally:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)
