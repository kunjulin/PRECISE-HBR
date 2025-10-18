# ============================================================================
# PRECISE-HBR Load Testing Script (PowerShell Version)
# Tests with 1, 10, and 30 concurrent users
# ============================================================================

Write-Host "========================================"
Write-Host "PRECISE-HBR Performance Load Tests"
Write-Host "========================================"
Write-Host ""

# Check if environment variables are set
if (-not $env:LOCUST_SESSION_COOKIE) {
    Write-Host "ERROR: LOCUST_SESSION_COOKIE environment variable is not set!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please follow these steps:"
    Write-Host "1. Login to the application in your browser"
    Write-Host "2. Open Developer Tools (F12)"
    Write-Host "3. Go to Application/Storage > Cookies"
    Write-Host "4. Copy the 'session' cookie value"
    Write-Host "5. Set it as environment variable:"
    Write-Host "   `$env:LOCUST_SESSION_COOKIE='your_session_cookie_value'" -ForegroundColor Yellow
    Write-Host "6. Set the patient ID:"
    Write-Host "   `$env:LOCUST_TEST_PATIENT_ID='your_patient_id'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not $env:LOCUST_TEST_PATIENT_ID) {
    Write-Host "ERROR: LOCUST_TEST_PATIENT_ID environment variable is not set!" -ForegroundColor Red
    Write-Host "Please set it with: `$env:LOCUST_TEST_PATIENT_ID='your_patient_id'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Set the target host (modify if needed)
$HOST_URL = if ($env:LOCUST_TARGET_HOST) { $env:LOCUST_TARGET_HOST } else { "http://localhost:8080" }

Write-Host "Target Host: $HOST_URL" -ForegroundColor Green
Write-Host "Patient ID: $env:LOCUST_TEST_PATIENT_ID" -ForegroundColor Green
Write-Host "Session Cookie: $($env:LOCUST_SESSION_COOKIE.Substring(0, [Math]::Min(20, $env:LOCUST_SESSION_COOKIE.Length)))..." -ForegroundColor Green
Write-Host ""

# Create results directory
if (-not (Test-Path "load_test_results")) {
    New-Item -ItemType Directory -Path "load_test_results" | Out-Null
}

# Get timestamp for this test run
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "========================================"
Write-Host "Test 1: Single User (1 user)"
Write-Host "========================================"
Write-Host "Running 1 minute test with 1 user..." -ForegroundColor Cyan
Write-Host ""

python -m locust -f locustfile.py --headless --users 1 --spawn-rate 1 --run-time 60s --host $HOST_URL --html "load_test_results/test_1user_$timestamp.html" --csv "load_test_results/test_1user_$timestamp"

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================"
Write-Host "Test 2: Small Team (10 users)"
Write-Host "========================================"
Write-Host "Running 2 minute test with 10 users..." -ForegroundColor Cyan
Write-Host ""

python -m locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 120s --host $HOST_URL --html "load_test_results/test_10users_$timestamp.html" --csv "load_test_results/test_10users_$timestamp"

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================"
Write-Host "Test 3: Moderate Load (30 users)"
Write-Host "========================================"
Write-Host "Running 3 minute test with 30 users..." -ForegroundColor Cyan
Write-Host ""

python -m locust -f locustfile.py --headless --users 30 --spawn-rate 5 --run-time 180s --host $HOST_URL --html "load_test_results/test_30users_$timestamp.html" --csv "load_test_results/test_30users_$timestamp"

Write-Host ""
Write-Host "========================================"
Write-Host "All tests completed!"
Write-Host "========================================"
Write-Host ""
Write-Host "Results saved in: load_test_results\" -ForegroundColor Green
Write-Host ""
Write-Host "Generating comparison report..."
python analyze_load_tests.py load_test_results

Write-Host ""
Write-Host "Done! Check the load_test_results folder for detailed reports." -ForegroundColor Green
Read-Host "Press Enter to exit"

