#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT" || { echo "Error: Failed to change directory to $PROJECT_ROOT"; exit 1; }

echo "Building in: $(pwd)"

if [ ! -f "main.py" ]; then
    echo "Error: main.py not found. Run this script from the project root."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Run install.sh first."
    exit 1
fi

source venv/bin/activate || { echo "Error: Failed to activate virtual environment"; exit 1; }

if ! python -c "import pyinstaller" &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller || { echo "Error: Failed to install PyInstaller"; exit 1; }
else
    echo "PyInstaller is already installed."
fi

echo "Starting build..."
pyinstaller --onefile --windowed \
  --add-data "venv/lib/python3.*/site-packages/face_recognition_models/models/*:face_recognition_models/models" \
  --add-data "assets/icon.svg:assets/icon.svg" \
  --name PyFaceID main.py


echo "Build complete. Check the dist/ directory."
