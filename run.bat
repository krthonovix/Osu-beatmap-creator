@echo off
title Ai Mapper - osu! Beatmap Creator
cd /d "%~dp0"

echo ===================================================
echo   Ai Mapper - osu! Beatmap Creator con IA
echo   GPU: NVIDIA GeForce GTX 1660 SUPER (CUDA)
echo ===================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en .venv.
    pause
    exit /b
)

echo Iniciando servidor FastAPI en http://localhost:8000 ...
start http://localhost:8000

.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
