@echo off
cd /d "%~dp0"

echo Uruchamianie aplikacji Torty...
".venv\Scripts\python.exe" -m streamlit run "src\app.py"

echo.
echo Aplikacja zostala zatrzymana.
pause