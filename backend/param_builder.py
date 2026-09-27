from typing import Dict, Any, List, Optional
from backend.mapper_profiles import MAPPER_PROFILES, MAP_STYLES

def calculate_difficulty_stats(stars: float) -> Dict[str, float]:
    """
    Calcula valores canónicos de osu! estándar según la cantidad de estrellas:
    AR (Approach Rate), CS (Circle Size), OD (Overall Difficulty), HP (Drain Rate), SV (Slider Velocity)
    """
    stars = max(1.0, min(10.0, stars))
    
    if stars <= 3.0:
        ar = round(6.0 + (stars - 1.0) * 0.75, 1) # 1* -> 6.0, 3* -> 7.5
        cs = 3.5
        od = round(5.0 + (stars - 1.0) * 1.0, 1)
        hp = 3.5
        sv = 1.4
    elif stars <= 5.0:
        ar = round(7.5 + (stars - 3.0) * 0.65, 1) # 3* -> 7.5, 5* -> 8.8
        cs = 4.0
        od = round(7.0 + (stars - 3.0) * 0.75, 1) # 3* -> 7.0, 5* -> 8.5
        hp = 5.0
        sv = 1.6
    elif stars <= 7.0:
        ar = round(8.8 + (stars - 5.0) * 0.35, 1) # 5* -> 8.8, 7* -> 9.5
        cs = 4.2
        od = round(8.5 + (stars - 5.0) * 0.35, 1) # 5* -> 8.5, 7* -> 9.2
        hp = 5.0
        sv = 1.82
    else: # 7* a 10*
        ar = round(min(10.0, 9.5 + (stars - 7.0) * 0.17), 1) # 7* -> 9.5, 10* -> 10.0
        cs = 4.2 if stars < 8.0 else 4.4
        od = round(min(10.0, 9.2 + (stars - 7.0) * 0.27), 1)
        hp = 5.5
        sv = round(1.82 + (stars - 7.0) * 0.15, 2)

    return {
        "ar": ar,
        "cs": cs,
        "od": od,
        "hp": hp,
        "sv": sv
    }

def build_inference_args(
    audio_path: str,
    output_path: str,
    difficulty: float,
    style_id: str = "jump",
    mapper_key: str = "sotarks",
    custom_cs: Optional[float] = None,
    custom_sv: Optional[float] = None,
    hitsounded: bool = False
) -> List[str]:
    """
    Construye la lista de argumentos en formato Hydra override para inference.py de Mapperatorinator.
    """
    stats = calculate_difficulty_stats(difficulty)
    cs = custom_cs if custom_cs is not None else stats["cs"]
    sv = custom_sv if custom_sv is not None else stats["sv"]
    
    # Buscar mapper
    mapper_info = next((m for m in MAPPER_PROFILES if m["id"] == mapper_key), None)
    mapper_id = mapper_info["mapper_id"] if mapper_info else None
    
    # Buscar estilo
    style_info = next((s for s in MAP_STYLES if s["id"] == style_id), None)
    descriptors = style_info["descriptors"] if style_info else ["style/clean"]
    neg_descriptors = style_info["negative_descriptors"] if style_info else []

    # Normalizar rutas con forward slash para evitar problemas de escape en Windows/Hydra
    norm_audio = audio_path.replace("\\", "/")
    norm_output = output_path.replace("\\", "/")

    # Formato de lista para Hydra
    desc_str = "[" + ",".join([f"'{d}'" for d in descriptors]) + "]"

    args = [
        f"audio_path='{norm_audio}'",
        f"output_path='{norm_output}'",
        "gamemode=0", # osu! standard
        f"difficulty={round(difficulty, 2)}",
        f"approach_rate={stats['ar']}",
        f"overall_difficulty={stats['od']}",
        f"hp_drain_rate={stats['hp']}",
        f"circle_size={cs}",
        f"slider_multiplier={sv}",
        f"descriptors={desc_str}",
        f"hitsounded={str(hitsounded).lower()}",
        "in_context=[NONE]",
        "precision='fp16'",
        "year=2024"
    ]

    if mapper_id is not None:
        args.append(f"mapper_id={mapper_id}")

    if neg_descriptors:
        neg_desc_str = "[" + ",".join([f"'{d}'" for d in neg_descriptors]) + "]"
        args.append(f"negative_descriptors={neg_desc_str}")

    return args
