# 🎵 Ai Mapper — osu! Beatmap Creator con IA

**Ai Mapper** es una aplicación web local que analiza cualquier canción en formato `.mp3`, extrae su ritmo, BPM y energía con algoritmos DSP (`librosa`), y genera automáticamente un beatmap jugable de **osu!** utilizando modelos de difusión y transformers (`osuT5` + `osu-diffusion` / **Mapperatorinator**), emulando estilos de mappers famosos como **Sotarks**, **Reform**, **RLC**, **Nevo**, y más.

---

## 🚀 Inicio Rápido

Simplemente haz doble clic en el archivo:
```bat
run.bat
```
Esto iniciará el servidor local y abrirá tu navegador automáticamente en:
👉 **http://localhost:8000**

---

## 🎮 Cómo Usar la Aplicación

1. **Sube tu canción:**
   - Arrastra y suelta tu archivo `.mp3` en el recuadro o haz clic para seleccionarlo.
   - El sistema calculará el **BPM estimado**, la duración y extraerá los metadatos (título y artista).
2. **Selecciona la Dificultad (Star Rating):**
   - Ajusta el deslizador de estrellas (ejemplo: **7.0 ★**).
   - Los valores de **AR** (Approach Rate), **CS** (Circle Size), **OD** (Overall Difficulty) y **HP** se calibran automáticamente según los estándares competitivos de osu!.
3. **Elige el Estilo del Beatmap:**
   - **Jump Map:** Foco en saltos y aim rápido.
   - **Stream Map:** Notas consecutivas y alta densidad rítmica.
   - **Technical Map:** Sliders elaborados y ritmos complejos.
   - **Alternating (Alt):** Diseñado para alternar dedos.
   - **Slider-Heavy / Flow:** Sliders largos y transiciones suaves.
4. **Elige la Inspiración del Mapper:**
   - **Sotarks:** Jumps de 1-2 limpios y dinámicos.
   - **Reform:** Patrones rítmicos técnicos y creativos.
   - **fieryrage:** Cross-screen jumps agresivos.
   - **Nevo:** Flow natural y transiciones limpias.
   - **Monstrata:** Estructura geométrica y sliders legibles.
   - *Y muchos más (RLC, Lasse, Doormat, Sing, Hollow Wings, o Neutral).*
5. **Genera y Descarga:**
   - Haz clic en **⚡ Generar Beatmap con IA**.
   - Podrás ver el progreso en tiempo real mediante Server-Sent Events.
   - Al finalizar, haz clic en **📥 Descargar paquete .osz** y arrástralo a tu ventana de osu! para jugarlo de inmediato.

---

## 🖥️ Arquitectura del Sistema

```
creatorOfBeatmapsOsu/
├── backend/
│   ├── main.py             # Servidor FastAPI y endpoints REST/SSE
│   ├── audio_analyzer.py   # Detección de BPM, duración y metadatos con librosa y mutagen
│   ├── param_builder.py    # Mapeo de dificultad, estrellas y descriptores
│   ├── mapper_profiles.py  # Base de datos de mappers y estilos
│   ├── generator.py        # Orquestador del modelo de IA (subproceso seguro)
│   ├── osz_packager.py     # Creador y empaquetador del archivo .osz final
│   └── models/
│       └── job.py          # Modelos de estado de generación
├── frontend/
│   ├── index.html          # Interfaz web con tema oscuro osu!
│   ├── style.css           # Estilos modernos con acentos rosados osu!
│   └── app.js              # Lógica de upload, slider interactivo y SSE
├── Mapperatorinator/       # Motor de difusión y transformers de IA (osuT5)
├── run.bat                 # Lanzador de un solo clic
└── requirements_app.txt    # Dependencias de la aplicación
```

---

## ⚡ Aceleración por Hardware

- **GPU:** NVIDIA GeForce GTX 1660 SUPER
- **CUDA:** PyTorch 2.14+cu130 acelerado por hardware
- **FFmpeg:** Instalado en el sistema para decodificación de audio de alta fidelidad
