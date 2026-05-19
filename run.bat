@echo off
cd /d "%~dp0"
weather_env\Scripts\python.exe main.py %*
