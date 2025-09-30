#!/usr/bin/env python3
"""
Script to extract Hebrew messages from messages.csv file to a simple text file.
This is useful for proofreading, spell checking, or reviewing translations.

Usage: python extract_hebrew_messages.py <input_csv_file> [output_text_file]
If no output file is specified, it will create a file with '_hebrew_only.txt' suffix.
"""

import sys
import os
import re
from pathlib import Path


def parse_csv_line(line):
    """
    Parse a CSV line with 4 columns: logic_id, message_id, english_text, hebrew_text, empty_column
    Returns the Hebrew text (4th column)
    """
    parts = []
    current_part = ""
    in_quotes = False
    i = 0
    
    while i < len(line):
        char = line[i]
        
        if char == '"' and (i == 0 or line[i-1] == ','):
            # Start of quoted field
            in_quotes = True
        elif char == '"' and in_quotes:
            # Check if this is an escaped quote or end of quoted field
            if i + 1 < len(line) and line[i + 1] == '"':
                # Escaped quote
                current_part += '""'
                i += 1  # Skip next quote
            else:
                # End of quoted field
                in_quotes = False
        elif char == ',' and not in_quotes:
            # Field separator
            parts.append(current_part)
            current_part = ""
        else:
            current_part += char
        
        i += 1
    
    # Add the last part
    parts.append(current_part)
    
    # Return Hebrew text (4th column, index 3) if it exists
    if len(parts) > 3:
        hebrew_text = parts[3].strip()
        # Remove outer quotes if present
        if hebrew_text.startswith('"') and hebrew_text.endswith('"'):
            hebrew_text = hebrew_text[1:-1]
            # Unescape internal quotes
            hebrew_text = hebrew_text.replace('""', '"')
        return hebrew_text
    
    return ""


def contains_hebrew(text):
    """Check if text contains Hebrew characters"""
    if not text:
        return False
    
    # Hebrew Unicode range: 0x0590-0x05FF
    hebrew_pattern = re.compile(r'[\u0590-\u05FF]')
    return bool(hebrew_pattern.search(text))


def extract_hebrew_messages(input_file, output_file=None, include_metadata=False, ignore_variables=False):
    """Extract Hebrew messages from CSV file to text file"""
    
    if output_file is None:
        # Create output filename
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_hebrew_only.txt"
    
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open(input_file, 'r', encoding='cp1255') as f:
            lines = f.readlines()
    
    hebrew_messages = []
    total_lines = 0
    hebrew_count = 0
    skipped_variables = 0
    
    for line_num, line in enumerate(lines, 1):
        line = line.rstrip('\n\r')
        if not line.strip():
            continue
        
        total_lines += 1
        
        try:
            hebrew_text = parse_csv_line(line)
            
            if hebrew_text and contains_hebrew(hebrew_text):
                # Check if we should ignore lines with % variables
                if ignore_variables and '%' in hebrew_text:
                    skipped_variables += 1
                    continue
                
                # Replace double quotes with single quotes
                hebrew_text = hebrew_text.replace('""', '"')
                
                hebrew_count += 1
                if include_metadata:
                    # Include line number and original context
                    hebrew_messages.append(f"[Line {line_num}] {hebrew_text}")
                else:
                    hebrew_messages.append(hebrew_text)
            elif hebrew_text:
                # Non-Hebrew text in Hebrew column (might be English or empty)
                if include_metadata:
                    hebrew_messages.append(f"[Line {line_num}] (Non-Hebrew: {hebrew_text})")
                
        except Exception as e:
            print(f"Warning: Could not parse line {line_num}: {e}")
            continue
    
    # Write Hebrew messages to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write Hebrew messages
        for message in hebrew_messages:
            f.write(f"{message}\n")
    
    print(f"Extraction complete!")
    print(f"Total lines processed: {total_lines}")
    print(f"Hebrew messages found: {hebrew_count}")
    if ignore_variables:
        print(f"Messages with variables (%) skipped: {skipped_variables}")
    print(f"Output written to: {output_file}")
    
    return hebrew_count


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_hebrew_messages.py <input_csv_file> [output_text_file]")
        print("Options:")
        print("  -m, --metadata       Include line numbers and metadata in output")
        print("  -i, --ignore-vars    Ignore lines containing % variables")
        print("")
        print("Examples:")
        print("  python extract_hebrew_messages.py output_kq3/messages.csv")
        print("  python extract_hebrew_messages.py output_kq3/messages.csv hebrew_messages.txt")
        print("  python extract_hebrew_messages.py output_kq3/messages.csv -m")
        print("  python extract_hebrew_messages.py output_kq3/messages.csv -i")
        print("  python extract_hebrew_messages.py output_kq3/messages.csv -m -i")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    include_metadata = False
    ignore_variables = False
    
    # Parse arguments
    for arg in sys.argv[2:]:
        if arg in ['-m', '--metadata']:
            include_metadata = True
        elif arg in ['-i', '--ignore-vars']:
            ignore_variables = True
        elif not output_file:
            output_file = arg
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist")
        sys.exit(1)
    
    print(f"Processing: {input_file}")
    if output_file:
        print(f"Output will be saved to: {output_file}")
    else:
        print("Output will be saved with '_hebrew_only.txt' suffix")
    
    if include_metadata:
        print("Including metadata and line numbers in output")
    
    if ignore_variables:
        print("Ignoring lines containing % variables")
    
    extract_hebrew_messages(input_file, output_file, include_metadata, ignore_variables)


if __name__ == "__main__":
    main()
