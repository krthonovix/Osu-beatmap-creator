"""
engine_patcher.py - Garantiza la compatibilidad y correcciones críticas en Mapperatorinator.
Asegura que:
1. config.py admita BPM float (evita crash de Hydra).
2. inference.py incluya la importación de DictConfig.
3. inference.py desinfecte marcas de tiempo anómalas antes de resnap_events (evita silencios de intro).
"""

import os
import re

def ensure_engine_patched(mapperator_dir: str) -> None:
    config_path = os.path.join(mapperator_dir, "config.py")
    inference_path = os.path.join(mapperator_dir, "inference.py")

    # 1. Parchear config.py para BPM float
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg_content = f.read()
            if "bpm: Optional[int]" in cfg_content:
                cfg_content = cfg_content.replace("bpm: Optional[int]", "bpm: Optional[float]")
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(cfg_content)
        except Exception as e:
            print(f"[WARN] No se pudo verificar parche de config.py: {e}")

    # 2. Parchear inference.py para DictConfig y TimingPoint
    if os.path.exists(inference_path):
        try:
            with open(inference_path, "r", encoding="utf-8") as f:
                inf_content = f.read()

            modified = False

            # Asegurar importación de DictConfig
            if "DictConfig" not in inf_content:
                inf_content = inf_content.replace(
                    "from omegaconf import OmegaConf",
                    "from omegaconf import OmegaConf, DictConfig"
                )
                modified = True

            # Asegurar importación de numpy, timedelta y TimingPoint
            if "from slider import Beatmap, TimingPoint" not in inf_content:
                inf_content = inf_content.replace(
                    "from slider import Beatmap",
                    "import numpy as np\nfrom datetime import timedelta\nfrom slider import Beatmap, TimingPoint"
                )
                modified = True

            # Asegurar sanitización de marcas de tiempo antes de resnap
            if "# Sanitize timing points before resnap" not in inf_content and "resnap_events" in inf_content:
                timing_fix = '''        # Sanitize timing points before resnap to eliminate corrupt redlines (e.g. 19417ms) and empty intros
        if timing is not None and len(timing) > 0:
            try:
                valid_mpbs = [tp.ms_per_beat for tp in timing if getattr(tp, 'parent', None) is None and 150.0 <= tp.ms_per_beat <= 1200.0]
                fallback_mpb = float(np.median(valid_mpbs)) if valid_mpbs else (60000.0 / args.bpm if getattr(args, 'bpm', None) and args.bpm > 0 else 300.0)
                cleaned_timing = []
                for tp in timing:
                    if getattr(tp, 'parent', None) is None and (tp.ms_per_beat > 1500.0 or tp.ms_per_beat < 100.0):
                        cleaned_timing.append(TimingPoint(
                            tp.offset,
                            fallback_mpb,
                            getattr(tp, 'meter', 4),
                            getattr(tp, 'sample_type', 1),
                            getattr(tp, 'sample_set', 0),
                            getattr(tp, 'volume', 100),
                            None,
                            getattr(tp, 'kiai_mode', False)
                        ))
                    else:
                        cleaned_timing.append(tp)
                if cleaned_timing and cleaned_timing[0].offset.total_seconds() > 5.0:
                    first_tp = cleaned_timing[0]
                    cleaned_timing.insert(0, TimingPoint(
                        timedelta(seconds=0),
                        fallback_mpb,
                        getattr(first_tp, 'meter', 4),
                        getattr(first_tp, 'sample_type', 1),
                        getattr(first_tp, 'sample_set', 0),
                        getattr(first_tp, 'volume', 100),
                        None,
                        False
                    ))
                timing = cleaned_timing
            except Exception as e:
                logger.warning(f"Error sanitizing timing points: {e}")

        # Resnap timing events'''
                inf_content = inf_content.replace("        # Resnap timing events", timing_fix)
                modified = True

            if modified:
                with open(inference_path, "w", encoding="utf-8") as f:
                    f.write(inf_content)
        except Exception as e:
            print(f"[WARN] No se pudo verificar parche de inference.py: {e}")
