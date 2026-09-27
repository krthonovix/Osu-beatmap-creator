from typing import Dict, Any, List, Optional

MAPPER_PROFILES: List[Dict[str, Any]] = [
    {
        "id": "neutral",
        "name": "Auto / Neutral",
        "mapper_id": None,
        "description": "El modelo genera libremente según el género y ritmo",
        "tags": ["balanced"]
    },
    {
        "id": "sotarks",
        "name": "Sotarks",
        "mapper_id": 1848318,
        "description": "Aim-heavy, jumps limpios de 1-2, muy jugable y popular",
        "tags": ["jumps", "clean", "flow"]
    },
    {
        "id": "reform",
        "name": "Reform",
        "mapper_id": 3288847,
        "description": "Technical, patrones rítmicos elaborados y sliders creativos",
        "tags": ["technical", "complex", "sliders"]
    },
    {
        "id": "fieryrage",
        "name": "fieryrage",
        "mapper_id": 3533958,
        "description": "Cross-screen jumps agresivos, alto énfasis en ritmo dinámico",
        "tags": ["jumps", "aggressive"]
    },
    {
        "id": "nevo",
        "name": "Nevo",
        "mapper_id": 7451883,
        "description": "Jump maps con flow natural, estética limpia y transiciones suaves",
        "tags": ["jumps", "flow", "clean"]
    },
    {
        "id": "rlc",
        "name": "RLC",
        "mapper_id": 1047883,
        "description": "Alternating, streams cortos, excelente estructura y lectura",
        "tags": ["alternating", "streams", "structured"]
    },
    {
        "id": "monstrata",
        "name": "Monstrata",
        "mapper_id": 2706438,
        "description": "Geometría limpia, sliders fluidos y mapas altamente legibles",
        "tags": ["structured", "sliders", "clean"]
    },
    {
        "id": "lasse",
        "name": "Lasse",
        "mapper_id": 896613,
        "description": "Equilibrio entre jumps y streams consistentes",
        "tags": ["balanced", "streams", "jumps"]
    },
    {
        "id": "doormat",
        "name": "Doormat",
        "mapper_id": 3230571,
        "description": "Technical con patrones complejos y ritmo sincopado",
        "tags": ["technical", "complex"]
    },
    {
        "id": "sing",
        "name": "Sing",
        "mapper_id": 3795679,
        "description": "Pop maps accesibles con streams suaves y buen ritmo",
        "tags": ["flow", "streams"]
    },
    {
        "id": "hollow_wings",
        "name": "Hollow Wings",
        "mapper_id": 416662,
        "description": "Patrones experimentales, sliders largos y flow artístico",
        "tags": ["experimental", "complex", "sliders"]
    }
]

MAP_STYLES: List[Dict[str, Any]] = [
    {
        "id": "jump",
        "name": "Jump Map",
        "description": "Foco en saltos (jumps) entre círculos, ritmo marcado y aim",
        "descriptors": ["skillset/jumps", "style/clean"],
        "negative_descriptors": ["skillset/streams"]
    },
    {
        "id": "stream",
        "name": "Stream Map",
        "description": "Notas consecutivas a alta densidad (streams) siguiendo melodía y batería",
        "descriptors": ["skillset/streams", "style/clean"],
        "negative_descriptors": ["skillset/jumps"]
    },
    {
        "id": "technical",
        "name": "Technical Map",
        "description": "Patrones complejos, sliders elaborados y cambios de ritmo frecuentes",
        "descriptors": ["skillset/technical", "style/complex"],
        "negative_descriptors": []
    },
    {
        "id": "alt",
        "name": "Alternating (Alt)",
        "description": "Patrones continuos que exigen alternar dedos con distancias medias",
        "descriptors": ["skillset/alternating", "style/flow"],
        "negative_descriptors": []
    },
    {
        "id": "slider",
        "name": "Slider-Heavy / Flow",
        "description": "Sliders largos, curvas expresivas y flow suave con menor densidad",
        "descriptors": ["skillset/sliders", "style/flow"],
        "negative_descriptors": ["skillset/streams"]
    },
    {
        "id": "balanced",
        "name": "Equilibrado",
        "description": "Mezcla balanceada de jumps, sliders y streams según la canción",
        "descriptors": ["style/clean", "style/flow"],
        "negative_descriptors": []
    }
]
