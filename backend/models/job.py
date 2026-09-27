from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import time

class JobStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    PACKAGING = "packaging"
    COMPLETED = "completed"
    FAILED = "failed"

class JobState(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0 # 0 a 100
    message: str = "Iniciando..."
    audio_filename: str = ""
    title: str = ""
    artist: str = ""
    duration: float = 0.0
    bpm: float = 0.0
    difficulty: float = 7.0
    style_id: str = "jump"
    mapper_id: Optional[str] = "sotarks"
    osz_path: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
