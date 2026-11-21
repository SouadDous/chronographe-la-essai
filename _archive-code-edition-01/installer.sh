#!/bin/sh
# Installation de l'environnement de production (macOS ou Linux). Ne publie rien.
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "ffmpeg est requis (macOS : brew install ffmpeg)"; exit 1; }
python3 -m venv .env
. .env/bin/activate
pip install -r exigences.txt
python -m playwright install chromium
echo "Prêt. Activez l'environnement avec : . .env/bin/activate"
echo "Puis vérifiez tout avec : python outils/verifier.py"
