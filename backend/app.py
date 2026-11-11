import os
import json
import uuid
import sqlite3
import secrets
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import torch
import torchaudio
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from chatterbox.tts import ChatterboxTTS

ROOT = Path("/app")
DATA = Path(os.getenv("DATA_DIR", "/app/data"))
VOICES = DATA / "voices"
OUTPUTS = DATA / "outputs"
DATASETS = DATA / "datasets"
FRONTEND = ROOT / "frontend"
for folder in (DATA, VOICES, OUTPUTS, DATASETS):
    folder.mkdir(parents=True, exist_ok=True)

DB = DATA / "studio.db"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-this-admin-token")
MAX_AUDIO_BYTES = 25 * 1024 * 1024
ALLOWED = {".wav", ".mp3", ".m4a", ".flac"}
app = FastAPI(title="Farhan's Voice Studio", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(","),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
_model = None

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS voices (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, filename TEXT NOT NULL,
          consent INTEGER NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS generations (
          id TEXT PRIMARY KEY, voice_id TEXT, text TEXT NOT NULL,
          filename TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS dataset_clips (
          id TEXT PRIMARY KEY, speaker TEXT NOT NULL, filename TEXT NOT NULL,
          consent INTEGER NOT NULL, created_at TEXT NOT NULL
        );
        """)
init_db()

def require_admin(token):
    if not token or not secrets.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(401, "Admin token is missing or incorrect.")

def load_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = ChatterboxTTS.from_pretrained(device=device)
    return _model

def save_upload(raw: bytes, suffix: str, folder: Path) -> str:
    name = f"{uuid.uuid4().hex}{suffix}"
    (folder / name).write_bytes(raw)
    return name

@app.get("/")
def home():
    return FileResponse(FRONTEND / "index.html")

@app.get("/health")
def health():
    return {"status": "ok", "gpu_available": torch.cuda.is_available(), "model_loaded": _model is not None}

@app.get("/admin/stats")
def stats(x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    with db() as con:
        voices = con.execute("SELECT COUNT(*) n FROM voices").fetchone()["n"]
        generations = con.execute("SELECT COUNT(*) n FROM generations").fetchone()["n"]
        clips = con.execute("SELECT COUNT(*) n FROM dataset_clips").fetchone()["n"]
        recent = con.execute("SELECT id,text,filename,created_at,status FROM generations ORDER BY created_at DESC LIMIT 12").fetchall()
    return {"voices": voices, "generations": generations, "dataset_clips": clips,
            "gpu_available": torch.cuda.is_available(), "model_loaded": _model is not None,
            "recent": [dict(r) for r in recent]}

@app.get("/voices")
def list_voices(x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    with db() as con:
        rows = con.execute("SELECT id,name,created_at FROM voices ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/voices")
async def add_voice(name: str = Form(...), consent: bool = Form(...),
                    audio: UploadFile = File(...), x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    if not consent:
        raise HTTPException(400, "Confirm that you have the speaker's permission.")
    name = name.strip()
    if not name or len(name) > 60:
        raise HTTPException(400, "Voice name must be 1–60 characters.")
    suffix = Path(audio.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "Use WAV, MP3, M4A, or FLAC.")
    raw = await audio.read()
    if not raw or len(raw) > MAX_AUDIO_BYTES:
        raise HTTPException(400, "Audio must be non-empty and at most 25 MB.")
    file_name = save_upload(raw, suffix, VOICES)
    voice_id = uuid.uuid4().hex
    with db() as con:
        con.execute("INSERT INTO voices VALUES (?,?,?,?,?)",
                    (voice_id, name, file_name, 1, datetime.now(timezone.utc).isoformat()))
    return {"id": voice_id, "name": name}

@app.delete("/voices/{voice_id}")
def delete_voice(voice_id: str, x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    with db() as con:
        row = con.execute("SELECT filename FROM voices WHERE id=?", (voice_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Voice not found.")
        (VOICES / row["filename"]).unlink(missing_ok=True)
        con.execute("DELETE FROM voices WHERE id=?", (voice_id,))
    return {"deleted": True}

@app.post("/dataset")
async def add_dataset_clip(speaker: str = Form(...), consent: bool = Form(...),
                           audio: UploadFile = File(...), x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    if not consent:
        raise HTTPException(400, "Confirm permission to use this speaker's recording.")
    speaker = speaker.strip()
    if not speaker or len(speaker) > 80:
        raise HTTPException(400, "Speaker label must be 1–80 characters.")
    suffix = Path(audio.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "Use WAV, MP3, M4A, or FLAC.")
    raw = await audio.read()
    if not raw or len(raw) > MAX_AUDIO_BYTES:
        raise HTTPException(400, "Audio must be non-empty and at most 25 MB.")
    file_name = save_upload(raw, suffix, DATASETS)
    clip_id = uuid.uuid4().hex
    with db() as con:
        con.execute("INSERT INTO dataset_clips VALUES (?,?,?,?,?)",
                    (clip_id, speaker, file_name, 1, datetime.now(timezone.utc).isoformat()))
    return {"id": clip_id, "speaker": speaker, "message": "Dataset clip saved. Fine-tuning is not run by this endpoint."}

@app.get("/dataset/manifest")
def dataset_manifest(x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    with db() as con:
        rows = con.execute("SELECT id,speaker,filename,created_at FROM dataset_clips ORDER BY created_at").fetchall()
    manifest = [{"id": r["id"], "speaker": r["speaker"], "audio": f"datasets/{r['filename']}", "created_at": r["created_at"]} for r in rows]
    return {"count": len(manifest), "items": manifest,
            "note": "This manifest organizes consented recordings; model-specific fine-tuning must be implemented separately."}

@app.post("/generate")
async def generate(text: str = Form(...), voice_id: str = Form(...),
                   x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    text = text.strip()
    if not text or len(text) > 1000:
        raise HTTPException(400, "Text must be 1–1000 characters.")
    with db() as con:
        voice = con.execute("SELECT filename FROM voices WHERE id=?", (voice_id,)).fetchone()
    if not voice:
        raise HTTPException(404, "Saved voice not found.")
    prompt_path = VOICES / voice["filename"]
    try:
        engine = load_model()
        with torch.inference_mode():
            audio = engine.generate(text, audio_prompt_path=str(prompt_path))
        output_name = f"{uuid.uuid4().hex}.wav"
        output_path = OUTPUTS / output_name
        torchaudio.save(str(output_path), audio.cpu(), engine.sr)
        gen_id = uuid.uuid4().hex
        with db() as con:
            con.execute("INSERT INTO generations VALUES (?,?,?,?,?,?)",
                        (gen_id, voice_id, text, output_name, datetime.now(timezone.utc).isoformat(), "completed"))
        return FileResponse(output_path, media_type="audio/wav", filename="farhan-voice.wav")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Generation failed ({type(exc).__name__}); check server logs.")

@app.get("/history/{generation_id}/audio")
def download_generation(generation_id: str, x_admin_token: str = Header(default="")):
    require_admin(x_admin_token)
    with db() as con:
        row = con.execute("SELECT filename FROM generations WHERE id=?", (generation_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Generation not found.")
    path = OUTPUTS / row["filename"]
    if not path.is_file():
        raise HTTPException(404, "Audio file is no longer available.")
    return FileResponse(path, media_type="audio/wav", filename="farhan-voice.wav")
