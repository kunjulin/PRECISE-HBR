#!/usr/bin/env python3
"""
ONC Compliance: 45 CFR 170.523 (n) - Complaint Process Management Tool

This script helps manage and report complaints received through the application.
It provides functionality to:
- View all complaints
- Filter complaints by date, category, severity
- Generate quarterly reports for ONC submission
- Export complaints to CSV for analysis

Usage:
    python complaint_manager.py list                    # List all complaints
    python complaint_manager.py report 2025 Q4          # Generate quarterly report
    python complaint_manager.py export complaints.csv   # Export to CSV
"""

import json
import os
import sys
import datetime
from collections import defaultdict
from typing import List, Dict
import argparse


class ComplaintManager:
    def __init__(self, complaints_file='instance/complaints/complaints.jsonl'):
        self.complaints_file = complaints_file
        self.complaints = []
        self.load_complaints()
    
    def load_complaints(self):
        """Load all complaints from the JSON Lines file"""
        if not os.path.exists(self.complaints_file):
            print(f"No complaints file found at: {self.complaints_file}")
            print("No complaints have been submitted yet.")
            return
        
        try:
            with open(self.complaints_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.complaints.append(json.loads(line))
            print(f"Loaded {len(self.complaints)} complaint(s)")
        except Exception as e:
            print(f"Error loading complaints: {e}")
            sys.exit(1)
    
    def list_complaints(self, category=None, severity=None, start_date=None, end_date=None):
        """List complaints with optional filters"""
        filtered = self.complaints
        
        if category:
            filtered = [c for c in filtered if c.get('category') == category]
        
        if severity:
            filtered = [c for c in filtered if c.get('severity') == severity]
        
        if start_date:
            filtered = [c for c in filtered if c.get('timestamp', '') >= start_date]
        
        if end_date:
            filtered = [c for c in filtered if c.get('timestamp', '') <= end_date]
        
        if not filtered:
            print("No complaints match the specified filters.")
            return
        
        print(f"\n{'='*100}")
        print(f"COMPLAINT LIST ({len(filtered)} total)")
        print(f"{'='*100}\n")
        
        for i, complaint in enumerate(filtered, 1):
            timestamp = complaint.get('timestamp', 'Unknown')[:19]  # Remove microseconds
            ref_id = complaint.get('reference_id', 'N/A')
            category = complaint.get('category', 'unknown')
            severity = complaint.get('severity', 'unknown')
            complainant = complaint.get('complainant_type', 'unknown')
            subject = complaint.get('subject', 'No subject')
            
            print(f"{i}. [{ref_id}] - {timestamp}")
            print(f"   Complainant: {complainant.capitalize()}")
            print(f"   Category: {category.replace('_', ' ').title()}")
            print(f"   Severity: {severity.upper()}")
            print(f"   Subject: {subject}")
            print(f"   Contact: {complaint.get('contact_email', 'Not provided')}")
            print(f"   {'-'*95}\n")
    
    def generate_quarterly_report(self, year, quarter):
        """Generate ONC quarterly report"""
        # Determine date range for the quarter
        quarter_starts = {
            1: f"{year}-01-01",
            2: f"{year}-04-01",
            3: f"{year}-07-01",
            4: f"{year}-10-01"
        }
        
        quarter_ends = {
            1: f"{year}-03-31T23:59:59",
            2: f"{year}-06-30T23:59:59",
            3: f"{year}-09-30T23:59:59",
            4: f"{year}-12-31T23:59:59"
        }
        
        start_date = quarter_starts.get(quarter)
        end_date = quarter_ends.get(quarter)
        
        if not start_date:
            print(f"Invalid quarter: {quarter}. Must be 1, 2, 3, or 4.")
            return
        
        # Filter complaints for this quarter
        quarterly_complaints = [
            c for c in self.complaints
            if start_date <= c.get('timestamp', '') <= end_date
        ]
        
        # Statistics
        total_count = len(quarterly_complaints)
        
        # Count by category
        by_category = defaultdict(int)
        for c in quarterly_complaints:
            by_category[c.get('category', 'unknown')] += 1
        
        # Count by complainant type
        by_complainant = defaultdict(int)
        for c in quarterly_complaints:
            by_complainant[c.get('complainant_type', 'unknown')] += 1
        
        # Count by severity
        by_severity = defaultdict(int)
        for c in quarterly_complaints:
            by_severity[c.get('severity', 'unknown')] += 1
        
        # Generate report
        print(f"\n{'='*100}")
        print(f"ONC QUARTERLY COMPLAINT REPORT")
        print(f"Application: SMART on FHIR PRECISE-HBR Calculator")
        print(f"Reporting Period: Q{quarter} {year} ({start_date} to {end_date[:10]})")
        print(f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*100}\n")
        
        print(f"SUMMARY")
        print(f"{'-'*100}")
        print(f"Total Complaints Received: {total_count}\n")
        
        if total_count == 0:
            print("No complaints were received during this quarter.\n")
            print("This report fulfills the requirement under 45 CFR 170.523 (n) to submit")
            print("quarterly complaint information to the National Coordinator.")
            return
        
        print(f"COMPLAINTS BY CATEGORY (Nature/Substance)")
        print(f"{'-'*100}")
        for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_count) * 100
            category_name = category.replace('_', ' ').title()
            print(f"  {category_name:.<50} {count:>3} ({percentage:>5.1f}%)")
        print()
        
        print(f"COMPLAINTS BY COMPLAINANT TYPE")
        print(f"{'-'*100}")
        for complainant, count in sorted(by_complainant.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_count) * 100
            complainant_name = complainant.replace('_', ' ').title()
            print(f"  {complainant_name:.<50} {count:>3} ({percentage:>5.1f}%)")
        print()
        
        print(f"COMPLAINTS BY SEVERITY")
        print(f"{'-'*100}")
        for severity, count in sorted(by_severity.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_count) * 100
            print(f"  {severity.upper():.<50} {count:>3} ({percentage:>5.1f}%)")
        print()
        
        print(f"DETAILED COMPLAINT LIST")
        print(f"{'-'*100}")
        for i, complaint in enumerate(quarterly_complaints, 1):
            timestamp = complaint.get('timestamp', 'Unknown')[:19]
            ref_id = complaint.get('reference_id', 'N/A')
            category = complaint.get('category', 'unknown').replace('_', ' ').title()
            complainant = complaint.get('complainant_type', 'unknown').capitalize()
            severity = complaint.get('severity', 'unknown').upper()
            subject = complaint.get('subject', 'No subject')
            
            print(f"\n{i}. [{ref_id}] - {timestamp}")
            print(f"   Category: {category}")
            print(f"   Complainant Type: {complainant}")
            print(f"   Severity: {severity}")
            print(f"   Subject: {subject[:80]}{'...' if len(subject) > 80 else ''}")
        
        print(f"\n{'='*100}")
        print(f"END OF REPORT")
        print(f"{'='*100}\n")
        
        print("CERTIFICATION STATEMENT:")
        print("This report has been prepared in compliance with 45 CFR 170.523 (n)")
        print("which requires submission of complaint information to the National Coordinator")
        print("on a quarterly basis each calendar year.\n")
        
        # Save report to file
        report_filename = f"onc_complaint_report_{year}_Q{quarter}.txt"
        try:
            # Create reports directory if it doesn't exist
            reports_dir = os.path.join(os.path.dirname(self.complaints_file), 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            report_path = os.path.join(reports_dir, report_filename)
            
            # Redirect stdout to file
            with open(report_path, 'w', encoding='utf-8') as f:
                original_stdout = sys.stdout
                sys.stdout = f
                # Re-run the report generation to write to file
                self.generate_quarterly_report(year, quarter)
                sys.stdout = original_stdout
            
            print(f"Report saved to: {report_path}")
        except Exception as e:
            print(f"Warning: Could not save report to file: {e}")
    
    def export_to_csv(self, output_file):
        """Export all complaints to CSV format"""
        import csv
        
        if not self.complaints:
            print("No complaints to export.")
            return
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'reference_id', 'timestamp', 'complainant_type', 'category',
                    'severity', 'subject', 'description', 'contact_email'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for complaint in self.complaints:
                    row = {k: complaint.get(k, '') for k in fieldnames}
                    writer.writerow(row)
            
            print(f"Successfully exported {len(self.complaints)} complaints to: {output_file}")
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='ONC Complaint Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python complaint_manager.py list
  python complaint_manager.py list --category safety --severity critical
  python complaint_manager.py report 2025 4
  python complaint_manager.py export complaints_export.csv
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all complaints')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--severity', help='Filter by severity')
    list_parser.add_argument('--start-date', help='Filter by start date (YYYY-MM-DD)')
    list_parser.add_argument('--end-date', help='Filter by end date (YYYY-MM-DD)')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate quarterly ONC report')
    report_parser.add_argument('year', type=int, help='Year (e.g., 2025)')
    report_parser.add_argument('quarter', type=int, choices=[1, 2, 3, 4], help='Quarter (1-4)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export complaints to CSV')
    export_parser.add_argument('output_file', help='Output CSV file path')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Initialize manager
    manager = ComplaintManager()
    
    # Execute command
    if args.command == 'list':
        manager.list_complaints(
            category=args.category,
            severity=args.severity,
            start_date=args.start_date,
            end_date=args.end_date
        )
    elif args.command == 'report':
        manager.generate_quarterly_report(args.year, args.quarter)
    elif args.command == 'export':
        manager.export_to_csv(args.output_file)


if __name__ == '__main__':
    main()

