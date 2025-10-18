#!/usr/bin/env python3
"""
Performance Comparison Report Generator
Analyzes Locust test results and generates comprehensive comparison reports.
"""

import json
import csv
import glob
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import pandas as pd

class PerformanceAnalyzer:
    def __init__(self, results_dir: str = "performance_results"):
        self.results_dir = results_dir
        self.test_data = {}
        
    def load_test_results(self) -> bool:
        """Load all test results from CSV and JSON files."""
        try:
            # Load CSV results
            csv_files = glob.glob(f"{self.results_dir}/*_stats.csv")
            json_files = glob.glob(f"{self.results_dir}/*.json")
            
            if not csv_files and not json_files:
                print(f"No test result files found in {self.results_dir}")
                return False
            
            # Process CSV files (Locust default output)
            for csv_file in csv_files:
                test_name = os.path.basename(csv_file).replace('_stats.csv', '')
                self.test_data[test_name] = self._load_csv_data(csv_file)
            
            # Process JSON files (our custom output)
            for json_file in json_files:
                if 'performance_test_' in json_file:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        users = data['test_summary']['user_count']
                        test_name = f"test_{users}_users"
                        if test_name in self.test_data:
                            self.test_data[test_name].update({'custom_metrics': data})
                        else:
                            self.test_data[test_name] = {'custom_metrics': data}
            
            print(f"Loaded {len(self.test_data)} test result sets")
            return True
            
        except Exception as e:
            print(f"Error loading test results: {e}")
            return False
    
    def _load_csv_data(self, csv_file: str) -> Dict[str, Any]:
        """Load data from Locust CSV output."""
        data = {'endpoints': {}, 'summary': {}}
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Type'] == 'GET' or row['Type'] == 'POST':
                        endpoint = row['Name']
                        data['endpoints'][endpoint] = {
                            'method': row['Type'],
                            'requests': int(row['Request Count']),
                            'failures': int(row['Failure Count']),
                            'avg_response_time': float(row['Average Response Time']),
                            'min_response_time': float(row['Min Response Time']),
                            'max_response_time': float(row['Max Response Time']),
                            'requests_per_second': float(row['Requests/s'])
                        }
                    elif row['Type'] == 'Aggregated':
                        data['summary'] = {
                            'total_requests': int(row['Request Count']),
                            'total_failures': int(row['Failure Count']),
                            'avg_response_time': float(row['Average Response Time']),
                            'min_response_time': float(row['Min Response Time']),
                            'max_response_time': float(row['Max Response Time']),
                            'requests_per_second': float(row['Requests/s'])
                        }
        except Exception as e:
            print(f"Error reading CSV file {csv_file}: {e}")
        
        return data
    
    def generate_comparison_report(self) -> str:
        """Generate a comprehensive comparison report."""
        if not self.test_data:
            return "No test data available for comparison."
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PERFORMANCE COMPARISON REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary table
        report_lines.append("SUMMARY COMPARISON")
        report_lines.append("-" * 50)
        report_lines.append(f"{'Test':<15} {'Users':<8} {'Requests':<10} {'Failures':<10} {'Avg RT (ms)':<12} {'RPS':<8} {'Error %':<8}")
        report_lines.append("-" * 80)
        
        test_summaries = []
        for test_name, data in sorted(self.test_data.items()):
            users = self._extract_user_count(test_name)
            
            if 'custom_metrics' in data:
                summary = data['custom_metrics']['test_summary']
                requests = summary['total_requests']
                failures = summary['total_failures']
                avg_rt = summary['average_response_time']
                rps = summary['requests_per_second']
                error_rate = summary['error_rate_percent']
            elif 'summary' in data:
                summary = data['summary']
                requests = summary['total_requests']
                failures = summary['total_failures']
                avg_rt = summary['avg_response_time']
                rps = summary['requests_per_second']
                error_rate = (failures / requests * 100) if requests > 0 else 0
            else:
                continue
            
            test_summaries.append({
                'test_name': test_name,
                'users': users,
                'requests': requests,
                'failures': failures,
                'avg_rt': avg_rt,
                'rps': rps,
                'error_rate': error_rate
            })
            
            report_lines.append(f"{test_name:<15} {users:<8} {requests:<10} {failures:<10} {avg_rt:<12.1f} {rps:<8.1f} {error_rate:<8.1f}")
        
        report_lines.append("")
        
        # Performance analysis
        if len(test_summaries) >= 2:
            report_lines.append("PERFORMANCE ANALYSIS")
            report_lines.append("-" * 50)
            
            # Sort by user count for comparison
            test_summaries.sort(key=lambda x: x['users'])
            
            for i in range(1, len(test_summaries)):
                current = test_summaries[i]
                previous = test_summaries[i-1]
                
                rt_change = ((current['avg_rt'] - previous['avg_rt']) / previous['avg_rt']) * 100
                rps_change = ((current['rps'] - previous['rps']) / previous['rps']) * 100
                
                report_lines.append(f"From {previous['users']} to {current['users']} users:")
                report_lines.append(f"  - Response time: {rt_change:+.1f}% ({previous['avg_rt']:.1f}ms → {current['avg_rt']:.1f}ms)")
                report_lines.append(f"  - Throughput: {rps_change:+.1f}% ({previous['rps']:.1f} → {current['rps']:.1f} RPS)")
                report_lines.append(f"  - Error rate: {previous['error_rate']:.1f}% → {current['error_rate']:.1f}%")
                report_lines.append("")
        
        # Endpoint breakdown
        report_lines.append("ENDPOINT PERFORMANCE BREAKDOWN")
        report_lines.append("-" * 50)
        
        endpoints = set()
        for data in self.test_data.values():
            if 'custom_metrics' in data:
                endpoints.update(data['custom_metrics']['endpoint_stats'].keys())
            elif 'endpoints' in data:
                endpoints.update(data['endpoints'].keys())
        
        for endpoint in sorted(endpoints):
            report_lines.append(f"\nEndpoint: {endpoint}")
            report_lines.append(f"{'Test':<15} {'Requests':<10} {'Avg RT (ms)':<12} {'RPS':<8} {'Error %':<8}")
            report_lines.append("-" * 60)
            
            for test_name, data in sorted(self.test_data.items()):
                users = self._extract_user_count(test_name)
                
                if 'custom_metrics' in data and endpoint in data['custom_metrics']['endpoint_stats']:
                    stats = data['custom_metrics']['endpoint_stats'][endpoint]
                    report_lines.append(f"{users:<15} {stats['requests']:<10} {stats['avg_response_time']:<12.1f} {stats['requests_per_second']:<8.1f} {stats['error_rate_percent']:<8.1f}")
                elif 'endpoints' in data and endpoint in data['endpoints']:
                    stats = data['endpoints'][endpoint]
                    error_rate = (stats['failures'] / stats['requests'] * 100) if stats['requests'] > 0 else 0
                    report_lines.append(f"{users:<15} {stats['requests']:<10} {stats['avg_response_time']:<12.1f} {stats['requests_per_second']:<8.1f} {error_rate:<8.1f}")
        
        # Recommendations
        report_lines.append("\n\nRECOMMENDATIONS")
        report_lines.append("-" * 50)
        
        if test_summaries:
            highest_load = max(test_summaries, key=lambda x: x['users'])
            
            if highest_load['error_rate'] > 5:
                report_lines.append("⚠️  HIGH ERROR RATE DETECTED:")
                report_lines.append(f"   At {highest_load['users']} users, error rate is {highest_load['error_rate']:.1f}%")
                report_lines.append("   Consider optimizing application or infrastructure.")
                report_lines.append("")
            
            if highest_load['avg_rt'] > 2000:
                report_lines.append("⚠️  HIGH RESPONSE TIMES DETECTED:")
                report_lines.append(f"   At {highest_load['users']} users, average response time is {highest_load['avg_rt']:.1f}ms")
                report_lines.append("   Consider performance optimizations.")
                report_lines.append("")
            
            # Calculate scalability
            if len(test_summaries) >= 2:
                linear_scaling = test_summaries[0]['rps'] * (highest_load['users'] / test_summaries[0]['users'])
                actual_scaling = highest_load['rps']
                scaling_efficiency = (actual_scaling / linear_scaling) * 100
                
                report_lines.append(f"SCALABILITY ANALYSIS:")
                report_lines.append(f"   Linear scaling expectation: {linear_scaling:.1f} RPS")
                report_lines.append(f"   Actual performance: {actual_scaling:.1f} RPS")
                report_lines.append(f"   Scaling efficiency: {scaling_efficiency:.1f}%")
                
                if scaling_efficiency < 80:
                    report_lines.append("   ⚠️  Poor scaling efficiency - investigate bottlenecks")
                elif scaling_efficiency > 95:
                    report_lines.append("   ✅ Excellent scaling efficiency")
                else:
                    report_lines.append("   ✅ Good scaling efficiency")
        
        return "\n".join(report_lines)
    
    def _extract_user_count(self, test_name: str) -> int:
        """Extract user count from test name."""
        try:
            if 'test_1_user' in test_name:
                return 1
            elif 'test_10_user' in test_name:
                return 10
            elif 'test_100_user' in test_name:
                return 100
            else:
                # Try to extract number from test name
                import re
                match = re.search(r'(\d+)', test_name)
                return int(match.group(1)) if match else 0
        except:
            return 0
    
    def generate_charts(self) -> bool:
        """Generate performance comparison charts."""
        try:
            if not self.test_data:
                return False
            
            # Prepare data for charts
            users = []
            avg_response_times = []
            requests_per_second = []
            error_rates = []
            
            for test_name, data in sorted(self.test_data.items()):
                user_count = self._extract_user_count(test_name)
                if user_count == 0:
                    continue
                
                if 'custom_metrics' in data:
                    summary = data['custom_metrics']['test_summary']
                    avg_rt = summary['average_response_time']
                    rps = summary['requests_per_second']
                    error_rate = summary['error_rate_percent']
                elif 'summary' in data:
                    summary = data['summary']
                    avg_rt = summary['avg_response_time']
                    rps = summary['requests_per_second']
                    error_rate = (summary['total_failures'] / summary['total_requests'] * 100) if summary['total_requests'] > 0 else 0
                else:
                    continue
                
                users.append(user_count)
                avg_response_times.append(avg_rt)
                requests_per_second.append(rps)
                error_rates.append(error_rate)
            
            if not users:
                return False
            
            # Create charts
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Performance Test Results Comparison', fontsize=16, fontweight='bold')
            
            # Response Time Chart
            ax1.plot(users, avg_response_times, 'bo-', linewidth=2, markersize=8)
            ax1.set_xlabel('Concurrent Users')
            ax1.set_ylabel('Average Response Time (ms)')
            ax1.set_title('Response Time vs User Load')
            ax1.grid(True, alpha=0.3)
            ax1.set_xscale('log')
            
            # Throughput Chart
            ax2.plot(users, requests_per_second, 'go-', linewidth=2, markersize=8)
            ax2.set_xlabel('Concurrent Users')
            ax2.set_ylabel('Requests per Second')
            ax2.set_title('Throughput vs User Load')
            ax2.grid(True, alpha=0.3)
            ax2.set_xscale('log')
            
            # Error Rate Chart
            ax3.plot(users, error_rates, 'ro-', linewidth=2, markersize=8)
            ax3.set_xlabel('Concurrent Users')
            ax3.set_ylabel('Error Rate (%)')
            ax3.set_title('Error Rate vs User Load')
            ax3.grid(True, alpha=0.3)
            ax3.set_xscale('log')
            
            # Summary Bar Chart
            x_pos = range(len(users))
            ax4.bar([f"{u} users" for u in users], requests_per_second, alpha=0.7, color='skyblue')
            ax4.set_ylabel('Requests per Second')
            ax4.set_title('Throughput Comparison')
            ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(f'{self.results_dir}/performance_comparison_charts.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Charts saved to {self.results_dir}/performance_comparison_charts.png")
            return True
            
        except ImportError:
            print("Matplotlib not available. Skipping chart generation.")
            return False
        except Exception as e:
            print(f"Error generating charts: {e}")
            return False

def main():
    """Main function to generate performance comparison report."""
    analyzer = PerformanceAnalyzer()
    
    if not analyzer.load_test_results():
        print("Failed to load test results. Make sure you have run the performance tests first.")
        sys.exit(1)
    
    # Generate text report
    report = analyzer.generate_comparison_report()
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"performance_results/comparison_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Performance comparison report saved to: {report_file}")
    print("\n" + "="*50)
    print(report)
    
    # Generate charts if possible
    analyzer.generate_charts()

if __name__ == "__main__":
    main()
