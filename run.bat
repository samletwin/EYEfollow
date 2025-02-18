@echo off
cd /d "\path\here"

echo Pulling latest changes from Git...
git pull origin main

if %errorlevel% neq 0 (
    echo Git pull failed. Exiting.
    exit /b %errorlevel%
)

echo Running Python application...
py application.py
