@echo off
title Ai Mapper - Instalacion y Configuracion
cd /d "%~dp0"

echo ========================================================
echo   Ai Mapper - Instalacion y Configuracion del Sistema
echo ========================================================
echo.

:: 1. Verificar Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git no esta instalado. Instalandolo con winget...
    winget install --id Git.Git -e --source winget
)

:: 2. Verificar FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Verificando FFmpeg...
    winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
)

:: 3. Crear entorno virtual del backend
echo [*] Creando entorno virtual del backend (.venv)...
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

echo [*] Instalando dependencias del backend...
.\.venv\Scripts\pip.exe install -r requirements_app.txt

:: 4. Clonar Mapperatorinator si no existe
if not exist "Mapperatorinator\inference.py" (
    echo [*] Clonando motor de IA Mapperatorinator...
    git clone https://github.com/OliBomby/Mapperatorinator.git
)

:: 5. Crear entorno virtual de Mapperatorinator
echo [*] Configurando entorno virtual del motor de IA...
if not exist "Mapperatorinator\.venv\Scripts\python.exe" (
    cd Mapperatorinator
    python -m venv .venv
    
    echo [*] Instalando PyTorch con aceleracion CUDA...
    .\.venv\Scripts\pip.exe install torch torchaudio --index-url https://download.pytorch.org/whl/cu130
    
    echo [*] Instalando dependencias del motor...
    set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
    .\.venv\Scripts\pip.exe install rosu-pp-py
    .\.venv\Scripts\pip.exe install -r requirements.txt
    .\.venv\Scripts\pip.exe install "hydra-core==1.3.7"
    cd ..
)

echo.
echo ========================================================
echo   Instalacion completada con exito!
echo   Para iniciar la aplicacion, ejecuta: run.bat
echo ========================================================
pause
