@echo off
REM ========================================
REM Python Application Launcher
REM Safe virtual environment setup script
REM ========================================

cd /d "%~dp0"
echo Current directory: %cd%
echo.

set VENV_DIR=.venv
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe

echo Checking for virtual environment...

REM Check if virtual environment exists
if exist "%PYTHON_EXE%" (
    echo Virtual environment found.
    goto :run_app
)

echo.
echo First-time setup: Creating virtual environment...
echo This will only happen once.
echo.

REM Find Python installation
set PYTHON_CMD=
for %%P in (python.exe python3.exe py.exe) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=%%P
        goto :create_venv
    )
)

REM Python not found
echo ERROR: Python not found in PATH
echo.
echo Please install Python 3.10 or higher from:
echo https://www.python.org/downloads/
echo.
echo Make sure to check "Add Python to PATH" during installation
echo.
pause
exit /b 1

:create_venv
echo Creating virtual environment with %PYTHON_CMD%...
%PYTHON_CMD% -m venv "%VENV_DIR%"

if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Installing dependencies (this may take a minute)...
"%PYTHON_EXE%" -m pip install --quiet --upgrade pip
"%PYTHON_EXE%" -m pip install --quiet -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install packages
    echo Please check your internet connection
    pause
    exit /b 1
)

echo Setup complete!
echo.

:run_app
echo Starting application...
echo.
"%PYTHON_EXE%" main.py

if errorlevel 1 (
    echo.
    echo Application closed with errors
)

echo.
pause