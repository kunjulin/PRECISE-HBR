#!/usr/bin/env python3
"""
Session Information Extractor
Helps extract session cookie and patient ID for performance testing.
"""

import requests
import json
import sys
import re
from urllib.parse import urlparse, parse_qs

def extract_from_browser_cookies():
    """Instructions for manual extraction from browser."""
    print("=" * 60)
    print("MANUAL EXTRACTION FROM BROWSER")
    print("=" * 60)
    print()
    print("1. Open your browser and navigate to your SMART FHIR app")
    print("2. Complete the login process")
    print("3. Open Developer Tools (F12)")
    print("4. Go to Application/Storage tab")
    print("5. Expand 'Cookies' in the left sidebar")
    print("6. Click on your app's URL (e.g., http://localhost:8080)")
    print("7. Find the 'session' cookie and copy its value")
    print()
    print("For Patient ID:")
    print("- Check the main page for displayed Patient ID")
    print("- Or check Network tab for /api/calculate_risk requests")
    print("- Or use browser console to search for patient information")
    print()

def test_session_cookie(host, session_cookie, patient_id=None):
    """Test if the session cookie is valid."""
    print("=" * 60)
    print("TESTING SESSION COOKIE")
    print("=" * 60)
    
    if not session_cookie:
        print("❌ No session cookie provided")
        return False
    
    if not host.startswith('http'):
        host = f'http://{host}'
    
    # Test main page access
    print(f"Testing access to: {host}/main")
    
    headers = {
        'Cookie': f'session={session_cookie}',
        'User-Agent': 'Performance-Test-Script/1.0'
    }
    
    try:
        response = requests.get(f'{host}/main', headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Session cookie is valid - main page accessible")
            
            # Try to extract patient ID from the page
            if not patient_id:
                patient_id = extract_patient_id_from_response(response.text)
                if patient_id:
                    print(f"✅ Patient ID found in page: {patient_id}")
                else:
                    print("⚠️  Could not extract Patient ID from page")
            
            return True, patient_id
            
        elif response.status_code == 302:
            print("⚠️  Session cookie may be expired (redirect detected)")
            print("   You may need to log in again")
            return False, None
            
        else:
            print(f"❌ Session cookie test failed: HTTP {response.status_code}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("   Make sure your app is running")
        return False, None

def extract_patient_id_from_response(html_content):
    """Try to extract patient ID from HTML response."""
    patterns = [
        r'Patient ID[:\s]*([A-Za-z0-9\-_]+)',
        r'patient[_\-]?id[:\s]*["\']?([A-Za-z0-9\-_]+)["\']?',
        r'patientId[:\s]*["\']?([A-Za-z0-9\-_]+)["\']?',
        r'smart[-_](\d+)',
        r'patient[-_](\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def test_api_with_credentials(host, session_cookie, patient_id):
    """Test the API endpoint with the provided credentials."""
    print("=" * 60)
    print("TESTING API ENDPOINT")
    print("=" * 60)
    
    if not all([host, session_cookie, patient_id]):
        print("❌ Missing required parameters for API test")
        return False
    
    if not host.startswith('http'):
        host = f'http://{host}'
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cookie': f'session={session_cookie}'
    }
    
    payload = {
        "patientId": patient_id
    }
    
    try:
        print(f"Testing: POST {host}/api/calculate_risk")
        print(f"Patient ID: {patient_id}")
        
        response = requests.post(
            f'{host}/api/calculate_risk',
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ API test successful!")
                print(f"   Response contains: {list(result.keys())}")
                if 'total_score' in result:
                    print(f"   Risk score: {result['total_score']}")
                return True
            except json.JSONDecodeError:
                print("⚠️  API returned 200 but invalid JSON")
                return False
        else:
            print(f"❌ API test failed: HTTP {response.status_code}")
            if response.text:
                print(f"   Error: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API test error: {e}")
        return False

def generate_env_commands(session_cookie, patient_id, host='http://localhost:8080'):
    """Generate environment variable commands."""
    print("=" * 60)
    print("ENVIRONMENT VARIABLE COMMANDS")
    print("=" * 60)
    print()
    print("Copy and run these commands in your terminal:")
    print()
    print("Windows (Command Prompt):")
    print(f'set LOCUST_SESSION_COOKIE={session_cookie}')
    print(f'set LOCUST_TEST_PATIENT_ID={patient_id}')
    print(f'set LOCUST_HOST={host}')
    print()
    print("Windows (PowerShell):")
    print(f'$env:LOCUST_SESSION_COOKIE="{session_cookie}"')
    print(f'$env:LOCUST_TEST_PATIENT_ID="{patient_id}"')
    print(f'$env:LOCUST_HOST="{host}"')
    print()
    print("Linux/Mac:")
    print(f'export LOCUST_SESSION_COOKIE="{session_cookie}"')
    print(f'export LOCUST_TEST_PATIENT_ID="{patient_id}"')
    print(f'export LOCUST_HOST="{host}"')
    print()

def interactive_mode():
    """Interactive mode to guide user through the process."""
    print("=" * 60)
    print("INTERACTIVE SESSION INFO EXTRACTION")
    print("=" * 60)
    print()
    
    # Get host
    host = input("Enter your app URL (default: http://localhost:8080): ").strip()
    if not host:
        host = 'http://localhost:8080'
    
    print()
    print("Now you need to get your session cookie:")
    print("1. Open your browser and go to your app")
    print("2. Complete the login process")
    print("3. Open Developer Tools (F12)")
    print("4. Go to Application > Cookies")
    print("5. Find the 'session' cookie and copy its value")
    print()
    
    session_cookie = input("Paste your session cookie here: ").strip()
    
    if not session_cookie:
        print("❌ No session cookie provided. Exiting.")
        return
    
    # Test the session cookie
    valid, extracted_patient_id = test_session_cookie(host, session_cookie)
    
    if not valid:
        print("❌ Session cookie test failed. Please try again.")
        return
    
    # Get patient ID
    patient_id = extracted_patient_id
    if not patient_id:
        print()
        print("Patient ID not found automatically. Please provide it:")
        print("- Check your app's main page for the Patient ID")
        print("- Or check the Network tab for API requests")
        print()
        patient_id = input("Enter Patient ID: ").strip()
    
    if not patient_id:
        print("❌ No patient ID provided. Exiting.")
        return
    
    # Test API
    print()
    api_works = test_api_with_credentials(host, session_cookie, patient_id)
    
    if api_works:
        print()
        print("🎉 All tests passed! Your credentials are ready for performance testing.")
        generate_env_commands(session_cookie, patient_id, host)
        
        print()
        print("Next steps:")
        print("1. Run the environment variable commands above")
        print("2. Execute: python quick_performance_test.py")
        print("3. Or run: run_performance_tests.bat (Windows) / ./run_performance_tests.sh (Linux/Mac)")
    else:
        print()
        print("❌ API test failed. Please check your credentials and try again.")

def main():
    """Main function."""
    if len(sys.argv) == 1:
        # Interactive mode
        interactive_mode()
    elif len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', 'help']:
        # Help mode
        print("Session Information Extractor")
        print("Usage:")
        print("  python extract_session_info.py              # Interactive mode")
        print("  python extract_session_info.py help         # Show this help")
        print("  python extract_session_info.py test <cookie> <patient_id> [host]  # Test credentials")
        print()
        extract_from_browser_cookies()
    elif len(sys.argv) >= 4 and sys.argv[1] == 'test':
        # Test mode
        session_cookie = sys.argv[2]
        patient_id = sys.argv[3]
        host = sys.argv[4] if len(sys.argv) > 4 else 'http://localhost:8080'
        
        valid, _ = test_session_cookie(host, session_cookie, patient_id)
        if valid:
            api_works = test_api_with_credentials(host, session_cookie, patient_id)
            if api_works:
                generate_env_commands(session_cookie, patient_id, host)
    else:
        print("Invalid arguments. Use 'python extract_session_info.py help' for usage.")

if __name__ == "__main__":
    main()
