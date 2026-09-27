import os
import re
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import rosu_pp_py as rpp

class DifficultyCalibrator:
    """
    Calibrador de Precisión de Dificultad y Calidad Geométrica para osu! beatmaps.
    - Corrige anomalías de timing y huecos largos al inicio.
    - Preserva la forma rígida y longitud exacta de sliders para evitar colisiones con círculos.
    - Calibra el Star Rating oficial con rosu-pp en bucle cerrado (±0.03★).
    """

    @classmethod
    def sanitize_timing_points(cls, lines: List[str], target_bpm: Optional[float] = None) -> List[str]:
        """
        Detecta y repara timing points anómalos (por ejemplo beatLength > 1500ms o < 100ms)
        y asegura que exista un punto de sincronización inicial desde 0ms para evitar silencios.
        """
        valid_mpbs: List[float] = []
        in_tp = False

        for l in lines:
            if l.strip() == "[TimingPoints]":
                in_tp = True
                continue
            if in_tp and l.strip().startswith("["):
                in_tp = False
            if in_tp and l.strip():
                parts = l.strip().split(",")
                # El campo 6 (índice 6) es 'uninherited' (1 = redline / BPM change)
                if len(parts) >= 7 and parts[6] == "1":
                    try:
                        mpb = float(parts[1])
                        if 150.0 <= mpb <= 1200.0:
                            valid_mpbs.append(mpb)
                    except ValueError:
                        pass

        if valid_mpbs:
            clean_mpb = float(np.median(valid_mpbs))
        elif target_bpm and target_bpm > 0:
            clean_mpb = round(60000.0 / target_bpm, 4)
        else:
            clean_mpb = 300.0  # 200 BPM default seguro

        out_lines: List[str] = []
        in_tp = False
        first_redline_checked = False

        for l in lines:
            if l.strip() == "[TimingPoints]":
                in_tp = True
                out_lines.append(l)
                continue
            if in_tp and l.strip().startswith("["):
                in_tp = False

            if in_tp and l.strip():
                parts = l.strip().split(",")
                if len(parts) >= 7 and parts[6] == "1":
                    try:
                        offset = float(parts[0])
                        mpb = float(parts[1])

                        # Si el primer punto de BPM aparece tarde (> 5s), insertar uno al inicio (0ms)
                        if not first_redline_checked:
                            first_redline_checked = True
                            if offset > 5000.0:
                                out_lines.append(f"0,{clean_mpb:.4f},4,2,-1,100,1,0")

                        # Si el beatLength es anómalo (ej: 19417ms que genera un vacío de 20s)
                        if mpb > 1500.0 or mpb < 100.0:
                            parts[1] = f"{clean_mpb:.4f}"
                            l = ",".join(parts)
                    except Exception:
                        pass
                out_lines.append(l)
            elif not in_tp:
                out_lines.append(l)

        return out_lines

    @classmethod
    def resolve_slider_collisions(cls, objects: List[List[str]]) -> List[List[str]]:
        """
        Inspecciona pares de objetos consecutivos para garantizar que ningún círculo
        colisione ni se encime con el cuerpo o cola de un slider previo.
        """
        for i in range(len(objects) - 1):
            curr = objects[i]
            nxt = objects[i + 1]

            curr_type = int(curr[3])
            # Si el actual es un slider (bit 1, valor 2)
            if (curr_type & 2) and len(curr) >= 8:
                try:
                    s_x, s_y, s_t = float(curr[0]), float(curr[1]), float(curr[2])
                    n_x, n_y, n_t = float(nxt[0]), float(nxt[1]), float(nxt[2])

                    # Obtener coordenadas de la cola o último punto del slider
                    curve_parts = curr[5].split("|")
                    tail_x, tail_y = s_x, s_y
                    for pt in reversed(curve_parts[1:]):
                        if ":" in pt:
                            tx, ty = map(float, pt.split(":"))
                            tail_x, tail_y = tx, ty
                            break

                    # Distancia de la siguiente nota a la cabeza y a la cola del slider
                    dist_to_tail = np.hypot(n_x - tail_x, n_y - tail_y)
                    dist_to_head = np.hypot(n_x - s_x, n_y - s_y)

                    # Si el siguiente objeto ocurre casi inmediatamente y está encimado (< 55px)
                    if (n_t - s_t) < 500.0 and (dist_to_tail < 55.0 or dist_to_head < 55.0):
                        # Desplazar el siguiente objeto en dirección de salida para despejarlo
                        angle = np.arctan2(n_y - tail_y, n_x - tail_x) if dist_to_tail > 1.0 else 0.5
                        shift_dist = 70.0
                        new_nx = max(16.0, min(496.0, n_x + np.cos(angle) * shift_dist))
                        new_ny = max(16.0, min(368.0, n_y + np.sin(angle) * shift_dist))

                        nxt[0] = str(int(round(new_nx)))
                        nxt[1] = str(int(round(new_ny)))
                except Exception:
                    pass

        return objects

    @classmethod
    def calibrate_beatmap(
        cls,
        osu_file_path: str,
        target_stars: float,
        custom_cs: Optional[float] = None,
        target_bpm: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calibra el archivo .osu in-situ para alcanzar el target_stars preservando
        la rigidez de sliders, eliminando vacíos de timing y colisiones.
        """
        if not os.path.exists(osu_file_path) or target_stars <= 0:
            return {"calibrated": False, "factor": 1.0, "real_stars": target_stars}

        with open(osu_file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        raw_lines = content.split("\n")

        # 1. Sanitizar timing points para evitar anomalías y huecos al inicio
        lines = cls.sanitize_timing_points(raw_lines, target_bpm=target_bpm)

        # Medición inicial con timing limpio
        temp_content = "\n".join(lines)
        initial_bm = rpp.Beatmap(bytes=temp_content.encode("utf-8"))
        initial_diff = rpp.Difficulty().calculate(initial_bm)
        initial_sr = round(float(initial_diff.stars), 2)

        # Parsear hit objects
        parsed_objects: List[List[str]] = []
        in_ho = False

        for line in lines:
            line_str = line.strip()
            if line_str == "[HitObjects]":
                in_ho = True
                continue
            if in_ho and line_str.startswith("["):
                in_ho = False
            if in_ho and line_str:
                parts = line_str.split(",")
                if len(parts) >= 4:
                    parsed_objects.append(parts)

        if len(parsed_objects) < 2:
            return {
                "calibrated": False,
                "factor": 1.0,
                "initial_stars": initial_sr,
                "real_stars": initial_sr
            }

        # Agrupar en combos
        raw_combos: List[List[List[str]]] = []
        current_combo: List[List[str]] = []
        for p in parsed_objects:
            obj_type = int(p[3])
            if (obj_type & 4) and len(current_combo) > 0:
                raw_combos.append(current_combo)
                current_combo = [p]
            else:
                current_combo.append(p)
        if current_combo:
            raw_combos.append(current_combo)

        # Fusionar combos de 1 sola nota con el anterior para estabilidad del centroide
        combos: List[List[List[str]]] = []
        for c in raw_combos:
            if len(c) == 1 and combos:
                combos[-1].extend(c)
            else:
                combos.append(c)

        # Función de transformación y evaluación de candidatos
        def evaluate_factor(factor: float) -> Tuple[float, float, float, str]:
            scaled_parsed: List[List[str]] = []
            for combo in combos:
                xs = [float(p[0]) for p in combo]
                ys = [float(p[1]) for p in combo]
                cx, cy = float(np.mean(xs)), float(np.mean(ys))

                nxs = [cx + factor * (x - cx) for x in xs]
                nys = [cy + factor * (y - cy) for y in ys]

                min_x, max_x = min(nxs), max(nxs)
                min_y, max_y = min(nys), max(nys)

                shift_x = 0.0
                if min_x < 16.0:
                    shift_x = 16.0 - min_x
                elif max_x > 496.0:
                    shift_x = 496.0 - max_x

                shift_y = 0.0
                if min_y < 16.0:
                    shift_y = 16.0 - min_y
                elif max_y > 368.0:
                    shift_y = 368.0 - max_y

                for i, p in enumerate(combo):
                    new_p = list(p)
                    ox, oy = float(p[0]), float(p[1])
                    nx = max(8.0, min(504.0, nxs[i] + shift_x))
                    ny = max(8.0, min(376.0, nys[i] + shift_y))
                    new_p[0] = str(int(round(nx)))
                    new_p[1] = str(int(round(ny)))

                    # SLIDERS: Traslación rígida exacta (dx, dy).
                    # ¡NO estiramos pixelLength ni deformamos el slider para no colisionar con círculos!
                    obj_type = int(p[3])
                    if (obj_type & 2) and len(p) >= 8:
                        dx = nx - ox
                        dy = ny - oy
                        curve_data = p[5].split("|")
                        new_curve = [curve_data[0]]
                        for pt in curve_data[1:]:
                            if ":" in pt:
                                px, py = map(float, pt.split(":"))
                                c_x = max(8.0, min(504.0, px + dx))
                                c_y = max(8.0, min(376.0, py + dy))
                                new_curve.append(f"{int(round(c_x))}:{int(round(c_y))}")
                            else:
                                new_curve.append(pt)
                        new_p[5] = "|".join(new_curve)
                        # Longitud original p[7] intacta (respeta la duración musical)

                    scaled_parsed.append(new_p)

            # Resolver cualquier colisión residual entre sliders y círculos
            scaled_parsed = cls.resolve_slider_collisions(scaled_parsed)

            out_lines = []
            in_ho_section = False
            for l in lines:
                if custom_cs is not None and l.startswith("CircleSize:"):
                    out_lines.append(f"CircleSize:{custom_cs}")
                    continue
                if l.strip() == "[HitObjects]":
                    in_ho_section = True
                    out_lines.append(l)
                    for sp in scaled_parsed:
                        out_lines.append(",".join(sp))
                    continue
                if in_ho_section and l.strip().startswith("["):
                    in_ho_section = False
                if not in_ho_section:
                    out_lines.append(l)

            mod_str = "\n".join(out_lines)
            cand_bm = rpp.Beatmap(bytes=mod_str.encode("utf-8"))
            d = rpp.Difficulty().calculate(cand_bm)
            return float(d.stars), float(d.aim), float(d.speed), mod_str

        # Búsqueda binaria para encontrar el factor exacto de escala
        low = 0.2
        high = 3.5
        best_diff = 999.0
        best_mod = temp_content
        best_sr = initial_sr
        best_aim = float(initial_diff.aim)
        best_speed = float(initial_diff.speed)
        best_factor = 1.0

        for _ in range(16):
            mid = (low + high) / 2.0
            sr, aim, speed, mod_candidate = evaluate_factor(mid)
            diff = sr - target_stars

            if abs(diff) < abs(best_diff):
                best_diff = diff
                best_mod = mod_candidate
                best_sr = sr
                best_aim = aim
                best_speed = speed
                best_factor = mid

            if abs(diff) <= 0.03:
                break

            if sr < target_stars:
                low = mid
            else:
                high = mid

        # Sobrescribir archivo con la versión calibrada, sin colisiones y con timing limpio
        with open(osu_file_path, "w", encoding="utf-8") as f:
            f.write(best_mod)

        return {
            "calibrated": True,
            "factor": round(best_factor, 3),
            "initial_stars": initial_sr,
            "real_stars": round(best_sr, 2),
            "aim_stars": round(best_aim, 2),
            "speed_stars": round(best_speed, 2),
            "difference": round(best_sr - target_stars, 2)
        }
