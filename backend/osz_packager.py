import os
import shutil
import zipfile
import re
from typing import Optional

class OszPackager:
    @staticmethod
    def fix_osu_metadata(
        osu_path: str,
        title: str,
        artist: str,
        version_name: str,
        audio_filename: str = "audio.mp3",
        creator_name: str = "Ai Mapper"
    ) -> None:
        """
        Asegura que el archivo .osu tenga los títulos, audio y versión correctos.
        """
        if not os.path.exists(osu_path):
            return

        with open(osu_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Actualizar AudioFilename
        content = re.sub(r"AudioFilename:\s*.*", f"AudioFilename: {audio_filename}", content)
        
        # Actualizar Metadata
        content = re.sub(r"Title:\s*.*", f"Title:{title}", content)
        content = re.sub(r"TitleUnicode:\s*.*", f"TitleUnicode:{title}", content)
        content = re.sub(r"Artist:\s*.*", f"Artist:{artist}", content)
        content = re.sub(r"ArtistUnicode:\s*.*", f"ArtistUnicode:{artist}", content)
        content = re.sub(r"Creator:\s*.*", f"Creator:{creator_name}", content)
        content = re.sub(r"Version:\s*.*", f"Version:{version_name}", content)

        with open(osu_path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def package_beatmap(
        osu_file_path: str,
        audio_file_path: str,
        output_osz_path: str,
        title: str,
        artist: str,
        version_name: str = "AI Generated"
    ) -> str:
        """
        Empaqueta el archivo .osu y el audio .mp3 en un archivo .osz.
        """
        # Preparar nombre de audio limpio dentro del osz
        internal_audio_name = "audio.mp3"
        
        # Actualizar cabecera del archivo .osu
        OszPackager.fix_osu_metadata(
            osu_path=osu_file_path,
            title=title,
            artist=artist,
            version_name=version_name,
            audio_filename=internal_audio_name
        )

        os.makedirs(os.path.dirname(os.path.abspath(output_osz_path)), exist_ok=True)
        osu_basename = os.path.basename(osu_file_path)

        # Crear archivo zip renombrado a .osz
        with zipfile.ZipFile(output_osz_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(audio_file_path, arcname=internal_audio_name)
            zipf.write(osu_file_path, arcname=osu_basename)

        return output_osz_path
