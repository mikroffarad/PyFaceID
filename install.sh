#!/bin/bash

sudo apt update && sudo apt upgrade -y

sudo apt install -y python3 python3-dev python3-venv python3-tk cmake build-essential

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

cd "$SCRIPT_DIR"

python3 -m venv venv

source $SCRIPT_DIR/venv/bin/activate

echo "$SCRIPT DIR"

pip install opencv-python face_recognition 

pip install wheel setuptools pip --upgrade 
pip install git+https://github.com/ageitgey/face_recognition_models --verbose
