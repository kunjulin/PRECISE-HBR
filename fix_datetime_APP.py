#!/usr/bin/env python3
"""Script to fix datetime import issues in APP.py"""

import re

def fix_datetime_references():
    with open('APP.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix datetime.timedelta references
    content = re.sub(r'datetime\.timedelta', 'dt_module.timedelta', content)
    
    # Fix any remaining datetime.datetime references
    content = re.sub(r'datetime\.datetime', 'dt_module.datetime', content)
    
    # Fix datetime.date references (but not dt_module.date)
    content = re.sub(r'(?<!dt_module\.)datetime\.date', 'dt_module.date', content)
    
    with open('APP.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed datetime references in APP.py")

if __name__ == '__main__':
    fix_datetime_references() 