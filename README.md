# Ai Mapper — osu! AI Beatmap Generator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%20--%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.14%20(CUDA%2013)-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)

An intelligent, local web application that converts any `.mp3` audio track into a fully playable, rankable-quality **osu!** beatmap (`.osz`) using deep learning (Transformers & Diffusion models).

[Features](#-key-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Core Engine](#-core-engine)

</div>

---

## 🌟 Key Features

- **End-to-End Generation:** Upload a single audio file and obtain a fully packaged, ready-to-play `.osz` archive.
- **Audio DSP Analysis:** Automatically extracts tempo, BPM, and energy curves using `librosa` and ID3 metadata using `mutagen`.
- **Mapper Style Transfer:** Condition object placement and rhythmic density on well-known community mappers:
  - **Sotarks:** Sharp aim-heavy 1-2 jump patterns with structured flow.
  - **Reform:** Technical maps with complex rhythmic syncopation and intricate sliders.
  - **fieryrage:** Aggressive cross-screen jumps and high-energy dynamics.
  - **Nevo:** Organic flow with clean geometric transitions.
  - **Monstrata:** Rigid geometric structuring and readable slider design.
  - **RLC, Lasse, Doormat, Sing, Hollow Wings**, and an unconstrained **Neutral** mode.
- **Gameplay Skillsets:** Choose between specific mapping disciplines:
  - *Jump Maps*
  - *Stream Maps*
  - *Technical Maps*
  - *Alternating (Alt)*
  - *Slider-Heavy / Flow*
- **Automatic Difficulty Scaling:** Target any Star Rating between **1.0★ and 10.0★**. The engine calculates canonical competitive osu! parameters (**AR, CS, OD, HP, and Slider Velocity**) matching the selected difficulty tier.
- **Hardware Acceleration:** Native PyTorch GPU acceleration with CUDA support for fast tensor evaluation and diffusion sampling (CPU fallback available).
- **Modern Web Interface:** Clean osu!-inspired dark theme with real-time Server-Sent Events (SSE) progress tracking.

---

## 🖥️ System Requirements

### Hardware
- **GPU (Recommended):** NVIDIA GPU with CUDA support (4 GB VRAM minimum, 6 GB+ recommended for optimal speed). CPU mode is supported as a fallback.
- **RAM:** 8 GB minimum (16 GB recommended).
- **Disk Space:** ~8 to 10 GB free space for virtual environments, PyTorch wheels, and model cache.

### Software
- **OS:** Windows 10 / 11 (64-bit).
- **Python:** 3.10 to 3.14 (64-bit).
- **FFmpeg:** Required for audio decoding (installed automatically via `setup.bat`).
- **Git:** Required for dependency management.

---

## 📦 Installation

### Quick Setup (Automated)

1. Clone this repository:
   ```bash
   git clone https://github.com/krthonovix/Osu-beatmap-creator.git
   cd Osu-beatmap-creator
   ```

2. Run the automated setup script:
   ```bat
   setup.bat
   ```
   This script will:
   - Check and configure **FFmpeg** and **Git**.
   - Create the backend virtual environment (`.venv`) and install application dependencies.
   - Clone the core inference engine ([Mapperatorinator](https://github.com/OliBomby/Mapperatorinator)).
   - Set up the inference environment with PyTorch CUDA 13 and compile native modules (`rosu-pp-py`, `slider`).

---

## 🚀 Usage

1. Launch the server by running:
   ```bat
   run.bat
   ```
   The browser will automatically open at:
   ```
   http://localhost:8000
   ```

2. **Step 1 — Upload Audio:**
   Drag and drop an `.mp3` file into the input zone. The system will compute estimated BPM and track length.

3. **Step 2 — Configure Map Settings:**
   - Adjust the **Star Rating Slider** to set difficulty (e.g., `7.0★`).
   - Select the desired **Map Style** (Jump, Stream, Technical, etc.).
   - Choose a **Mapper Style** for aesthetic and structural inspiration.

4. **Step 3 — Generate & Download:**
   - Click **⚡ Generar Beatmap con IA**.
   - Monitor live diffusion and sequencing progress.
   - Click **📥 Descargar paquete .osz** upon completion.
   - Double-click the downloaded `.osz` or drag it directly into the osu! game window to import.

---

## 🏗️ Architecture

```
Osu-beatmap-creator/
├── backend/
│   ├── main.py             # FastAPI REST endpoints, static router, and SSE stream
│   ├── audio_analyzer.py   # Signal processing (BPM, duration, RMS energy) & ID3 parser
│   ├── param_builder.py    # Canonical stat calibration (AR/CS/OD/HP/SV) and Hydra overrides
│   ├── mapper_profiles.py  # Mappers database and style descriptor tokens
│   ├── generator.py        # Asynchronous orchestrator invoking inference pipeline
│   ├── osz_packager.py     # Beatmap sanitizer and .osz ZIP compressor
│   └── models/
│       └── job.py          # Pydantic state models for async generation jobs
├── frontend/
│   ├── index.html          # osu!-styled responsive dashboard
│   ├── style.css           # Modern dark UI theme with glowing accents
│   └── app.js              # Client state, audio upload handler, and SSE listener
├── Mapperatorinator/       # Transformer (osuT5) & Diffusion pipeline engine
├── requirements_app.txt    # Application dependencies
├── run.bat                 # One-click launcher
├── setup.bat               # Automated environment installer
└── .gitignore              # Repository exclude rules
```

---

## 📊 Pipeline Flow

```mermaid
flowchart LR
    A[MP3 File] --> B[Audio Analyzer\nlibrosa / DSP]
    B --> C[Parameter Builder\nStats & Style Tags]
    C --> D[Mapperatorinator\nosuT5 + Diffusion]
    D --> E[Raw .osu Generation]
    E --> F[OSZ Packager\nMetadata & Audio ZIP]
    F --> G[Playable .osz Package]
```

---

## ⚖️ Ethical Use & Guidelines

- **Fair Mapping Practice:** This software is intended as an assistive tool for inspiration, rhythm game research, and personal practice.
- **Community Standards:** Always disclose the use of automated/AI tools when sharing or submitting beatmaps to community platforms.

---

## 🔗 Core Engine

This project uses the [Mapperatorinator](https://github.com/OliBomby/Mapperatorinator) framework as its core AI generation engine for audio spectrogram processing, rhythmic sequencing, and diffusion-based hit object coordinate prediction.
