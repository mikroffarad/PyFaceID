#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT" || { echo "Error: Failed to change directory to $PROJECT_ROOT"; exit 1; }

echo "Running installation in: $(pwd)"

if [ ! -f "requirements.txt" ]; then
    echo "Error: This script must be run from the PyFaceID project root."
    exit 1
fi

if command -v apt &> /dev/null; then
    echo "Detected APT-based system (Debian, Ubuntu, etc.)"
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3 python3-dev python3-venv cmake build-essential qt6-base-dev libxcb-cursor-dev
elif command -v pacman &> /dev/null; then
    echo "Detected Pacman-based system (Arch Linux, Manjaro, etc.)"
    sudo pacman -Syyu --noconfirm
    sudo pacman -S --noconfirm python3 cmake qt6-base
else
    echo "Error: Unsupported package manager. Please install dependencies manually."
    exit 1
fi

python3 -m venv venv || { echo "Error: Failed to create virtual environment"; exit 1; }
source venv/bin/activate || { echo "Error: Failed to activate virtual environment"; exit 1; }

# Встановлення пакетів
pip install -r requirements.txt || { echo "Error: Failed to install dependencies"; exit 1; }

echo "Installation complete. Activate virtual environment and run main.py"
