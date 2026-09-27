# 🎵 AI Osu! Beatmap Creator — Plan de Implementación

> **Fecha:** Septiembre 2026  
> **Objetivo:** Sistema web local que genere beatmaps de osu! reales y jugables a partir de un `.mp3`, con selección de estilo de mapa y estilo de mapper (Sotarks, Reform, etc.)

---

## ✅ Contexto del Usuario (Confirmado)

| Pregunta | Respuesta | Impacto en el Desarrollo |
|----------|-----------|--------------------------|
| GPU | **GTX 1660 Super — 6 GB VRAM** | ✅ Generación con CUDA (~1-2 min/mapa) |
| Python | **3.14.3** en `C:\Python314\python.exe` | ⚠️ Ver nota abajo |
| FFmpeg | **No instalado** | Hay que instalarlo (parte del setup) |
| Imagen de fondo | **Sin imagen** | El usuario la pone a mano |
| Modelos de mapper | **Ya vienen pre-entrenados en Mapperatorinator** | ✅ No hay que re-entrenar nada |

### ⚠️ Nota sobre Python 3.14

El README de Mapperatorinator dice "usar Python 3.10, versiones posteriores *podrían* no ser compatibles". Sin embargo, al revisar el `requirements.txt` actual:

- Incluye `audioop-lts` — paquete que existe **exclusivamente para Python 3.13+**
- Incluye `PyTorch 2.10` — que tiene **soporte oficial para Python 3.14**
- Esto indica que el proyecto **ya evolucionó** para soportar Python moderno

**Estrategia:** Usaremos tu Python 3.14 directamente con un entorno virtual. Si hay algún paquete puntual que no compile, lo resolveremos en el momento.

### ⚠️ GTX 1660 Super — 6 GB VRAM

Con 6 GB VRAM la generación **funciona**. El modelo principal de osuT5 cabe en memoria. Si hay problemas de OOM (Out Of Memory), Mapperatorinator tiene modo CPU como fallback automático, aunque sería mucho más lento.

---

## 1. Tipo de Proyecto

**App Web Local — FastAPI (Python) + HTML/CSS/JS**

- ✅ Funciona **100% offline** — tus canciones no salen de tu PC
- ✅ UI con drag & drop, previsualización, barra de progreso en tiempo real
- ✅ Python = lenguaje nativo del ecosistema ML de osu!
- ✅ Resultado: `.osz` que arrastras a osu! directamente
- ✅ No requiere instalar nada extra más allá de Python

---

## 2. La IA Detrás del Proyecto: Mapperatorinator

### ¿Por qué no un LLM (ChatGPT, Gemini)?

Un LLM general **no puede** generar beatmaps reales porque no comprende:
- Coordenadas en píxeles (campo de 512×384)
- Sincronización en milisegundos con el audio
- La física de spacing y approach rate que hace un mapa *jugable*
- Los patrones de spacing y flow de cada mapper

### La Solución: Mapperatorinator (Estado del Arte)

