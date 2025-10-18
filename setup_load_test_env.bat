@echo off
REM ============================================================================
REM PRECISE-HBR Load Test Environment Setup
REM This script helps you set up environment variables for load testing
REM ============================================================================

echo ========================================
echo PRECISE-HBR Load Test Setup
echo ========================================
echo.

echo This script will help you set environment variables for load testing.
echo.
echo STEP 1: Get your session cookie
echo --------------------------------
echo 1. Open your browser and login to the application
echo 2. Press F12 to open Developer Tools
echo 3. Go to Application (Chrome) or Storage (Firefox) tab
echo 4. Click on Cookies in the left sidebar
echo 5. Select your site (e.g., http://localhost:8080)
echo 6. Find the cookie named 'session'
echo 7. Copy its Value
echo.

set /p SESSION_COOKIE="Paste your session cookie value here: "

if "%SESSION_COOKIE%"=="" (
    echo.
    echo ERROR: Session cookie cannot be empty!
    pause
    exit /b 1
)

echo.
echo STEP 2: Enter patient ID
echo -------------------------
echo You can find the patient ID in the application's main page.
echo.

set /p PATIENT_ID="Enter patient ID (e.g., 12724066): "

if "%PATIENT_ID%"=="" (
    echo.
    echo ERROR: Patient ID cannot be empty!
    pause
    exit /b 1
)

echo.
echo STEP 3: Enter target host (optional)
echo --------------------------------------
echo.

set /p TARGET_HOST="Enter target host [http://localhost:8080]: "

if "%TARGET_HOST%"=="" (
    set TARGET_HOST=http://localhost:8080
)

REM Set the environment variables
set LOCUST_SESSION_COOKIE=%SESSION_COOKIE%
set LOCUST_TEST_PATIENT_ID=%PATIENT_ID%
set LOCUST_TARGET_HOST=%TARGET_HOST%

echo.
echo ========================================
echo Environment variables set successfully!
echo ========================================
echo.
echo LOCUST_SESSION_COOKIE: %LOCUST_SESSION_COOKIE:~0,20%...
echo LOCUST_TEST_PATIENT_ID: %LOCUST_TEST_PATIENT_ID%
echo LOCUST_TARGET_HOST: %LOCUST_TARGET_HOST%
echo.
echo NOTE: These variables are only valid in this command window.
echo       You can now run: run_load_tests.bat
echo.

pause

