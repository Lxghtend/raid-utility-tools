@echo off
REM update.bat — lives in the repo ROOT (same folder as .git)
REM Waits for the main app to exit, asks for confirmation, pulls latest, relaunches
REM Usage: update.bat <PID> <folder-to-relaunch> <script-to-run>

setlocal
set PID=%1
set RELAUNCH_DIR=%2
set RELAUNCH_SCRIPT=%3

echo Waiting for app (PID %PID%) to close...

:WAIT
tasklist /FI "PID eq %PID%" 2>NUL | find "%PID%" >NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto WAIT
)

echo.
echo App closed.
choice /M "Pull latest changes from git now"
if errorlevel 2 (
    echo Update cancelled. Relaunching without updating...
    goto RELAUNCH
)

REM %~dp0 = folder this .bat lives in = repo root
cd /d "%~dp0"

git pull

if errorlevel 1 (
    echo git pull failed - check your git install / network / local changes.
    pause
    exit /b 1
)

echo Update complete.

:RELAUNCH
echo Relaunching...
cd /d "%RELAUNCH_DIR%"
start "" python "%RELAUNCH_SCRIPT%"

exit
