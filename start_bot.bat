@echo off
echo ============================================================
echo Kaori POS Bot - Starting...
echo ============================================================
echo.
echo Checking for existing Python processes...
tasklist | findstr python.exe >nul 2>&1
if %errorlevel%==0 (
    echo WARNING: Python processes are already running!
    echo Please close them before starting the bot.
    echo.
    tasklist | findstr python.exe
    echo.
    echo Press any key to force kill and continue, or Ctrl+C to exit...
    pause >nul
    taskkill /F /IM python.exe >nul 2>&1
    timeout /t 2 >nul
)

echo.
echo Starting bot...
echo.
python run.py
