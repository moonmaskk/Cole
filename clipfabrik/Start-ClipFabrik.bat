@echo off
rem ClipFabrik ohne .exe starten (braucht Python 3.11+ von python.org, Haken bei "Add to PATH").
cd /d "%~dp0"
if exist .venv goto run
echo Richte ClipFabrik beim ersten Start ein ...
python -m venv .venv || goto nopython
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
set /p SUBS="Untertitel einrichten (faster-whisper, ca. 1 GB)? [j/n] "
if /i "%SUBS%"=="j" .venv\Scripts\python -m pip install faster-whisper
:run
.venv\Scripts\python -m clipfabrik
pause
exit /b 0
:nopython
echo Python fehlt: https://www.python.org/downloads/
pause
exit /b 1
