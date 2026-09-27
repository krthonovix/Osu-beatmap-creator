import os
from typing import Dict, Any, Optional
import numpy as np
import librosa
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

class AudioAnalyzer:
    @staticmethod
    def extract_metadata(file_path: str) -> Dict[str, str]:
        """
        Extrae artista y título desde los tags ID3 del MP3 si existen,
        o del nombre del archivo como fallback.
        """
        artist = "Unknown Artist"
        title = "Unknown Track"
        
        try:
            audio = MP3(file_path, ID3=EasyID3)
            if "artist" in audio and len(audio["artist"]) > 0:
                artist = audio["artist"][0]
            if "title" in audio and len(audio["title"]) > 0:
                title = audio["title"][0]
        except Exception:
            pass
            
        if artist == "Unknown Artist" and title == "Unknown Track":
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            if " - " in base_name:
                parts = base_name.split(" - ", 1)
                artist = parts[0].strip()
                title = parts[1].strip()
            else:
                title = base_name.strip()
                
        return {"artist": artist, "title": title}

    @staticmethod
    def analyze_audio(file_path: str) -> Dict[str, Any]:
        """
        Analiza el archivo MP3:
        - Duración (segundos)
        - BPM estimado
        - Energía media y nivel de intensidad
        """
        metadata = AudioAnalyzer.extract_metadata(file_path)
        
        # Cargar audio a 22050 Hz mono (estándar para análisis rápido)
        y, sr = librosa.load(file_path, sr=22050, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr))
        
        # Detección de BPM
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        
        bpm = float(tempo[0]) if isinstance(tempo, (list, np.ndarray)) else float(tempo)
        
        # Cálculo de energía RMS
        rms = librosa.feature.rms(y=y)[0]
        avg_energy = float(np.mean(rms))
        max_energy = float(np.max(rms)) if len(rms) > 0 else 0.0
        
        return {
            "artist": metadata["artist"],
            "title": metadata["title"],
            "duration": round(duration, 2),
            "bpm": round(bpm, 1),
            "avg_energy": round(avg_energy, 4),
            "max_energy": round(max_energy, 4),
        }
