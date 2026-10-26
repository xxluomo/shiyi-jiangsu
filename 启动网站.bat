@echo off
setlocal
title SHIYI JIANGSU - Local Museum
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" start_local.py %*
goto end
:missing
echo Python environment is missing. Read README.md for setup instructions.
:end
echo.
pause
endlocal
