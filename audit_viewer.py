#!/usr/bin/env python3
"""
ONC Compliance: 45 CFR 170.315 (d)(3) - Audit Report(s)

This tool provides functionality to create audit reports from the audit log,
allowing users to review, filter, sort, and export audit events.

Usage:
    python audit_viewer.py list                              # List recent audit events
    python audit_viewer.py list --user user123 --limit 50    # Filter by user
    python audit_viewer.py report 2025-01-01 2025-01-31      # Generate date range report
    python audit_viewer.py verify                            # Verify log integrity
    python audit_viewer.py export audit_report.csv           # Export to CSV
"""

import json
import os
import sys
import datetime
import argparse
from collections import defaultdict, Counter
from typing import List, Dict, Optional
import csv


class AuditViewer:
    """Tool for viewing and analyzing audit logs"""
    
    def __init__(self, audit_file='instance/audit/audit_log.jsonl'):
        self.audit_file = audit_file
        self.entries = []
        self.load_audit_log()
    
    def load_audit_log(self):
        """Load all audit log entries"""
        if not os.path.exists(self.audit_file):
            print(f"Audit log file not found: {self.audit_file}")
            print("No audit events have been logged yet.")
            return
        
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        # Skip the header entry
                        if entry.get('log_type') != 'AUDIT_LOG_HEADER':
                            self.entries.append(entry)
            
            print(f"Loaded {len(self.entries)} audit event(s)")
        except Exception as e:
            print(f"Error loading audit log: {e}")
            sys.exit(1)
    
    def list_events(self,
                   user_id: Optional[str] = None,
                   patient_id: Optional[str] = None,
                   event_type: Optional[str] = None,
                   action: Optional[str] = None,
                   outcome: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   limit: int = 20):
        """
        List audit events with optional filters.
        
        Args:
            user_id: Filter by user ID
            patient_id: Filter by patient ID
            event_type: Filter by event type (e.g., 'ePHI_ACCESS', 'AUTHENTICATION')
            action: Filter by specific action
            outcome: Filter by outcome ('success' or 'failure')
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            limit: Maximum number of events to display
        """
        filtered = self.entries
        
        # Apply filters
        if user_id:
            filtered = [e for e in filtered if e.get('user_id') == user_id]
        if patient_id:
            filtered = [e for e in filtered if e.get('patient_id') == patient_id]
        if event_type:
            filtered = [e for e in filtered if e.get('event_type') == event_type]
        if action:
            filtered = [e for e in filtered if e.get('action') == action]
        if outcome:
            filtered = [e for e in filtered if e.get('outcome') == outcome]
        if start_date:
            filtered = [e for e in filtered if e.get('timestamp', '') >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.get('timestamp', '') <= end_date]
        
        # Sort by timestamp (most recent first)
        filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply limit
        filtered = filtered[:limit]
        
        if not filtered:
            print("No audit events match the specified filters.")
            return
        
        print(f"\n{'='*120}")
        print(f"AUDIT LOG ({len(filtered)} events shown, {len(self.entries)} total)")
        print(f"{'='*120}\n")
        
        for i, entry in enumerate(filtered, 1):
            timestamp = entry.get('timestamp', 'Unknown')[:19].replace('T', ' ')
            event_type = entry.get('event_type', 'UNKNOWN')
            action = entry.get('action', 'unknown')
            user = entry.get('user_id', 'unknown')[:20]
            patient = entry.get('patient_id', 'N/A')[:20]
            outcome = entry.get('outcome', 'unknown').upper()
            ip = entry.get('ip_address', 'unknown')
            
            outcome_symbol = '✓' if outcome == 'SUCCESS' else '✗'
            outcome_color = '\033[92m' if outcome == 'SUCCESS' else '\033[91m'  # Green or Red
            reset_color = '\033[0m'
            
            print(f"{i}. [{timestamp}] {outcome_color}{outcome_symbol} {outcome}{reset_color}")
            print(f"   Event: {event_type} - {action}")
            print(f"   User: {user} | Patient: {patient} | IP: {ip}")
            
            # Show additional details if present
            details = entry.get('details', {})
            if details:
                detail_str = ', '.join([f"{k}={v}" for k, v in list(details.items())[:3]])
                if detail_str:
                    print(f"   Details: {detail_str}")
            
            print(f"   {'-'*115}\n")
    
    def generate_report(self, start_date: str, end_date: str):
        """
        Generate a comprehensive audit report for a date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        # Filter events by date range
        filtered = [
            e for e in self.entries
            if start_date <= e.get('timestamp', '')[:10] <= end_date
        ]
        
        if not filtered:
            print(f"No audit events found between {start_date} and {end_date}")
            return
        
        # Statistics
        total_events = len(filtered)
        success_events = len([e for e in filtered if e.get('outcome') == 'success'])
        failure_events = total_events - success_events
        
        # Count by event type
        events_by_type = Counter([e.get('event_type', 'UNKNOWN') for e in filtered])
        
        # Count by action
        events_by_action = Counter([e.get('action', 'unknown') for e in filtered])
        
        # Count by user
        events_by_user = Counter([e.get('user_id', 'unknown') for e in filtered])
        
        # Count by patient
        patient_accesses = Counter([e.get('patient_id') for e in filtered if e.get('patient_id')])
        
        # Identify failures
        failures = [e for e in filtered if e.get('outcome') == 'failure']
        
        # Generate report
        print(f"\n{'='*120}")
        print(f"AUDIT REPORT")
        print(f"Application: SMART on FHIR PRECISE-HBR Calculator")
        print(f"Reporting Period: {start_date} to {end_date}")
        print(f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Compliance Standard: 45 CFR 170.315 (d)(2) & (d)(3)")
        print(f"{'='*120}\n")
        
        print(f"SUMMARY")
        print(f"{'-'*120}")
        print(f"Total Audit Events: {total_events}")
        print(f"Successful Events: {success_events} ({success_events/total_events*100:.1f}%)")
        print(f"Failed Events: {failure_events} ({failure_events/total_events*100:.1f}%)")
        print(f"Unique Users: {len(events_by_user)}")
        print(f"Unique Patients Accessed: {len(patient_accesses)}\n")
        
        print(f"EVENTS BY TYPE")
        print(f"{'-'*120}")
        for event_type, count in events_by_type.most_common():
            percentage = (count / total_events) * 100
            print(f"  {event_type:.<50} {count:>5} ({percentage:>5.1f}%)")
        print()
        
        print(f"TOP 10 ACTIONS")
        print(f"{'-'*120}")
        for action, count in events_by_action.most_common(10):
            percentage = (count / total_events) * 100
            print(f"  {action:.<50} {count:>5} ({percentage:>5.1f}%)")
        print()
        
        print(f"TOP 10 USERS")
        print(f"{'-'*120}")
        for user, count in events_by_user.most_common(10):
            percentage = (count / total_events) * 100
            print(f"  {user:.<50} {count:>5} ({percentage:>5.1f}%)")
        print()
        
        if patient_accesses:
            print(f"TOP 10 PATIENT ACCESSES")
            print(f"{'-'*120}")
            for patient, count in patient_accesses.most_common(10):
                print(f"  {patient:.<50} {count:>5} accesses")
            print()
        
        if failures:
            print(f"FAILURE EVENTS ({len(failures)} total)")
            print(f"{'-'*120}")
            for i, failure in enumerate(failures[:20], 1):  # Show first 20 failures
                timestamp = failure.get('timestamp', 'Unknown')[:19].replace('T', ' ')
                event_type = failure.get('event_type', 'UNKNOWN')
                action = failure.get('action', 'unknown')
                user = failure.get('user_id', 'unknown')
                details = failure.get('details', {})
                error = details.get('error', 'No error details')
                
                print(f"\n{i}. [{timestamp}] {event_type} - {action}")
                print(f"   User: {user}")
                print(f"   Error: {error}")
            
            if len(failures) > 20:
                print(f"\n   ... and {len(failures) - 20} more failures")
            print()
        
        print(f"{'='*120}")
        print(f"END OF REPORT")
        print(f"{'='*120}\n")
        
        # Save report to file
        report_filename = f"audit_report_{start_date}_to_{end_date}.txt"
        report_dir = os.path.join(os.path.dirname(self.audit_file), 'reports')
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, report_filename)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                # Redirect output to file (simplified version without colors)
                f.write(f"AUDIT REPORT\n")
                f.write(f"Application: SMART on FHIR PRECISE-HBR Calculator\n")
                f.write(f"Reporting Period: {start_date} to {end_date}\n")
                f.write(f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"\nTotal Events: {total_events}\n")
                f.write(f"Successful: {success_events}\n")
                f.write(f"Failed: {failure_events}\n")
                # Add more details as needed
            
            print(f"Report saved to: {report_path}")
        except Exception as e:
            print(f"Warning: Could not save report to file: {e}")
    
    def verify_integrity(self):
        """Verify the integrity of the audit log chain"""
        print("Verifying audit log integrity...")
        
        if not os.path.exists(self.audit_file):
            print("ERROR: Audit log file does not exist.")
            return False
        
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                print("ERROR: Audit log is empty.")
                return False
            
            previous_hash = None
            valid_entries = 0
            
            for line_num, line in enumerate(lines, 1):
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    print(f"ERROR: Invalid JSON at line {line_num}")
                    return False
                
                # Verify hash chain
                if entry.get('previous_hash') != previous_hash:
                    print(f"ERROR: Hash chain broken at line {line_num}")
                    print(f"  Expected previous_hash: {previous_hash}")
                    print(f"  Got: {entry.get('previous_hash')}")
                    return False
                
                # Verify entry hash
                stored_hash = entry.get('entry_hash')
                # Recalculate hash (simplified version)
                import hashlib
                data_to_hash = {k: v for k, v in entry.items() if k != 'entry_hash'}
                json_str = json.dumps(data_to_hash, sort_keys=True, ensure_ascii=False)
                calculated_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
                
                if stored_hash != calculated_hash:
                    print(f"ERROR: Entry hash mismatch at line {line_num}")
                    print(f"  Stored: {stored_hash}")
                    print(f"  Calculated: {calculated_hash}")
                    return False
                
                previous_hash = stored_hash
                valid_entries += 1
            
            print(f"✓ Audit log integrity verified successfully!")
            print(f"✓ Verified {valid_entries} entries")
            print(f"✓ Hash chain is intact")
            print(f"✓ No tampering detected")
            return True
            
        except Exception as e:
            print(f"ERROR: Verification failed: {str(e)}")
            return False
    
    def export_to_csv(self, output_file: str):
        """Export audit log to CSV format"""
        if not self.entries:
            print("No audit events to export.")
            return
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'timestamp', 'event_type', 'action', 'user_id', 'patient_id',
                    'resource_type', 'outcome', 'ip_address', 'details'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for entry in self.entries:
                    row = {k: entry.get(k, '') for k in fieldnames}
                    # Convert details dict to string
                    row['details'] = json.dumps(entry.get('details', {}))
                    writer.writerow(row)
            
            print(f"Successfully exported {len(self.entries)} audit events to: {output_file}")
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Audit Log Viewer and Reporter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python audit_viewer.py list
  python audit_viewer.py list --user user123 --event-type ePHI_ACCESS
  python audit_viewer.py report 2025-01-01 2025-12-31
  python audit_viewer.py verify
  python audit_viewer.py export audit_log_export.csv
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List audit events')
    list_parser.add_argument('--user', help='Filter by user ID')
    list_parser.add_argument('--patient', help='Filter by patient ID')
    list_parser.add_argument('--event-type', help='Filter by event type')
    list_parser.add_argument('--action', help='Filter by action')
    list_parser.add_argument('--outcome', choices=['success', 'failure'], help='Filter by outcome')
    list_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    list_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    list_parser.add_argument('--limit', type=int, default=20, help='Maximum events to show')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate audit report')
    report_parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
    report_parser.add_argument('end_date', help='End date (YYYY-MM-DD)')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify log integrity')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export to CSV')
    export_parser.add_argument('output_file', help='Output CSV file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Initialize viewer
    viewer = AuditViewer()
    
    # Execute command
    if args.command == 'list':
        viewer.list_events(
            user_id=args.user,
            patient_id=args.patient,
            event_type=args.event_type,
            action=args.action,
            outcome=args.outcome,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit
        )
    elif args.command == 'report':
        viewer.generate_report(args.start_date, args.end_date)
    elif args.command == 'verify':
        success = viewer.verify_integrity()
        sys.exit(0 if success else 1)
    elif args.command == 'export':
        viewer.export_to_csv(args.output_file)


if __name__ == '__main__':
    main()

