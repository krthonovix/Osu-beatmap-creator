import os
import uuid
import json
import asyncio
from typing import Optional, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.audio_analyzer import AudioAnalyzer
from backend.mapper_profiles import MAPPER_PROFILES, MAP_STYLES
from backend.models.job import JobState, JobStatus
from backend.generator import BeatmapGenerator, PROJECT_ROOT

app = FastAPI(title="Ai Mapper - osu! Beatmap Creator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenamiento en memoria de trabajos
jobs: Dict[str, JobState] = {}
uploaded_audios: Dict[str, str] = {} # token -> file_path

# Montar carpeta frontend como estáticos
frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
os.makedirs(frontend_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Ai Mapper</h1><p>Frontend cargando...</p>"

@app.get("/api/options")
async def get_options():
    return {
        "mappers": MAPPER_PROFILES,
        "styles": MAP_STYLES
    }

@app.post("/api/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    """
    Guarda el archivo temporalmente y analiza BPM, duración y metadatos.
    """
    token = str(uuid.uuid4())
    temp_dir = os.path.join(PROJECT_ROOT, "temp", "uploads")
    os.makedirs(temp_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1] or ".mp3"
    saved_path = os.path.join(temp_dir, f"{token}{file_ext}")
    
    with open(saved_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    uploaded_audios[token] = saved_path
    
    # Analizar audio
    try:
        analysis = AudioAnalyzer.analyze_audio(saved_path)
    except Exception as e:
        analysis = {
            "artist": "Unknown Artist",
            "title": os.path.splitext(file.filename)[0],
            "duration": 0.0,
            "bpm": 180.0,
            "avg_energy": 0.0,
            "max_energy": 0.0
        }
        
    return {
        "audio_token": token,
        "filename": file.filename,
        **analysis
    }

@app.post("/api/generate")
async def start_generation(
    background_tasks: BackgroundTasks,
    audio_token: str = Form(...),
    difficulty: float = Form(7.0),
    style_id: str = Form("jump"),
    mapper_id: str = Form("sotarks"),
    title: Optional[str] = Form(None),
    artist: Optional[str] = Form(None),
):
    audio_path = uploaded_audios.get(audio_token)
    if not audio_path or not os.path.exists(audio_path):
        # Intentar buscar en temp/uploads
        import glob
        pattern = os.path.join(PROJECT_ROOT, "temp", "uploads", f"{audio_token}.*")
        matches = glob.glob(pattern)
        if matches:
            audio_path = matches[0]
            uploaded_audios[audio_token] = audio_path
        else:
            raise HTTPException(status_code=400, detail="Audio no encontrado o expirado. Vuelve a subirlo.")
        
    job_id = str(uuid.uuid4())
    
    job = JobState(
        job_id=job_id,
        status=JobStatus.PENDING,
        difficulty=difficulty,
        style_id=style_id,
        mapper_id=mapper_id,
        title=title or "Track",
        artist=artist or "Artist"
    )
    
    jobs[job_id] = job
    
    # Ejecutar generación en background
    background_tasks.add_task(
        BeatmapGenerator.run_generation,
        job=job,
        audio_path=audio_path
    )
    
    return {"job_id": job_id, "status": job.status}

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return jobs[job_id]

@app.get("/api/events/{job_id}")
async def stream_job_events(job_id: str):
    """
    Stream de Server-Sent Events (SSE) para el progreso en vivo.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
        
    async def event_generator():
        last_progress = -1
        last_status = None
        last_msg = ""
        
        while True:
            job = jobs.get(job_id)
            if not job:
                break
                
            if job.progress != last_progress or job.status != last_status or job.message != last_msg:
                last_progress = job.progress
                last_status = job.status
                last_msg = job.message
                data = job.model_dump_json()
                yield f"data: {data}\n\n"
                
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
                
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/download/{job_id}")
async def download_beatmap(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
        
    job = jobs[job_id]
    if job.status != JobStatus.COMPLETED or not job.osz_path or not os.path.exists(job.osz_path):
        raise HTTPException(status_code=400, detail="El beatmap no está listo para descargar")
        
    filename = os.path.basename(job.osz_path)
    return FileResponse(
        path=job.osz_path,
        filename=filename,
        media_type="application/octet-stream"
    )