**[Mapperatorinator](https://github.com/OliBomby/Mapperatorinator)** by OliBomby es el mejor generador de beatmaps con IA que existe. Internamente usa `osuT5` (transformer) + `osu-diffusion` (modelo de difusión), entrenado durante ~5700 horas de GPU en miles de beatmaps reales.

**¿Y los estilos de mapper? — Para responderte directamente:**

Sí, **ya están pre-entrenados**. El modelo fue entrenado sobre una base de datos masiva de beatmaps de osu! que incluye mapas de Sotarks, Reform y cientos de mappers más. Para imitar el estilo de un mapper, solo hay que pasar su **user ID de osu!** como parámetro `mapper_id` al invocar `inference.py`. El modelo ya aprendió los patrones de cada uno.

Además de `mapper_id`, Mapperatorinator soporta **descriptors** (tags de estilo):

```
descriptors = [
  "skillset/streams",      # Para stream maps
  "skillset/jumps",        # Para jump maps
  "skillset/technical",    # Para technical maps
  "skillset/alternating",  # Para alt maps
  "skillset/sliders",      # Para slider-heavy
  "style/clean",           # Estética limpia
  "style/flow",            # Buen flow
  "style/complex",         # Patrones complejos
  ...
]
```

Estos descriptors son **la clave** para el selector de estilo de mapa que haremos.

### Lo Que Construiremos Nosotros

Nuestro proyecto es un **wrapper con mejor UX** alrededor de Mapperatorinator:

1. **Interfaz propia** — drag & drop, más amigable, en español
2. **Lógica de parámetros** — traducir "quiero un stream map de 7★ estilo Sotarks" → `mapper_id=1848318 difficulty=7.0 descriptors=['skillset/streams']`
3. **Análisis de audio previo** — mostrar BPM, duración, y energía antes de generar
4. **Empaquetado** — tomar el `.osu` generado y crear el `.osz` listo para importar

---

## 3. Arquitectura General

```
┌───────────────────────────────────────────────────────────────┐
│                     NUESTRO PROYECTO                          │
│                                                               │
│   Frontend (HTML/CSS/JS — dark theme osu!)                    │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  1. Drag & Drop .mp3                                 │    │
│   │  2. Análisis previo: BPM, duración, energía          │    │
│   │  3. Estilo de Mapa: [Stream] [Jump] [Technical]...   │    │
│   │  4. Mapper: [Sotarks ▼] → dropdown con mappers       │    │
│   │  5. Dificultad: ━━━━●━━━ 7.0★                        │    │
│   │  6. [GENERAR] → barra de progreso en tiempo real     │    │
│   │  7. [DESCARGAR .osz]                                 │    │
│   └──────────────────────────────────────────────────────┘    │
│              │                                                │
│   Backend FastAPI (Python 3.14)                               │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  audio_analyzer.py   → BPM, energía, duración        │    │
│   │  param_builder.py    → Construye los args de IA      │    │
│   │  mapper_profiles.py  → BD de mapper IDs y estilos    │    │
│   │  generator.py        → Invoca Mapperatorinator        │    │
│   │  osz_packager.py     → Crea el .osz final             │    │
│   │  main.py             → API REST + Server-Sent Events  │    │
│   └──────────────────────────────────────────────────────┘    │
│              │                                                │
│   Mapperatorinator / inference.py (subproceso Python)         │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  osuT5 (Transformer) — genera ritmo y timing          │    │
│   │  osu-diffusion — genera coordenadas exactas           │    │
│   │  GPU: GTX 1660 Super (CUDA)                          │    │
│   │  Output: archivo .osu válido                         │    │
│   └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

---

## 4. Pipeline Completo

```
.mp3 subido por el usuario
        │
        ▼
[1] Análisis de Audio (librosa) — NUESTRO CÓDIGO
    ├─ Detecta BPM
    ├─ Duración total
    ├─ Curva de energía (intro/coro/outro)
    └─ ID3 tags (artista, título)
        │
        ▼
[2] Construcción de Parámetros — NUESTRO CÓDIGO
    ├─ Estilo elegido  → descriptors[] apropiados
    ├─ Mapper elegido  → mapper_id (osu! user ID)
    ├─ Star rating     → difficulty=7.0
    └─ Dificultad      → circle_size, slider_multiplier
        │
        ▼
[3] Invocación de Mapperatorinator — IA CORE
    │  Comando real generado:
    │  python inference.py
    │    audio_path="cancion.mp3"
    │    output_path="./output/"
    │    gamemode=0
    │    difficulty=7.0
    │    mapper_id=1848318
    │    descriptors="['skillset/jumps','style/clean']"
    │    in_context=[TIMING]
    │    hitsounded=false
    │
    └─ Output: ./output/cancion.osu
        │
        ▼
[4] Post-procesamiento — NUESTRO CÓDIGO
    ├─ Agregar metadata (título, artista, version, creator="AI")
    └─ Verificar que el .osu es válido (parsear y validar)
        │
        ▼
[5] Empaquetado .osz — NUESTRO CÓDIGO
    ├─ Crear carpeta: {artista} - {título}/
    ├─ Copiar: audio.mp3 + archivo.osu
    └─ Comprimir como .zip → renombrar a .osz
        │
        ▼
Usuario descarga el .osz → Arrastra a osu! → ¡A jugar!
```

---

## 5. Los Mappers Pre-entrenados y Sus IDs

Estos son los mappers que incluiremos en la UI. Sus estilos ya están en el modelo:

| Mapper | osu! User ID | Estilo Característico |
|--------|-------------|----------------------|
| **Sotarks** | 1848318 | Aim-heavy, jumps limpios, muy jugable, popular |
| **Reform** | 3288847 | Technical, sliders creativos, patrones elaborados |
| **RLC** | 1047883 | Alt-focused, streams cortos, estructurado |
| **Nevo** | 7451883 | Jump maps con flow natural, estética limpia |
| **Lasse** | 896613 | Jumps y streams balanceados, consistente |
| **Monstrata** | 2706438 | Sliders fluidos, bien estructurado |
| **Doormat** | 3230571 | Technical, ritmos complejos |
| **Sing** | 3795679 | Pop maps, sliders suaves, accesible |
| **Hollow Wings** | 416662 | Sliders artísticos muy elaborados |
| **Sin estilo (Neutro)** | *(sin mapper_id)* | El modelo decide libremente |

> **Respuesta a tu pregunta:** Sí, todos estos estilos **ya vienen pre-entrenados** en Mapperatorinator. Solo hay que pasarle el ID de osu! del mapper y automáticamente imita su estilo. No hay que hacer ningún entrenamiento adicional.

---

## 6. Estilos de Mapa y Sus Descriptors

Cada estilo que el usuario elige se traduce en `descriptors[]` para la IA:

| Estilo UI | Descriptors para IA | Descripción |
|-----------|--------------------|-|
| **Stream** | `['skillset/streams', 'style/clean']` | Notas consecutivas rápidas |
| **Jump** | `['skillset/jumps', 'style/flow']` | Saltos grandes entre notas |
| **Technical** | `['skillset/technical', 'style/complex']` | Patrones complejos, sliders elaborados |
| **Alt** | `['skillset/alternating']` | Alternación de dedos |
| **Slider-Heavy** | `['skillset/sliders', 'style/flow']` | Sliders largos, pocas notas |
| **Sin estilo** | `[]` | Libre — el modelo decide |

---

## 7. Star Rating → Parámetros de Dificultad

La estrella de dificultad elegida se traduce automáticamente así:

| Star Rating | AR | CS | OD | HP | Slider Mult |
|-------------|----|----|----|----|-------------|
| 3★ | 7.5 | 4.0 | 7.0 | 4.0 | 1.4 |
| 4★ | 8.0 | 4.2 | 8.0 | 5.0 | 1.6 |
| 5★ | 8.5 | 4.2 | 8.5 | 5.0 | 1.7 |
| 6★ | 9.0 | 4.2 | 9.0 | 5.0 | 1.8 |
| **7★** | **9.5** | **4.2** | **9.0** | **5.0** | **1.82** |
| 8★ | 9.8 | 4.5 | 9.5 | 5.5 | 2.0 |
| 9★ | 10.0 | 4.5 | 10.0 | 6.0 | 2.2 |

*(Basado en los valores de mapas reales de 7★ como los de Sotarks en tu colección)*

---

## 8. Estructura de Archivos del Proyecto

```
E:\ownProjects\creatorOfBeatmapsOsu\
│
├── PLAN_DE_IMPLEMENTACION.md      ← Este archivo
│
├── Mapperatorinator\              ← Clonar aquí (git clone)
│   ├── inference.py               ← El que invocamos
│   ├── web-ui.py
│   ├── requirements.txt
│   └── ...
│
├── backend\
│   ├── main.py                    # FastAPI: servidor + endpoints
│   ├── audio_analyzer.py          # BPM, energía, duración (librosa)
│   ├── param_builder.py           # Traduce UI → argumentos de IA
│   ├── mapper_profiles.py         # DB estática de mapper IDs
│   ├── generator.py               # Invoca Mapperatorinator como subproceso
│   ├── osz_packager.py            # Empaqueta .osz
│   └── models\
│       ├── __init__.py
│       └── job.py                 # Estado de un job de generación
│
├── frontend\
│   ├── index.html                 # UI principal
│   ├── style.css                  # Dark theme estilo osu!
│   └── app.js                     # Lógica: upload, progreso SSE, descarga
│
├── temp\                          # Archivos temporales durante generación
├── output\                        # .osz generados, listos para descargar
│
├── requirements_app.txt           # Dependencias SOLO de nuestro app
├── setup.bat                      # Instalación completa (FFmpeg + deps)
└── run.bat                        # Inicia el servidor
```

---

## 9. Dependencias

### 9.1 Sistema (instalación manual/automática)

- **FFmpeg** — Necesario para que Mapperatorinator procese el audio  
  → Instalación: `winget install ffmpeg` (lo haremos en setup.bat)
- **Git** — Para clonar Mapperatorinator  
  → Verificar: `git --version`
- **CUDA Toolkit 13.0** — Para usar la GPU GTX 1660 Super  
  → Descargar de: https://developer.nvidia.com/cuda-zone

### 9.2 Python (nuestro app)

```
# requirements_app.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
librosa>=0.10.0       # Análisis de audio
numpy>=1.24.0
mutagen>=1.47.0       # Leer ID3 tags del MP3
python-multipart>=0.0.6
aiofiles>=23.0.0
```

### 9.3 Python (Mapperatorinator — se instala en su propio venv)

```
# Mapperatorinator/requirements.txt (ya existe en el repo)
accelerate==1.12.0
pydub==0.25.1
nnAudio==0.3.4
transformers==4.57.3
hydra-core==1.3.2
lightning==2.6.0
# + torch 2.10 con CUDA 13.0
# + audioop-lts (para Python 3.13+)
```

> **Nota:** Mapperatorinator tendrá su **propio entorno virtual** dentro de su carpeta. Nuestro backend lo invocará como un **subproceso**, pasando los argumentos correctos. Así evitamos conflictos de dependencias.

---

## 10. UI — Diseño de Pantallas

### Pantalla Principal

```
╔══════════════════════════════════════════════════════════════╗
║  🎵  osu! AI Beatmap Creator                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │                                                      │   ║
║  │         📂  Arrastra tu .mp3 aquí                    │   ║
║  │              o haz clic para buscar                  │   ║
║  │                                                      │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
║  ✅  cancion.mp3 cargada  |  BPM: 184.2  |  Dur: 3:42       ║
║                                                              ║
║  ─────────────── Estilo de Mapa ──────────────────────────  ║
║  [ Stream ] [ Jump ] [ Technical ] [ Alt ] [ Slider ]        ║
║                                                              ║
║  ─────────────── Estilo de Mapper ────────────────────────  ║
║  Mapper:  [ Sotarks ▼ ]   (aim-heavy, jumps limpios)         ║
║                                                              ║
║  ─────────────── Dificultad ──────────────────────────────  ║
║  ⭐  1 ━━━━━━━━━━━●━━━━━━━━━━━ 10   →   7.0 ★               ║
║                                                              ║
║  AR: 9.5  |  CS: 4.2  |  OD: 9.0  |  HP: 5.0               ║
║  (auto-calculado, puedes ajustar manualmente)               ║
║                                                              ║
║              ┌──────────────────────────┐                   ║
║              │   🎮  GENERAR BEATMAP   │                   ║
║              └──────────────────────────┘                   ║
╚══════════════════════════════════════════════════════════════╝
```

### Pantalla de Progreso

```
╔══════════════════════════════════════════════════════════════╗
║  ⚙️  Generando beatmap...                                    ║
║                                                              ║
║  ████████████████░░░░░░░░░░░░░░░░  48%                       ║
║                                                              ║
║  ✅  Audio analizado — BPM: 184.2, Duración: 3:42            ║
║  ✅  Parámetros configurados — 7.0★, estilo Sotarks/Jump     ║
║  🔄  Generando hit objects con osuT5 + osu-diffusion...      ║
║  ⏳  Post-procesamiento pendiente                             ║
║  ⏳  Empaquetando .osz pendiente                              ║
║                                                              ║
║  Tiempo estimado restante: ~45 segundos                      ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 11. El Comando Real que Genera el Mapa

Cuando el usuario hace clic en "Generar", nuestro backend construye y ejecuta algo así:

```bash
# Dentro del venv de Mapperatorinator:
python inference.py \
  audio_path="E:/ownProjects/creatorOfBeatmapsOsu/temp/abc123/audio.mp3" \
  output_path="E:/ownProjects/creatorOfBeatmapsOsu/output/abc123/" \
  gamemode=0 \
  difficulty=7.0 \
  mapper_id=1848318 \
  year=2024 \
  hitsounded=false \
  circle_size=4.2 \
  slider_multiplier=1.82 \
  descriptors="['skillset/jumps','style/clean']" \
  in_context=[TIMING]
```

El resultado es un archivo `.osu` en la carpeta de output. Nuestro backend luego lo empaqueta junto con el `.mp3` en un `.osz`.

---

## 12. Fases de Desarrollo

### Fase 0 — Setup del Entorno (Día 1, ~1.5h)
- [ ] Instalar FFmpeg: `winget install ffmpeg`
- [ ] Instalar Git (si no está): `winget install Git.Git`
- [ ] Clonar Mapperatorinator en `E:\ownProjects\creatorOfBeatmapsOsu\Mapperatorinator\`
- [ ] Crear venv de Mapperatorinator con Python 3.14
- [ ] Instalar PyTorch 2.10 con CUDA 13.0 en ese venv
- [ ] Instalar `requirements.txt` de Mapperatorinator
- [ ] **Prueba de humo**: ejecutar `inference.py` con una canción de prueba — verificar que genera un `.osu`

### Fase 1 — Análisis de Audio (Día 1, ~1h)
- [ ] `backend/audio_analyzer.py`: BPM, duración, energía, ID3 tags
- [ ] Test con canciones de `D:\!OSU\Songs`

### Fase 2 — Perfiles de Mapper y Parámetros (Día 1, ~1h)
- [ ] `backend/mapper_profiles.py`: diccionario de mappers con sus IDs y descripción
- [ ] `backend/param_builder.py`: lógica de traducción UI → args de `inference.py`

### Fase 3 — Generador (Día 2, ~2h)
- [ ] `backend/generator.py`: invoca Mapperatorinator como subproceso
- [ ] Captura stdout en tiempo real para mostrar progreso
- [ ] Manejo de errores (timeout, OOM, etc.)

### Fase 4 — Empaquetado y API (Día 2, ~2h)
- [ ] `backend/osz_packager.py`: crea el `.osz` (ZIP renombrado)
- [ ] `backend/main.py`: FastAPI con endpoints REST + SSE para progreso
- [ ] Gestión de jobs asincrónicos

### Fase 5 — Frontend (Día 3, ~3h)
- [ ] `frontend/index.html + style.css`: dark theme estilo osu! (rosa/#FF66AB sobre #1a1a2e)
- [ ] `frontend/app.js`: drag & drop, selección de estilo, escuchar SSE de progreso, descarga

### Fase 6 — Testing y Pulido (Día 3-4, ~2h)
- [ ] Test end-to-end con 3-5 canciones distintas
- [ ] Verificar que los `.osz` se abren en osu! y son jugables
- [ ] `setup.bat`: script de instalación automática
- [ ] `run.bat`: script de arranque del servidor

---

## 13. Riesgos y Mitigación

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| Python 3.14 incompatible con alguna dep de Mapperatorinator | Media | Crear venv Python 3.10 solo para Mapperatorinator si es necesario |
| 6 GB VRAM insuficiente para el modelo | Baja | El modelo cabe; si falla, usar fallback CPU (más lento) |
| FFmpeg no detectado por Mapperatorinator | Baja | Verificar PATH en setup.bat |
| El `.osu` generado tiene errores de formato | Baja | Validar con parser propio antes de empaquetar |
| Tiempo de generación muy largo | Media | Mostrar progreso en tiempo real + tiempo estimado |

---

## 14. Preguntas Finales Antes de Empezar

Solo necesito saber 2 cosas más antes de arrancar:

1. **¿Tienes CUDA Toolkit instalado?** Puedes verificar con: `nvcc --version` en la terminal.
   - Si no lo tienes, hay que descargarlo de NVIDIA (son ~3 GB) — lo incluimos en el setup.

2. **¿Qué nombre quieres para el proyecto en la UI?**
   - Sugerencia: "**osu! AI Mapper**" o "**BeatForge**" o el que prefieras.

---

## 15. Recursos

- [Mapperatorinator (GitHub)](https://github.com/OliBomby/Mapperatorinator)
- [Mapperatorinator en Colab](https://colab.research.google.com/github/OliBomby/Mapperatorinator/blob/main/colab/mapperatorinator_inference.ipynb) — Para probar antes de instalar localmente
- [osu! File Format v14](https://osu.ppy.sh/wiki/en/Client/File_formats/osu_%28file_format%29)
- [librosa docs](https://librosa.org/)
- [FastAPI docs](https://fastapi.tiangolo.com/)
- [PyTorch Get Started](https://pytorch.org/get-started/locally/)

---

*Plan actualizado el 2026-09-26 con respuestas del usuario.*
