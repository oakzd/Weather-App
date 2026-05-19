#!/usr/bin/env bash
# Run the app with the project venv (avoids wrong system/python on PATH)
cd "$(dirname "$0")"
exec ./weather_env/Scripts/python.exe main.py "$@"
