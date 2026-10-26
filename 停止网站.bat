@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" stop_local.py
echo.
pause
endlocal
