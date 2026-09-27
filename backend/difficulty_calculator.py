import os
from typing import Dict, Any, Optional
import rosu_pp_py as rpp

class DifficultyCalculator:
    @staticmethod
    def calculate_beatmap_difficulty(osu_file_path: str, target_stars: Optional[float] = None) -> Dict[str, Any]:
        """
        Calcula el Star Rating oficial y desglosado de un archivo .osu
        utilizando rosu-pp-py (algoritmo oficial de osu! / ppy).
        """
        if not os.path.exists(osu_file_path):
            return {
                "real_stars": 0.0,
                "aim_stars": 0.0,
                "speed_stars": 0.0,
                "max_combo": 0,
                "circles": 0,
                "sliders": 0,
                "spinners": 0,
                "difference": 0.0,
                "evaluation": "Archivo no encontrado"
            }

        try:
            bm = rpp.Beatmap(path=osu_file_path)
            diff = rpp.Difficulty().calculate(bm)

            real_stars = round(float(diff.stars), 2)
            aim_stars = round(float(diff.aim), 2)
            speed_stars = round(float(diff.speed), 2)
            max_combo = int(diff.max_combo)
            circles = int(diff.n_circles)
            sliders = int(diff.n_sliders)
            spinners = int(diff.n_spinners)

            difference = round(real_stars - target_stars, 2) if target_stars is not None else 0.0

            # Evaluación textual intuitiva
            if target_stars is None:
                evaluation = "Cálculo oficial completado"
            elif abs(difference) <= 0.15:
                evaluation = f"🎯 Calibración exacta con el objetivo ({real_stars}★ vs {target_stars}★)"
            elif difference < -0.15:
                evaluation = f"⚠️ Dificultad real menor ({real_stars}★ vs {target_stars}★)"
            else:
                evaluation = f"⚡ Dificultad real superior ({real_stars}★ vs {target_stars}★)"

            return {
                "real_stars": real_stars,
                "aim_stars": aim_stars,
                "speed_stars": speed_stars,
                "max_combo": max_combo,
                "circles": circles,
                "sliders": sliders,
                "spinners": spinners,
                "difference": difference,
                "evaluation": evaluation
            }

        except Exception as e:
            return {
                "real_stars": target_stars or 0.0,
                "aim_stars": 0.0,
                "speed_stars": 0.0,
                "max_combo": 0,
                "circles": 0,
                "sliders": 0,
                "spinners": 0,
                "difference": 0.0,
                "evaluation": f"Error calculando métricas: {e}"
            }
