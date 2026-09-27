import os
import sys
import asyncio
import subprocess
import glob
import re
from typing import Dict, Any, Callable, Optional
from backend.models.job import JobState, JobStatus
from backend.param_builder import build_inference_args
from backend.osz_packager import OszPackager
from backend.difficulty_calculator import DifficultyCalculator
from backend.difficulty_calibrator import DifficultyCalibrator
from backend.history_manager import HistoryManager
from backend.engine_patcher import ensure_engine_patched

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAPPERATOR_DIR = os.path.join(PROJECT_ROOT, "Mapperatorinator")
MAPPERATOR_PYTHON = os.path.join(MAPPERATOR_DIR, ".venv", "Scripts", "python.exe")

class BeatmapGenerator:
    @staticmethod
    async def run_generation(
        job: JobState,
        audio_path: str,
        update_callback: Optional[Callable[[JobState], None]] = None
    ) -> None:
        """
        Ejecuta Mapperatorinator de forma asíncrona y empaqueta el beatmap final.
        """
        job_temp_dir = os.path.join(PROJECT_ROOT, "temp", job.job_id)
        job_output_dir = os.path.join(PROJECT_ROOT, "output", job.job_id)
        os.makedirs(job_temp_dir, exist_ok=True)
        os.makedirs(job_output_dir, exist_ok=True)

        job.status = JobStatus.GENERATING
        job.progress = 20
        job.message = "Configurando modelo de IA e inicializando tensores..."
        if update_callback:
            update_callback(job)

        # Asegurar que siempre se transmita un BPM fiable
        target_bpm = job.custom_bpm
        if not target_bpm or target_bpm <= 0:
            try:
                from backend.audio_analyzer import AudioAnalyzer
                audio_meta = AudioAnalyzer.analyze_audio(audio_path)
                target_bpm = float(audio_meta.get("bpm", 120.0))
                job.custom_bpm = target_bpm
            except Exception:
                target_bpm = 120.0

        # Construir argumentos para inference.py
        args = build_inference_args(
            audio_path=audio_path,
            output_path=job_temp_dir,
            difficulty=job.difficulty,
            style_id=job.style_id,
            mapper_key=job.mapper_id or "neutral",
            custom_ar=job.custom_ar,
            custom_cs=job.custom_cs,
            custom_od=job.custom_od,
            custom_hp=job.custom_hp,
            custom_sv=job.custom_sv,
            custom_bpm=target_bpm
        )

        cmd = [MAPPERATOR_PYTHON, "-u", "inference.py"] + args

        # Preparar entorno para incluir ffmpeg en PATH desde registro y ubicaciones conocidas
        env = os.environ.copy()
        
        # Buscar ffmpeg en el directorio de winget si no está en PATH
        extra_paths = []
        winget_ffmpeg_dir = r"C:\Users\joeld\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin"
        if os.path.exists(winget_ffmpeg_dir):
            extra_paths.append(winget_ffmpeg_dir)

        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                extra_paths.append(winreg.QueryValueEx(key, "Path")[0])
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                extra_paths.append(winreg.QueryValueEx(key, "Path")[0])
        except Exception:
            pass

        current_path = os.environ.get("PATH", "")
        full_path = ";".join([p for p in extra_paths if p] + [current_path])

        env["PATH"] = full_path
        env["PYO3_USE_ABI3_FORWARD_COMPATIBILITY"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        # Asegurar parches críticos de compatibilidad en el motor
        ensure_engine_patched(MAPPERATOR_DIR)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=MAPPERATOR_DIR,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )

            # Leer salida en tiempo real
            progress_val = 25
            last_lines = []
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                raw_text = line.decode("utf-8", errors="ignore")
                # tqdm usa \r para refrescar la misma línea en terminal
                for subline in raw_text.replace("\r", "\n").split("\n"):
                    decoded_line = subline.strip()
                    if not decoded_line:
                        continue

                    last_lines.append(decoded_line)
                    if len(last_lines) > 20:
                        last_lines.pop(0)

                    # Filtrar mensajes útiles y calcular progreso exacto
                    if "Loading model" in decoded_line or "Downloading" in decoded_line:
                        job.message = "Cargando pesos de la IA en GPU..."
                        progress_val = min(progress_val + 5, 40)
                    elif "Precomputing" in decoded_line or "Encoder" in decoded_line:
                        job.message = "Analizando audio y espectrograma..."
                        progress_val = 45
                    elif "Generating timing" in decoded_line:
                        job.message = "Sincronizando BPM y timing..."
                        progress_val = 55
                    elif "Generating map" in decoded_line:
                        job.message = "Generando notas y sliders con IA..."
                        progress_val = 65
                    elif "%|" in decoded_line: # Barra tqdm
                        match = re.search(r"(\d+)%", decoded_line)
                        if match:
                            pct = int(match.group(1))
                            progress_val = min(85, 45 + int(pct * 0.40))
                            job.message = f"Generando patrones ({pct}%)..."

                job.progress = progress_val
                if update_callback:
                    update_callback(job)

            await process.wait()

            if process.returncode != 0:
                error_snippet = "\n".join(last_lines[-6:]) if last_lines else f"Código {process.returncode}"
                raise RuntimeError(f"Error en motor de IA: {error_snippet}")

            # Buscar archivo .osu generado
            osu_files = glob.glob(os.path.join(job_temp_dir, "**", "*.osu"), recursive=True)
            if not osu_files:
                # Buscar en raíz de temp_dir
                osu_files = glob.glob(os.path.join(job_temp_dir, "*.osu"))

            if not osu_files:
                raise FileNotFoundError("No se encontró el archivo .osu generado por la IA.")

            generated_osu = osu_files[0]

            # Calibración de precisión de dificultad in-situ
            job.message = "Calibrando geometría y espaciado de saltos para alcanzar dificultad objetivo..."
            if update_callback:
                update_callback(job)

            try:
                calib_res = DifficultyCalibrator.calibrate_beatmap(
                    osu_file_path=generated_osu,
                    target_stars=job.difficulty,
                    custom_cs=job.custom_cs,
                    target_bpm=target_bpm
                )
                print(f"[CALIBRATOR] Resultado de calibración: {calib_res}")
            except Exception as calib_err:
                print(f"[WARN] Error en calibrador de dificultad: {calib_err}")

            # Calcular Star Rating oficial con rosu-pp
            diff_data = DifficultyCalculator.calculate_beatmap_difficulty(
                osu_file_path=generated_osu,
                target_stars=job.difficulty
            )
            job.real_stars = diff_data["real_stars"]
            job.aim_stars = diff_data["aim_stars"]
            job.speed_stars = diff_data["speed_stars"]
            job.max_combo = diff_data["max_combo"]
            job.circle_count = diff_data["circles"]
            job.slider_count = diff_data["sliders"]
            job.difficulty_evaluation = diff_data["evaluation"]

            job.status = JobStatus.PACKAGING
            job.progress = 90
            job.message = f"Dificultad calibrada: {job.real_stars:.2f}* (Aim: {job.aim_stars}*, Speed: {job.speed_stars}*). Empaquetando..."
            if update_callback:
                update_callback(job)

            # Nombre de la versión en el juego con la dificultad real calculada
            style_label = job.style_id.capitalize()
            mapper_label = (job.mapper_id or "AI").capitalize()
            version_name = f"{style_label} [{job.real_stars:.2f}* - {mapper_label}]"

            # Nombre limpio para el archivo .osz en el sistema de archivos (sin *, :, ?, etc.)
            clean_title = re.sub(r'[\\/*?:"<>|]', "", job.title or "Track")
            clean_artist = re.sub(r'[\\/*?:"<>|]', "", job.artist or "Artist")
            clean_version = re.sub(r'[\\/*?:"<>|]', "", version_name)
            osz_filename = f"{clean_artist} - {clean_title} [{clean_version}].osz"
            osz_full_path = os.path.join(job_output_dir, osz_filename)

            OszPackager.package_beatmap(
                osu_file_path=generated_osu,
                audio_file_path=audio_path,
                output_osz_path=osz_full_path,
                title=job.title,
                artist=job.artist,
                version_name=version_name
            )

            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.osz_path = osz_full_path
            job.download_url = f"/api/download/{job.job_id}"
            job.message = "¡Beatmap generado y empaquetado con éxito!"

            # Registrar en el historial persistente
            try:
                HistoryManager.add_entry(job.model_dump(), osz_full_path)
            except Exception as hist_err:
                print(f"[WARN] Error registrando en historial: {hist_err}")

            if update_callback:
                update_callback(job)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.message = f"Error durante la generación: {e}"
            if update_callback:
                update_callback(job)
