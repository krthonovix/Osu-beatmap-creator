import os
import json
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
HISTORY_FILE = os.path.join(OUTPUT_DIR, "history.json")

class HistoryManager:
    @staticmethod
    def _load_raw() -> List[Dict[str, Any]]:
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def _save_raw(entries: List[Dict[str, Any]]) -> None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_history() -> List[Dict[str, Any]]:
        """
        Obtiene el historial de beatmaps generados, validando que el archivo .osz exista.
        """
        entries = HistoryManager._load_raw()
        valid_entries = []
        changed = False

        for entry in entries:
            osz_path = entry.get("osz_path")
            if osz_path and os.path.exists(osz_path):
                valid_entries.append(entry)
            else:
                changed = True

        if changed:
            HistoryManager._save_raw(valid_entries)

        return valid_entries

    @staticmethod
    def add_entry(job_data: Dict[str, Any], osz_path: str) -> Dict[str, Any]:
        """
        Registra un nuevo beatmap generado en el historial.
        """
        entries = HistoryManager._load_raw()
        
        file_size_mb = 0.0
        if os.path.exists(osz_path):
            file_size_mb = round(os.path.getsize(osz_path) / (1024 * 1024), 2)

        entry = {
            "job_id": job_data.get("job_id"),
            "title": job_data.get("title") or "Track",
            "artist": job_data.get("artist") or "Artist",
            "target_stars": round(float(job_data.get("difficulty", 7.0)), 1),
            "real_stars": round(float(job_data.get("real_stars", job_data.get("difficulty", 7.0))), 2),
            "aim_stars": job_data.get("aim_stars"),
            "speed_stars": job_data.get("speed_stars"),
            "max_combo": job_data.get("max_combo"),
            "circle_count": job_data.get("circle_count"),
            "slider_count": job_data.get("slider_count"),
            "style_id": job_data.get("style_id", "jump"),
            "mapper_id": job_data.get("mapper_id") or "Neutral",
            "bpm": job_data.get("bpm"),
            "osz_filename": os.path.basename(osz_path),
            "osz_path": osz_path,
            "file_size_mb": file_size_mb,
            "download_url": f"/api/download/{job_data.get('job_id')}",
            "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        # Evitar duplicados por job_id
        entries = [e for e in entries if e.get("job_id") != entry["job_id"]]
        entries.insert(0, entry) # Insertar al principio

        HistoryManager._save_raw(entries)
        return entry

    @staticmethod
    def delete_entry(job_id: str) -> bool:
        """
        Elimina un beatmap del historial y borra su directorio de output.
        """
        entries = HistoryManager._load_raw()
        target_entry = next((e for e in entries if e.get("job_id") == job_id), None)
        
        if not target_entry:
            return False

        # Borrar archivo o carpeta de output
        job_dir = os.path.join(OUTPUT_DIR, job_id)
        if os.path.exists(job_dir):
            try:
                shutil.rmtree(job_dir)
            except Exception:
                pass

        osz_path = target_entry.get("osz_path")
        if osz_path and os.path.exists(osz_path):
            try:
                os.remove(osz_path)
            except Exception:
                pass

        entries = [e for e in entries if e.get("job_id") != job_id]
        HistoryManager._save_raw(entries)
        return True
