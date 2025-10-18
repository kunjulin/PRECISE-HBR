import os
import json
import time
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

class WebsiteUser(HttpUser):
    """
    Simulates a user interacting with the SMART on FHIR application.
    Enhanced for comprehensive performance testing.
    """
    wait_time = between(1, 3)  # Reduced wait time for more intensive testing

    def on_start(self):
        """
        This method is called when a new user is started.
        We will use a session cookie from an environment variable for authentication.
        
        **Instructions for Test Execution:**
        1. Manually log in to the application through a browser.
        2. Use browser developer tools to find the value of the 'session' cookie.
        3. Set this value as an environment variable named 'LOCUST_SESSION_COOKIE'
           and the patient ID as 'LOCUST_TEST_PATIENT_ID' before running Locust.
        """
        self.session_cookie = os.environ.get("LOCUST_SESSION_COOKIE")
        self.patient_id = os.environ.get("LOCUST_TEST_PATIENT_ID")
        self.test_mode = os.environ.get("LOCUST_TEST_MODE", "normal")  # normal, stress, spike

        if not self.session_cookie or not self.patient_id:
            print("="*80)
            print("ERROR: Environment variables LOCUST_SESSION_COOKIE and LOCUST_TEST_PATIENT_ID must be set.")
            print("Please follow the instructions in the on_start method.")
            print("="*80)
            if hasattr(self.environment.runner, 'quit'):
                self.environment.runner.quit()
            return
            
        # Manually set the Cookie header for each request.
        self.cookie_header = f"session={self.session_cookie}"

    @task(5)  # Higher weight for main functionality
    def calculate_risk(self):
        """
        Simulates a user calculating the PRECISE-HBR risk score.
        """
        if self.patient_id:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Cookie': self.cookie_header
            }
            payload = {
                "patientId": self.patient_id,
            }
            
            with self.client.post(
                "/api/calculate_risk",
                json=payload,
                headers=headers,
                name="/api/calculate_risk",
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    try:
                        json_response = response.json()
                        if 'total_score' in json_response:
                            response.success()
                        else:
                            response.failure("Missing total_score in response")
                    except json.JSONDecodeError:
                        response.failure("Invalid JSON response")
                elif response.status_code == 401:
                    response.failure("Authentication failed")
                elif response.status_code == 503:
                    response.failure("Service unavailable")
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")

    @task(2)
    def load_main_page(self):
        """
        Simulates loading the main application page.
        """
        headers = {'Cookie': self.cookie_header}
        with self.client.get("/main", headers=headers, name="/main", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 302:
                response.success()  # Redirect is expected behavior
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def load_docs_page(self):
        """
        Simulates loading the documentation page.
        """
        with self.client.get("/docs", name="/docs", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def health_check(self):
        """
        Simple health check by accessing the root page.
        """
        with self.client.get("/", name="/health_check", catch_response=True) as response:
            if response.status_code in [200, 302]:  # Both OK and redirect are acceptable
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

# Performance monitoring and reporting
performance_data = {
    'test_start_time': None,
    'user_counts': [],
    'response_times': [],
    'error_rates': [],
    'throughput': []
}

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Record test start time"""
    performance_data['test_start_time'] = datetime.now()
    print(f"Performance test started at {performance_data['test_start_time']}")

@events.test_stop.add_listener 
def on_test_stop(environment, **kwargs):
    """Generate performance report"""
    test_end_time = datetime.now()
    test_duration = test_end_time - performance_data['test_start_time']
    
    # Get final stats
    stats = environment.runner.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    error_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    
    # Generate report
    report = {
        'test_summary': {
            'start_time': performance_data['test_start_time'].isoformat(),
            'end_time': test_end_time.isoformat(),
            'duration_seconds': test_duration.total_seconds(),
            'total_requests': total_requests,
            'total_failures': total_failures,
            'error_rate_percent': round(error_rate, 2),
            'average_response_time': round(stats.total.avg_response_time, 2),
            'min_response_time': stats.total.min_response_time,
            'max_response_time': stats.total.max_response_time,
            'requests_per_second': round(stats.total.current_rps, 2),
            'user_count': environment.runner.user_count
        },
        'endpoint_stats': {}
    }
    
    # Add per-endpoint statistics
    for name, stat in stats.entries.items():
        if name != ('Aggregated', ''):
            report['endpoint_stats'][name[0]] = {
                'requests': stat.num_requests,
                'failures': stat.num_failures,
                'avg_response_time': round(stat.avg_response_time, 2),
                'min_response_time': stat.min_response_time,
                'max_response_time': stat.max_response_time,
                'requests_per_second': round(stat.current_rps, 2),
                'error_rate_percent': round((stat.num_failures / stat.num_requests * 100) if stat.num_requests > 0 else 0, 2)
            }
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    users = environment.runner.user_count
    filename = f"performance_test_{users}users_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nPerformance test completed!")
    print(f"Duration: {test_duration.total_seconds():.1f} seconds")
    print(f"Users: {users}")
    print(f"Total requests: {total_requests}")
    print(f"Error rate: {error_rate:.2f}%")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.current_rps:.2f}")
    print(f"Report saved to: {filename}")

# Custom user class for stress testing
class StressTestUser(WebsiteUser):
    """
    Stress test user with more aggressive behavior
    """
    wait_time = between(0.5, 1.5)  # Shorter wait times for stress testing
    
    @task(8)  # Even higher weight for main API
    def calculate_risk_stress(self):
        self.calculate_risk()
    
    @task(3)
    def rapid_page_loads(self):
        self.load_main_page()
        
    @task(2) 
    def concurrent_requests(self):
        """Make multiple concurrent requests to simulate heavy load"""
        self.calculate_risk()
        self.load_main_page()
