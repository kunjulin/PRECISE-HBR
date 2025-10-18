@echo off
REM Performance Testing Script for Windows
REM Tests application with 1, 10, and 100 concurrent users

echo ========================================
echo SMART FHIR App Performance Testing
echo ========================================
echo.

REM Check if required environment variables are set
if "%LOCUST_SESSION_COOKIE%"=="" (
    echo ERROR: LOCUST_SESSION_COOKIE environment variable is not set.
    echo Please set it using: set LOCUST_SESSION_COOKIE=your_session_cookie_value
    echo.
    pause
    exit /b 1
)

if "%LOCUST_TEST_PATIENT_ID%"=="" (
    echo ERROR: LOCUST_TEST_PATIENT_ID environment variable is not set.
    echo Please set it using: set LOCUST_TEST_PATIENT_ID=your_patient_id
    echo.
    pause
    exit /b 1
)

REM Set default host if not provided
if "%LOCUST_HOST%"=="" (
    set LOCUST_HOST=http://localhost:8080
    echo Using default host: %LOCUST_HOST%
) else (
    echo Using host: %LOCUST_HOST%
)

echo.
echo Session Cookie: %LOCUST_SESSION_COOKIE%
echo Patient ID: %LOCUST_TEST_PATIENT_ID%
echo Host: %LOCUST_HOST%
echo.

REM Create results directory
if not exist "performance_results" mkdir performance_results

echo Starting performance tests...
echo.

REM Test 1: Single User Test (Baseline)
echo ========================================
echo Running Test 1: 1 User (Baseline)
echo ========================================
echo Test duration: 60 seconds
echo Spawn rate: 1 user/second
echo.
locust -f locustfile.py --headless --users 1 --spawn-rate 1 --run-time 60s --host %LOCUST_HOST% --html performance_results/test_1_user.html --csv performance_results/test_1_user
if errorlevel 1 (
    echo Test 1 failed!
    pause
    exit /b 1
)
echo Test 1 completed successfully.
echo.

REM Wait between tests
timeout /t 10 /nobreak > nul

REM Test 2: 10 Users Test
echo ========================================
echo Running Test 2: 10 Users
echo ========================================
echo Test duration: 120 seconds
echo Spawn rate: 2 users/second
echo.
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 120s --host %LOCUST_HOST% --html performance_results/test_10_users.html --csv performance_results/test_10_users
if errorlevel 1 (
    echo Test 2 failed!
    pause
    exit /b 1
)
echo Test 2 completed successfully.
echo.

REM Wait between tests
timeout /t 15 /nobreak > nul

REM Test 3: 100 Users Test (Stress Test)
echo ========================================
echo Running Test 3: 100 Users (Stress Test)
echo ========================================
echo Test duration: 180 seconds
echo Spawn rate: 5 users/second
echo.
locust -f locustfile.py --headless --users 100 --spawn-rate 5 --run-time 180s --host %LOCUST_HOST% --html performance_results/test_100_users.html --csv performance_results/test_100_users
if errorlevel 1 (
    echo Test 3 failed!
    pause
    exit /b 1
)
echo Test 3 completed successfully.
echo.

echo ========================================
echo All Performance Tests Completed!
echo ========================================
echo.
echo Results saved in 'performance_results' directory:
echo - test_1_user.html (HTML report for 1 user)
echo - test_10_users.html (HTML report for 10 users) 
echo - test_100_users.html (HTML report for 100 users)
echo - CSV files with detailed statistics
echo - JSON files with custom performance metrics
echo.

REM Generate comparison report
echo Generating comparison report...
python generate_performance_comparison.py
if errorlevel 1 (
    echo Warning: Could not generate comparison report.
    echo You can still view individual test results.
)

echo.
echo Open the HTML files in your browser to view detailed results.
echo.
pause
