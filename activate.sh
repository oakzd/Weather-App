#!/usr/bin/env bash
# Activate venv and force this project's Python (fixes Git Bash using Windows Store python)
cd "$(dirname "$0")"
source weather_env/Scripts/activate
hash -r
unalias python 2>/dev/null
export PATH="$(pwd)/weather_env/Scripts:$PATH"
alias python="$(pwd)/weather_env/Scripts/python.exe"
echo "Python: $(./weather_env/Scripts/python.exe -c 'import sys; print(sys.executable)')"
