@echo off
echo ============================================================
echo Killing ALL Python processes...
echo ============================================================
echo.
taskkill /F /IM python.exe /T 2>nul
if %errorlevel%==0 (
    echo SUCCESS: All Python processes have been terminated.
) else (
    echo No Python processes were found running.
)
echo.
echo Waiting 3 seconds...
timeout /t 3 >nul
echo.
echo You can now run start_bot.bat to start a fresh instance.
echo.
pause
