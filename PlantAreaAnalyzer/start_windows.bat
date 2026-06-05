@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtuelle Umgebung nicht gefunden.
    echo Bitte zuerst in diesem Ordner ausfuehren:
    echo     py -3.13 -m venv .venv
    echo     .venv\Scripts\activate.bat
    echo     python -m pip install -r requirements.txt
    pause
    exit /b 1
)

set "QT_PLUGIN_PATH="
set "QT_QPA_PLATFORM_PLUGIN_PATH="

".venv\Scripts\python.exe" main.py
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Die App wurde mit Fehlercode %EXIT_CODE% beendet.
    pause
)

exit /b %EXIT_CODE%
