#!/usr/bin/env python3
"""
Script to fix CSV quoting issues in messages.csv files.
Ensures that Hebrew translations containing commas are properly quoted.

Usage: python fix_csv_quotes.py <input_csv_file> [output_csv_file]
If no output file is specified, the input file will be updated in place.
"""

import sys
import os
import re
from pathlib import Path


def needs_quotes(text):
    """Check if text needs to be quoted (contains comma, quote, or newline)"""
    return ',' in text or '"' in text or '\n' in text


def escape_quotes_in_text(text):
    """Escape existing quotes in text by doubling them"""
    return text.replace('"', '""')


def parse_csv_line(line):
    """
    Parse a CSV line with 4 columns: logic_id, message_id, english_text, hebrew_text, empty_column
    Returns tuple of (logic_id, message_id, english_text, hebrew_text, empty_column)
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
    
    # Ensure we have exactly 5 parts (pad with empty strings if needed)
    while len(parts) < 5:
        parts.append("")
    
    return parts[:5]  # Return only first 5 parts


def format_csv_field(text):
    """Format a field for CSV output, adding quotes if necessary"""
    if not text:
        return ""
    
    if needs_quotes(text):
        escaped_text = escape_quotes_in_text(text)
        return f'"{escaped_text}"'
    else:
        return text


def fix_csv_file(input_file, output_file=None):
    """Fix CSV quoting issues in the given file"""
    if output_file is None:
        output_file = input_file
    
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open(input_file, 'r', encoding='cp1255') as f:
            lines = f.readlines()
    
    fixed_lines = []
    issues_found = 0
    
    for line_num, line in enumerate(lines, 1):
        line = line.rstrip('\n\r')
        if not line.strip():
            fixed_lines.append(line)
            continue
        
        # Ensure line ends with comma for empty 5th column
        if not line.endswith(','):
            line = line + ','
        
        try:
            # Find the positions of the first 3 commas to locate English and Hebrew sections
            comma_positions = []
            in_quotes = False
            for i, char in enumerate(line):
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    comma_positions.append(i)
                    if len(comma_positions) == 3:
                        break
            
            if len(comma_positions) < 3:
                # Not enough commas, keep original line
                fixed_lines.append(line)
                continue
            
            # Extract parts while preserving original English formatting
            logic_part = line[:comma_positions[0]]
            message_part = line[comma_positions[0]+1:comma_positions[1]]
            english_part = line[comma_positions[1]+1:comma_positions[2]]  # Keep exactly as-is
            
            # Find Hebrew part - from after 3rd comma to last comma
            hebrew_start = comma_positions[2] + 1
            # Find the last comma (before empty 5th column)
            last_comma_pos = line.rfind(',')
            hebrew_part = line[hebrew_start:last_comma_pos]
            empty_part = line[last_comma_pos+1:] if last_comma_pos != -1 else ""
            
            # Check if Hebrew text needs fixing
            hebrew_needs_quotes = needs_quotes(hebrew_part)
            hebrew_is_quoted = hebrew_part.startswith('"') and hebrew_part.endswith('"')
            
            # Fix Hebrew part if needed
            if hebrew_needs_quotes and not hebrew_is_quoted:
                issues_found += 1
                print(f"Line {line_num}: Fixed Hebrew text with comma: {hebrew_part[:50]}...")
                hebrew_part = format_csv_field(hebrew_part)
            
            # Reconstruct the line preserving original English formatting
            fixed_line = f"{logic_part},{message_part},{english_part},{hebrew_part},{empty_part}"
            fixed_lines.append(fixed_line)
            
        except Exception as e:
            print(f"Warning: Could not parse line {line_num}: {e}")
            print(f"Line content: {line}")
            fixed_lines.append(line)  # Keep original line if parsing fails
    
    # Write the fixed file
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in fixed_lines:
            f.write(line + '\n')
    
    print(f"Fixed {issues_found} lines with quoting issues")
    print(f"Output written to: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_csv_quotes.py <input_csv_file> [output_csv_file]")
        print("If no output file is specified, the input file will be updated in place.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist")
        sys.exit(1)
    
    print(f"Processing: {input_file}")
    if output_file:
        print(f"Output will be saved to: {output_file}")
    else:
        print("File will be updated in place")
    
    fix_csv_file(input_file, output_file)
    print("Done!")


if __name__ == "__main__":
    main()
