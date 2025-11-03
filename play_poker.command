#!/bin/bash
# Python Virtual Environment Setup and Launcher
# Safe script for initializing Python development environment

set -e  # Exit on error

cd "$(dirname "$0")"
echo "Current directory: $(pwd)"

VENV_DIR=".venv"
REQUIRED_PYTHON="3.12"

echo "Checking for virtual environment..."

# Check if venv exists and is valid
if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python" ]; then
    echo "Virtual environment found."
else
    echo "Setting up virtual environment with Python $REQUIRED_PYTHON..."
    
    # Only remove if it exists but is broken
    [ -d "$VENV_DIR" ] && rm -rf "$VENV_DIR"
    
    # Find appropriate Python version
    PYTHON_CMD=""
    for ver in python3.12 python3.11 python3.10 python3; do
        if command -v $ver &> /dev/null; then
            PYTHON_CMD=$ver
            break
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        echo "ERROR: Python 3.10+ required for this application"
        echo "Install from: https://www.python.org/downloads/"
        read -p "Press Enter to exit..."
        exit 1
    fi
    
    echo "Using: $PYTHON_CMD"
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    echo "Installing dependencies..."
    "$VENV_DIR/bin/pip" install --quiet --upgrade pip
    "$VENV_DIR/bin/pip" install --quiet -r requirements.txt
fi

echo "Starting application..."
"$VENV_DIR/bin/python" main.py

# Pause on error (Windows-style behavior)
if [ $? -ne 0 ]; then
    echo ""
    read -p "Application exited with error. Press Enter to close..."
fi