#!/bin/bash

pyinstaller --onefile --windowed install.sh 
  --add-data "venv/lib/python3.12/site-packages/face_recognition_models/models/*:face_recognition_models/models" \
  --name PyFaceID main.py
