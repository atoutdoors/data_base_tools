@echo off
setlocal EnableExtensions

rem Run this file from any folder; all paths are resolved relative to this file.
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%read_incoming_log.py"
set "REQUIREMENTS=%SCRIPT_DIR%requirements.txt"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "INSTALL_MARKER=%VENV_DIR%\.requirements-installed-v3"

if not exist "%PYTHON_SCRIPT%" (
    echo Could not find read_incoming_log.py in "%SCRIPT_DIR%"
    pause
    exit /b 1
)

echo.
echo Starting read_incoming_log from "%SCRIPT_DIR%"

if not exist "%PYTHON_EXE%" (
    where py >nul 2>&1
    if not errorlevel 1 (
        echo Creating local Python environment...
        py -3 -m venv "%VENV_DIR%"
    ) else (
        where python >nul 2>&1
        if errorlevel 1 (
            echo Python 3 is required. Install Python from https://www.python.org/downloads/
            exit /b 1
        )
        echo Creating local Python environment...
        python -m venv "%VENV_DIR%"
    )
    if not exist "%PYTHON_EXE%" (
        echo Could not create the local Python environment.
        pause
        exit /b 1
    )
)

if not exist "%INSTALL_MARKER%" (
    echo Installing required Python packages...
    "%PYTHON_EXE%" -m pip install -r "%REQUIREMENTS%"
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
    >"%INSTALL_MARKER%" echo installed
)

"%PYTHON_EXE%" -c "import requests, dotenv, pandas, pypdf" >nul 2>&1
if errorlevel 1 (
    echo Installing missing Python packages...
    "%PYTHON_EXE%" -m pip install -r "%REQUIREMENTS%"
    if errorlevel 1 (
        echo Package installation failed.
        pause
        exit /b 1
    )
)

echo Launching parser...
"%PYTHON_EXE%" "%PYTHON_SCRIPT%" %*
set "EXIT_CODE=%errorlevel%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo Parser exited with code %EXIT_CODE%.
    pause
)
if "%~1"=="" pause
exit /b %EXIT_CODE%
