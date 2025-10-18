#!/bin/bash
# ============================================================================
# PRECISE-HBR Load Testing Script
# Tests with 1, 10, and 30 concurrent users
# ============================================================================

echo "========================================"
echo "PRECISE-HBR Performance Load Tests"
echo "========================================"
echo ""

# Check if environment variables are set
if [ -z "$LOCUST_SESSION_COOKIE" ]; then
    echo "ERROR: LOCUST_SESSION_COOKIE environment variable is not set!"
    echo ""
    echo "Please follow these steps:"
    echo "1. Login to the application in your browser"
    echo "2. Open Developer Tools (F12)"
    echo "3. Go to Application/Storage > Cookies"
    echo "4. Copy the 'session' cookie value"
    echo "5. Set it as environment variable:"
    echo "   export LOCUST_SESSION_COOKIE=your_session_cookie_value"
    echo "6. Set the patient ID:"
    echo "   export LOCUST_TEST_PATIENT_ID=your_patient_id"
    echo ""
    exit 1
fi

if [ -z "$LOCUST_TEST_PATIENT_ID" ]; then
    echo "ERROR: LOCUST_TEST_PATIENT_ID environment variable is not set!"
    echo "Please set it with: export LOCUST_TEST_PATIENT_ID=your_patient_id"
    exit 1
fi

# Set the target host (modify if needed)
HOST=${LOCUST_TARGET_HOST:-http://localhost:8080}

echo "Target Host: $HOST"
echo "Patient ID: $LOCUST_TEST_PATIENT_ID"
echo ""

# Create results directory
mkdir -p load_test_results

# Get timestamp for this test run
timestamp=$(date +%Y%m%d_%H%M%S)

echo "========================================"
echo "Test 1: Single User (1 user)"
echo "========================================"
echo "Running 1 minute test with 1 user..."
echo ""

locust -f locustfile.py --headless --users 1 --spawn-rate 1 --run-time 60s --host "$HOST" --html "load_test_results/test_1user_${timestamp}.html" --csv "load_test_results/test_1user_${timestamp}"

sleep 5

echo ""
echo "========================================"
echo "Test 2: Small Team (10 users)"
echo "========================================"
echo "Running 2 minute test with 10 users..."
echo ""

locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 120s --host "$HOST" --html "load_test_results/test_10users_${timestamp}.html" --csv "load_test_results/test_10users_${timestamp}"

sleep 5

echo ""
echo "========================================"
echo "Test 3: Moderate Load (30 users)"
echo "========================================"
echo "Running 3 minute test with 30 users..."
echo ""

locust -f locustfile.py --headless --users 30 --spawn-rate 5 --run-time 180s --host "$HOST" --html "load_test_results/test_30users_${timestamp}.html" --csv "load_test_results/test_30users_${timestamp}"

echo ""
echo "========================================"
echo "All tests completed!"
echo "========================================"
echo ""
echo "Results saved in: load_test_results/"
echo ""
echo "Generating comparison report..."
python analyze_load_tests.py load_test_results

echo ""
echo "Done! Check the load_test_results folder for detailed reports."

