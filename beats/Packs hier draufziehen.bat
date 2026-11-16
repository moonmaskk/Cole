@echo off
REM Sample-Packs (ZIPs oder Ordner) einfach auf diese Datei ziehen.
cd /d "%~dp0"
python tools\cole_beats.py sortieren %*
pause
