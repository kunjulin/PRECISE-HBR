#!/usr/bin/env python3
"""
Quick Performance Test Script
A simplified way to run performance tests with minimal setup.
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def print_banner():
    print("=" * 60)
    print("SMART FHIR App - Quick Performance Test")
    print("=" * 60)
    print()

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ['LOCUST_SESSION_COOKIE', 'LOCUST_TEST_PATIENT_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("Please set these variables before running the test:")
        print("Windows:")
        for var in missing_vars:
            print(f"   set {var}=your_value_here")
        print()
        print("Linux/Mac:")
        for var in missing_vars:
            print(f"   export {var}=\"your_value_here\"")
        print()
        return False
    
    print("✅ Environment variables are set")
    return True

def run_quick_test():
    """Run a quick performance test with predefined settings."""
    print("Starting quick performance comparison test...")
    print("This will test 1, 10, and 100 concurrent users")
    print()
    
    # Set default host if not provided
    host = os.environ.get('LOCUST_HOST', 'http://localhost:8080')
    print(f"Testing against: {host}")
    print()
    
    # Create results directory
    os.makedirs('performance_results', exist_ok=True)
    
    test_configs = [
        {'users': 1, 'duration': '30s', 'spawn_rate': 1, 'name': 'baseline'},
        {'users': 10, 'duration': '60s', 'spawn_rate': 2, 'name': 'moderate'},
        {'users': 100, 'duration': '90s', 'spawn_rate': 5, 'name': 'stress'}
    ]
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"🚀 Running Test {i}/3: {config['users']} users ({config['name']} load)")
        print(f"   Duration: {config['duration']}, Spawn rate: {config['spawn_rate']} users/sec")
        
        cmd = [
            'locust',
            '-f', 'locustfile.py',
            '--headless',
            '--users', str(config['users']),
            '--spawn-rate', str(config['spawn_rate']),
            '--run-time', config['duration'],
            '--host', host,
            '--html', f"performance_results/quick_test_{config['users']}_users.html",
            '--csv', f"performance_results/quick_test_{config['users']}_users"
        ]
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            end_time = time.time()
            
            if result.returncode == 0:
                print(f"   ✅ Test {i} completed in {end_time - start_time:.1f} seconds")
                results.append({
                    'test': i,
                    'users': config['users'],
                    'success': True,
                    'duration': end_time - start_time
                })
            else:
                print(f"   ❌ Test {i} failed")
                print(f"   Error: {result.stderr}")
                results.append({
                    'test': i,
                    'users': config['users'],
                    'success': False,
                    'error': result.stderr
                })
        
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Test {i} timed out")
            results.append({
                'test': i,
                'users': config['users'],
                'success': False,
                'error': 'Test timed out'
            })
        except Exception as e:
            print(f"   ❌ Test {i} failed with exception: {e}")
            results.append({
                'test': i,
                'users': config['users'],
                'success': False,
                'error': str(e)
            })
        
        # Wait between tests
        if i < len(test_configs):
            print("   Waiting 10 seconds before next test...")
            time.sleep(10)
        
        print()
    
    return results

def generate_quick_summary(results):
    """Generate a quick summary of test results."""
    print("📊 Test Summary:")
    print("-" * 40)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
    if failed_tests:
        print(f"❌ Failed tests: {len(failed_tests)}")
        for test in failed_tests:
            print(f"   - Test {test['test']} ({test['users']} users): {test['error']}")
    
    print()
    print("📁 Results Location:")
    print("   - performance_results/ directory")
    print("   - HTML reports: quick_test_*_users.html")
    print("   - CSV data: quick_test_*_users_stats.csv")
    
    if successful_tests:
        print()
        print("📈 Next Steps:")
        print("   1. Open HTML reports in your browser for detailed analysis")
        print("   2. Run 'python generate_performance_comparison.py' for comparison report")
        print("   3. Check application logs for any errors during testing")

def main():
    print_banner()
    
    if not check_environment():
        sys.exit(1)
    
    print("Press Enter to start the quick performance test, or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        sys.exit(0)
    
    print()
    results = run_quick_test()
    
    print("=" * 60)
    print("QUICK PERFORMANCE TEST COMPLETED")
    print("=" * 60)
    generate_quick_summary(results)
    
    print()
    print("For more detailed testing options, see PERFORMANCE_TESTING_GUIDE.md")

if __name__ == "__main__":
    main()
