@echo off
title AI Classroom Attendance System
echo.
echo  =============================================
echo   AI Classroom Attendance System
echo  =============================================
echo.

REM Try .venv first, then system Python
if exist ".venv\Scripts\python.exe" (
    echo  [INFO] Using virtual environment Python...
    ".venv\Scripts\python.exe" main.py
) else (
    echo  [INFO] Using system Python...
    python main.py
)

if errorlevel 1 (
    echo.
    echo  [ERROR] Application exited with an error.
    pause
)
