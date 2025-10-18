@echo off
echo ================================================
echo   Restarting SMART FHIR App (Local Development)
echo ================================================
echo.

REM Kill any existing Python processes running APP.py
echo Stopping existing Flask application...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *APP.py*" 2>nul
timeout /t 2 /nobreak >nul

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python
)

REM Set environment variables for local development
echo Setting environment variables...
set FLASK_ENV=development
set FLASK_DEBUG=true

REM Start Flask application
echo.
echo Starting Flask application on http://localhost:8080...
echo.
echo ================================================
echo   Application is starting...
echo   URL: http://localhost:8080
echo   Press Ctrl+C to stop
echo ================================================
echo.

python APP.py

pause

