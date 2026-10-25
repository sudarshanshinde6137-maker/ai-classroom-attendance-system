@echo off
title AI Classroom Attendance Web Studio
echo.
echo  =============================================
echo   AI Classroom Attendance Web Studio (FastAPI)
echo  =============================================
echo.
echo  [INFO] Starting Web Server on port 8000...
echo  [INFO] Accessible on Localhost and Local Network (Wi-Fi).
echo  [INFO] Press Ctrl+C to stop server.
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" web\server.py
) else (
    python web\server.py
)

if errorlevel 1 (
    echo.
    echo  [ERROR] Web Server exited with an error.
    pause
)