#!/usr/bin/env python3
"""
PRECISE-HBR Load Test Analysis Tool
Analyzes and compares load test results from 1, 10, and 30 concurrent users
"""

import json
import csv
import os
import sys
from datetime import datetime
from pathlib import Path


def parse_csv_stats(csv_file):
    """Parse Locust CSV stats file"""
    stats = {}
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Name'] == 'Aggregated':
                    stats = {
                        'requests': int(row['Request Count']),
                        'failures': int(row['Failure Count']),
                        'avg_response_time': float(row['Average Response Time']),
                        'min_response_time': float(row['Min Response Time']),
                        'max_response_time': float(row['Max Response Time']),
                        'median_response_time': float(row['Median Response Time']),
                        'rps': float(row['Requests/s']) if 'Requests/s' in row else 0,
                        'failure_rate': (int(row['Failure Count']) / int(row['Request Count']) * 100) if int(row['Request Count']) > 0 else 0
                    }
                    break
    except Exception as e:
        print(f"Error parsing {csv_file}: {e}")
    return stats


def parse_json_report(json_file):
    """Parse performance test JSON report"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error parsing {json_file}: {e}")
        return None


def find_test_files(directory):
    """Find all test result files"""
    test_files = {
        1: {'csv': None, 'json': None, 'html': None},
        10: {'csv': None, 'json': None, 'html': None},
        30: {'csv': None, 'json': None, 'html': None}
    }
    
    directory = Path(directory)
    if not directory.exists():
        print(f"Directory {directory} does not exist!")
        return test_files
    
    # Find the most recent test files for each user count
    for user_count in [1, 10, 30]:
        pattern = f"test_{user_count}user"
        
        # Find CSV files
        csv_files = list(directory.glob(f"{pattern}*_stats.csv"))
        if csv_files:
            test_files[user_count]['csv'] = sorted(csv_files)[-1]
        
        # Find JSON files
        json_files = list(directory.glob(f"performance_test_{user_count}users_*.json"))
        if json_files:
            test_files[user_count]['json'] = sorted(json_files)[-1]
        
        # Find HTML files
        html_files = list(directory.glob(f"{pattern}*.html"))
        if html_files:
            test_files[user_count]['html'] = sorted(html_files)[-1]
    
    return test_files


def generate_comparison_report(test_files, output_dir):
    """Generate comparison report"""
    results = {}
    
    # Parse results for each user count
    for user_count, files in test_files.items():
        if files['csv']:
            print(f"Analyzing {user_count} user test: {files['csv']}")
            stats = parse_csv_stats(files['csv'])
            if stats:
                results[user_count] = stats
        
        # Also parse JSON if available
        if files['json']:
            json_data = parse_json_report(files['json'])
            if json_data and user_count in results:
                results[user_count]['json_report'] = json_data
    
    if not results:
        print("No test results found!")
        return
    
    # Generate comparison report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path(output_dir) / f"load_test_comparison_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PRECISE-HBR LOAD TEST COMPARISON REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Summary table
        f.write("SUMMARY COMPARISON\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Metric':<35} {'1 User':>12} {'10 Users':>12} {'30 Users':>12}\n")
        f.write("-" * 80 + "\n")
        
        # Total requests
        f.write(f"{'Total Requests':<35} ")
        for users in [1, 10, 30]:
            if users in results:
                f.write(f"{results[users]['requests']:>12,} ")
            else:
                f.write(f"{'N/A':>12} ")
        f.write("\n")
        
        # Failures
        f.write(f"{'Total Failures':<35} ")
        for users in [1, 10, 30]:
            if users in results:
                f.write(f"{results[users]['failures']:>12,} ")
            else:
                f.write(f"{'N/A':>12} ")
        f.write("\n")
        
        # Failure Rate
        f.write(f"{'Failure Rate (%)':<35} ")
        for users in [1, 10, 30]:
            if users in results:
                f.write(f"{results[users]['failure_rate']:>11.2f}% ")
            else:
                f.write(f"{'N/A':>12} ")
        f.write("\n")
        
        # Average Response Time
        f.write(f"{'Avg Response Time (ms)':<35} ")
        for users in [1, 10, 30]:
            if users in results:
                f.write(f"{results[users]['avg_response_time']:>11.1f}  ")
            else:
                f.write(f"{'N/A':>12} ")
        f.write("\n")
        
        # Median Response Time
        f.write(f"{'Median Response Time (ms)':<35} ")
        for users in [1, 10, 30]:
            if users in results:
                f.write(f"{results[users]['median_response_time']:>11.1f}  ")
            else:
                f.write(f"{'N/A':>12} ")
        f.write("\n")
        
        # Min Response Time
        f.write(f"{'Min Response Time (ms)':<35} ")
        for users in [1, 10, 30]:
            if users in results:
                f.write(f"{results[users]['min_response_time']:>11.1f}  ")
            else:
                f.write(f"{'N/A':>12} ")
        f.write("\n")
        
        # Max Response Time
        f.write(f"{'Max Response Time (ms)':<35} ")
        for users in [1, 10, 30]:
            if users in results:
                f.write(f"{results[users]['max_response_time']:>11.1f}  ")
            else:
                f.write(f"{'N/A':>12} ")
        f.write("\n")
        
        # Requests per second
        f.write(f"{'Requests/sec':<35} ")
        for users in [1, 10, 30]:
            if users in results:
                f.write(f"{results[users]['rps']:>11.2f}  ")
            else:
                f.write(f"{'N/A':>12} ")
        f.write("\n")
        
        f.write("-" * 80 + "\n\n")
        
        # Performance Analysis
        f.write("PERFORMANCE ANALYSIS\n")
        f.write("-" * 80 + "\n\n")
        
        # Calculate scaling factors
        if 1 in results and 10 in results:
            response_time_increase_10 = ((results[10]['avg_response_time'] - results[1]['avg_response_time']) / results[1]['avg_response_time']) * 100
            throughput_increase_10 = ((results[10]['rps'] - results[1]['rps']) / results[1]['rps']) * 100
            
            f.write(f"1 User → 10 Users:\n")
            f.write(f"  - Response time increased by {response_time_increase_10:+.1f}%\n")
            f.write(f"  - Throughput increased by {throughput_increase_10:+.1f}%\n")
            f.write(f"  - Scaling efficiency: {(throughput_increase_10 / 900):.1%} (ideal: 100%)\n")
            f.write("\n")
        
        if 10 in results and 30 in results:
            response_time_increase_30 = ((results[30]['avg_response_time'] - results[10]['avg_response_time']) / results[10]['avg_response_time']) * 100
            throughput_increase_30 = ((results[30]['rps'] - results[10]['rps']) / results[10]['rps']) * 100
            
            f.write(f"10 Users → 30 Users:\n")
            f.write(f"  - Response time increased by {response_time_increase_30:+.1f}%\n")
            f.write(f"  - Throughput increased by {throughput_increase_30:+.1f}%\n")
            f.write(f"  - Scaling efficiency: {(throughput_increase_30 / 200):.1%} (ideal: 100%)\n")
            f.write("\n")
        
        if 1 in results and 30 in results:
            response_time_increase_total = ((results[30]['avg_response_time'] - results[1]['avg_response_time']) / results[1]['avg_response_time']) * 100
            throughput_increase_total = ((results[30]['rps'] - results[1]['rps']) / results[1]['rps']) * 100
            
            f.write(f"1 User → 30 Users:\n")
            f.write(f"  - Response time increased by {response_time_increase_total:+.1f}%\n")
            f.write(f"  - Throughput increased by {throughput_increase_total:+.1f}%\n")
            f.write(f"  - Overall scaling efficiency: {(throughput_increase_total / 2900):.1%} (ideal: 100%)\n")
            f.write("\n")
        
        # Recommendations
        f.write("RECOMMENDATIONS\n")
        f.write("-" * 80 + "\n")
        
        if 30 in results:
            avg_time = results[30]['avg_response_time']
            failure_rate = results[30]['failure_rate']
            
            if avg_time < 500 and failure_rate < 1:
                f.write("✓ EXCELLENT: System handles 30 concurrent users well.\n")
                f.write("  - Response times are fast (<500ms)\n")
                f.write("  - Failure rate is low (<1%)\n")
                f.write("  - System is ready for production use\n")
            elif avg_time < 1000 and failure_rate < 5:
                f.write("✓ GOOD: System performs acceptably under load.\n")
                f.write("  - Response times are reasonable (<1s)\n")
                f.write("  - Failure rate is acceptable (<5%)\n")
                f.write("  - Consider optimization for better performance\n")
            elif avg_time < 2000 and failure_rate < 10:
                f.write("⚠ MODERATE: System shows signs of stress.\n")
                f.write("  - Response times are getting slow (>1s)\n")
                f.write("  - Failure rate is concerning (>5%)\n")
                f.write("  - Optimization recommended before production\n")
            else:
                f.write("✗ POOR: System struggles under load.\n")
                f.write("  - Response times are too slow (>2s)\n")
                f.write("  - Failure rate is high (>10%)\n")
                f.write("  - Significant optimization required\n")
        
        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
    
    print(f"\nComparison report saved to: {report_file}")
    
    # Print summary to console
    print("\n" + "=" * 80)
    print("LOAD TEST SUMMARY")
    print("=" * 80)
    for user_count in [1, 10, 30]:
        if user_count in results:
            print(f"\n{user_count} User{'s' if user_count > 1 else ''}:")
            print(f"  Requests: {results[user_count]['requests']:,}")
            print(f"  Failures: {results[user_count]['failures']:,} ({results[user_count]['failure_rate']:.2f}%)")
            print(f"  Avg Response Time: {results[user_count]['avg_response_time']:.1f}ms")
            print(f"  Throughput: {results[user_count]['rps']:.2f} req/s")
    print("=" * 80)
    
    return report_file


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_load_tests.py <results_directory>")
        sys.exit(1)
    
    results_dir = sys.argv[1]
    
    print("Searching for test results...")
    test_files = find_test_files(results_dir)
    
    # Check if any files were found
    found_any = any(any(files.values()) for files in test_files.values())
    if not found_any:
        print("No test results found in the specified directory!")
        sys.exit(1)
    
    print("\nGenerating comparison report...")
    generate_comparison_report(test_files, results_dir)
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()

