#!/usr/bin/env python3
"""
Script to scan messages.csv file and find lines with more than 4 commas.
This helps identify malformed CSV entries that might have unescaped commas
in the text fields.
"""

import argparse
import os
import sys


def check_csv_commas(csv_file, max_commas=4):
    """
    Scan CSV file and find lines with more than the expected number of commas.
    Only counts commas that are outside of quoted strings.
    
    Args:
        csv_file: Path to the CSV file to check
        max_commas: Maximum expected number of commas (default 4 for 5 fields)
    
    Returns:
        List of problematic lines with their line numbers
    """
    problems = []
    
    def count_field_separators(line):
        """Count commas that are actual field separators (outside quotes)"""
        comma_count = 0
        in_quotes = False
        i = 0
        
        while i < len(line):
            char = line[i]
            
            if char == '"':
                # Check if this is an escaped quote
                if i + 1 < len(line) and line[i + 1] == '"':
                    # Skip escaped quote
                    i += 1
                else:
                    # Toggle quote state
                    in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                # This is a field separator comma
                comma_count += 1
                
            i += 1
            
        return comma_count
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n\r')
                if not line.strip():  # Skip empty lines
                    continue
                    
                comma_count = count_field_separators(line)
                if comma_count > max_commas:
                    problems.append({
                        'line_num': line_num,
                        'comma_count': comma_count,
                        'line': line
                    })
                    
    except UnicodeDecodeError:
        # Try with Windows-1255 encoding if UTF-8 fails
        try:
            with open(csv_file, 'r', encoding='windows-1255') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.rstrip('\n\r')
                    if not line.strip():  # Skip empty lines
                        continue
                        
                    comma_count = line.count(',')
                    if comma_count > max_commas:
                        problems.append({
                            'line_num': line_num,
                            'comma_count': comma_count,
                            'line': line
                        })
        except Exception as e:
            print(f"Error reading file with Windows-1255 encoding: {e}")
            return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    
    return problems


def main():
    parser = argparse.ArgumentParser(
        description='Scan CSV file for lines with too many commas',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('csv_file', help='Path to the CSV file to check')
    parser.add_argument('--max-commas', type=int, default=4, 
                       help='Maximum expected number of commas per line')
    parser.add_argument('--show-context', action='store_true',
                       help='Show surrounding lines for context')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: File '{args.csv_file}' not found.")
        sys.exit(1)
    
    print(f"Checking '{args.csv_file}' for lines with more than {args.max_commas} commas...")
    print("-" * 60)
    
    problems = check_csv_commas(args.csv_file, args.max_commas)
    
    if not problems:
        print("✓ No lines found with excessive commas.")
        return
    
    print(f"Found {len(problems)} problematic line(s):")
    print()
    
    for problem in problems:
        print(f"Line {problem['line_num']}: {problem['comma_count']} commas")
        print(f"Content: {problem['line']}")
        
        # Show which parts might be the issue
        parts = problem['line'].split(',')
        print(f"Fields ({len(parts)}):")
        for i, part in enumerate(parts):
            print(f"  [{i}]: {part}")
        print("-" * 40)
    
    # Show summary
    print(f"\nSummary: {len(problems)} lines with more than {args.max_commas} commas")
    print("This usually indicates unescaped commas in text fields.")
    print("Consider wrapping text fields in quotes or escaping commas.")


if __name__ == '__main__':
    main()
