#!/usr/bin/env python3
"""
Script to verify that Hebrew translations are not longer than their corresponding English lines.
Compares two text files with format: index|text
"""

import argparse
import sys
from pathlib import Path


def load_file_data(file_path):
    """Load file data into a dictionary with index as key and text as value."""
    data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                if '|' not in line:
                    print(f"Warning: Line {line_num} in {file_path} has no '|' separator: {line}")
                    continue
                
                parts = line.split('|', 1)
                if len(parts) != 2:
                    print(f"Warning: Line {line_num} in {file_path} malformed: {line}")
                    continue
                
                try:
                    index = int(parts[0])
                    text = parts[1]
                    data[index] = text
                except ValueError:
                    print(f"Warning: Line {line_num} in {file_path} has invalid index: {parts[0]}")
                    continue
                    
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit(1)
    
    return data


def verify_translation_lengths(english_file, hebrew_file, output_file=None):
    """
    Verify that Hebrew translations are not longer than English text.
    
    Args:
        english_file: Path to English text file
        hebrew_file: Path to Hebrew text file  
        output_file: Optional path to write results to
    
    Returns:
        List of violations (index, eng_len, heb_len, eng_text, heb_text)
    """
    print(f"Loading English file: {english_file}")
    english_data = load_file_data(english_file)
    
    print(f"Loading Hebrew file: {hebrew_file}")
    hebrew_data = load_file_data(hebrew_file)
    
    print(f"English entries: {len(english_data)}")
    print(f"Hebrew entries: {len(hebrew_data)}")
    
    violations = []
    
    # Check all English entries for corresponding Hebrew translations
    for index in sorted(english_data.keys()):
        english_text = english_data[index]
        english_len = len(english_text)
        
        if index not in hebrew_data:
            print(f"Warning: Missing Hebrew translation for index {index}")
            continue
            
        hebrew_text = hebrew_data[index]
        hebrew_len = len(hebrew_text)
        if hebrew_len > english_len:
            violations.append((index, english_len, hebrew_len, english_text, hebrew_text))
    
    # Check for Hebrew entries without English counterpart
    for index in sorted(hebrew_data.keys()):
        if index not in english_data:
            print(f"Warning: Hebrew entry {index} has no English counterpart")
    
    # Output results
    output_lines = []
    
    if violations:
        output_lines.append(f"Found {len(violations)} length violations:")
        output_lines.append("-" * 60)
        
        for index, eng_len, heb_len, eng_text, heb_text in violations:
            output_lines.append(f"Index {index}: Hebrew longer by {heb_len - eng_len} characters")
            output_lines.append(f"  English ({eng_len}): {eng_text}")
            output_lines.append(f"  Hebrew  ({heb_len}): {heb_text}")
            output_lines.append("-" * 40)
    else:
        output_lines.append("✓ All Hebrew translations are within length limits!")
    
    # Print to console
    for line in output_lines:
        print(line)
    
    # Write to output file if specified
    if output_file:
        output_path = Path(output_file)
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for line in output_lines:
                    f.write(line + '\n')
            print(f"\nResults written to: {output_path}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
    
    return violations


def main():
    parser = argparse.ArgumentParser(
        description='Verify Hebrew translations are not longer than English text',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('english_file', help='Path to English text file')
    parser.add_argument('hebrew_file', help='Path to Hebrew text file')
    parser.add_argument('--output', '-o', help='Output file for results')
    parser.add_argument('--max-violations', type=int, default=0,
                       help='Maximum allowed violations (0 = strict)')
    
    args = parser.parse_args()
    
    violations = verify_translation_lengths(args.english_file, args.hebrew_file, args.output)
    
    if len(violations) > args.max_violations:
        print(f"\nFAILED: {len(violations)} violations exceed limit of {args.max_violations}")
        sys.exit(1)
    else:
        print(f"\nPASSED: {len(violations)} violations within limit of {args.max_violations}")
        sys.exit(0)


if __name__ == '__main__':
    main()
