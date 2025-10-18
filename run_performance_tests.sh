#!/bin/bash

# Performance Testing Script for Linux/Mac
# Tests application with 1, 10, and 100 concurrent users

echo "========================================"
echo "SMART FHIR App Performance Testing"
echo "========================================"
echo

# Check if required environment variables are set
if [ -z "$LOCUST_SESSION_COOKIE" ]; then
    echo "ERROR: LOCUST_SESSION_COOKIE environment variable is not set."
    echo "Please set it using: export LOCUST_SESSION_COOKIE=your_session_cookie_value"
    echo
    exit 1
fi

if [ -z "$LOCUST_TEST_PATIENT_ID" ]; then
    echo "ERROR: LOCUST_TEST_PATIENT_ID environment variable is not set."
    echo "Please set it using: export LOCUST_TEST_PATIENT_ID=your_patient_id"
    echo
    exit 1
fi

# Set default host if not provided
if [ -z "$LOCUST_HOST" ]; then
    export LOCUST_HOST="http://localhost:8080"
    echo "Using default host: $LOCUST_HOST"
else
    echo "Using host: $LOCUST_HOST"
fi

echo
echo "Session Cookie: $LOCUST_SESSION_COOKIE"
echo "Patient ID: $LOCUST_TEST_PATIENT_ID"
echo "Host: $LOCUST_HOST"
echo

# Create results directory
mkdir -p performance_results

echo "Starting performance tests..."
echo

# Function to check if command succeeded
check_result() {
    if [ $? -ne 0 ]; then
        echo "$1 failed!"
        exit 1
    fi
    echo "$1 completed successfully."
    echo
}

# Test 1: Single User Test (Baseline)
echo "========================================"
echo "Running Test 1: 1 User (Baseline)"
echo "========================================"
echo "Test duration: 60 seconds"
echo "Spawn rate: 1 user/second"
echo

locust -f locustfile.py --headless --users 1 --spawn-rate 1 --run-time 60s \
    --host "$LOCUST_HOST" \
    --html performance_results/test_1_user.html \
    --csv performance_results/test_1_user

check_result "Test 1"

# Wait between tests
echo "Waiting 10 seconds before next test..."
sleep 10

# Test 2: 10 Users Test
echo "========================================"
echo "Running Test 2: 10 Users"
echo "========================================"
echo "Test duration: 120 seconds"
echo "Spawn rate: 2 users/second"
echo

locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 120s \
    --host "$LOCUST_HOST" \
    --html performance_results/test_10_users.html \
    --csv performance_results/test_10_users

check_result "Test 2"

# Wait between tests
echo "Waiting 15 seconds before next test..."
sleep 15

# Test 3: 100 Users Test (Stress Test)
echo "========================================"
echo "Running Test 3: 100 Users (Stress Test)"
echo "========================================"
echo "Test duration: 180 seconds"
echo "Spawn rate: 5 users/second"
echo

locust -f locustfile.py --headless --users 100 --spawn-rate 5 --run-time 180s \
    --host "$LOCUST_HOST" \
    --html performance_results/test_100_users.html \
    --csv performance_results/test_100_users

check_result "Test 3"

echo "========================================"
echo "All Performance Tests Completed!"
echo "========================================"
echo
echo "Results saved in 'performance_results' directory:"
echo "- test_1_user.html (HTML report for 1 user)"
echo "- test_10_users.html (HTML report for 10 users)"
echo "- test_100_users.html (HTML report for 100 users)"
echo "- CSV files with detailed statistics"
echo "- JSON files with custom performance metrics"
echo

# Generate comparison report
echo "Generating comparison report..."
if python3 generate_performance_comparison.py; then
    echo "Comparison report generated successfully."
else
    echo "Warning: Could not generate comparison report."
    echo "You can still view individual test results."
fi

echo
echo "Open the HTML files in your browser to view detailed results."
echo

# Make the script executable
chmod +x "$0"
