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

        # Construir argumentos para inference.py
        args = build_inference_args(
            audio_path=audio_path,
            output_path=job_temp_dir,
            difficulty=job.difficulty,
            style_id=job.style_id,
            mapper_key=job.mapper_id or "neutral"
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
                
                decoded_line = line.decode("utf-8", errors="ignore").strip()
                if not decoded_line:
                    continue

                last_lines.append(decoded_line)
                if len(last_lines) > 20:
                    last_lines.pop(0)

                # Filtrar mensajes útiles y calcular progreso aproximado
                if "Loading model" in decoded_line or "Downloading" in decoded_line:
                    job.message = "Descargando / Cargando pesos del modelo..."
                    progress_val = min(progress_val + 5, 45)
                elif "Spectrogram" in decoded_line or "Audio" in decoded_line:
                    job.message = "Procesando espectrograma y características de audio..."
                    progress_val = max(progress_val, 50)
                elif "Sampling" in decoded_line or "Diffusion" in decoded_line or "Generating" in decoded_line:
                    job.message = "Generando notas y sliders con modelo de difusión..."
                    progress_val = min(progress_val + 2, 85)
                elif "%|" in decoded_line: # Barra tqdm
                    match = re.search(r"(\d+)%", decoded_line)
                    if match:
                        pct = int(match.group(1))
                        # Mapear 0-100% de la barra a 40-85% del proceso global
                        progress_val = 40 + int(pct * 0.45)
                    job.message = f"Generando geometría del mapa: {decoded_line[:60]}"

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
            job.status = JobStatus.PACKAGING
            job.progress = 90
            job.message = "Empaquetando archivo .osz de osu!..."
            if update_callback:
                update_callback(job)

            # Nombre de la versión en el juego
            style_label = job.style_id.capitalize()
            mapper_label = (job.mapper_id or "AI").capitalize()
            version_name = f"{style_label} [{job.difficulty:.1f}★ - {mapper_label}]"

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
            if update_callback:
                update_callback(job)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.message = f"Error durante la generación: {e}"
            if update_callback:
                update_callback(job)
