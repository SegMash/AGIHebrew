import os
import re
import argparse
from pathlib import Path

import config


def contains_english_letters(text):
    """
    Check if text contains English letters (a-z, A-Z)
    Ignore English letters that come immediately after % sign (format specifiers)
    """
    # Remove all %[letter] patterns first
    import re
    text_without_format = re.sub(r'%[a-zA-Z]', '', text)
    
    # Now check if there are any remaining English letters
    return bool(re.search(r'[a-zA-Z]', text_without_format))


def contains_hebrew_letters(text):
    """
    Check if text contains Hebrew letters (Windows-1255 encoding)
    Hebrew letters range: א-ת (Unicode U+05D0 to U+05EA)
    """
    # Hebrew letter ranges in Unicode
    hebrew_pattern = r'[\u05D0-\u05EA\u05F0-\u05F4]'
    return bool(re.search(hebrew_pattern, text))


def find_quoted_strings_with_english(file_path):
    """
    Find all quoted strings in a file that contain English letters.
    Handles escaped quotes properly.
    Ignores strings inside said() method calls.
    Ignores configuration file names.
    """
    try:
        with open(file_path, 'r', encoding=config.encoding) as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []
    
    # Configuration file names to ignore
    config_files = {'resourceids.txt', 'reserved.txt', 'globals.txt'}
    
    # Pattern to match quoted strings, handling escaped quotes
    # This matches: "any text including \" escaped quotes"
    pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
    
    matches = []
    for match in re.finditer(pattern, content):
        quoted_text = match.group(1)  # The text inside quotes (without the quotes)
        full_match = match.group(0)   # The full match including quotes
        
        # Skip configuration file names
        if quoted_text in config_files:
            continue
        
        # Skip strings that contain Hebrew letters (already translated)
        if contains_hebrew_letters(quoted_text):
            continue
        
        # Check if this string contains English letters
        if contains_english_letters(quoted_text):
            # Check if this string is inside a said() method call
            # Look backwards from the match to see if it's part of said(...)
            before_match = content[:match.start()]
            
            # Find the start of the current line
            last_newline = before_match.rfind('\n')
            current_line_start = last_newline + 1 if last_newline != -1 else 0
            current_line = content[current_line_start:content.find('\n', match.end())]
            
            # Check if this line contains said(), get(), or drop() and the quoted string is within it
            skip_line = False
            for method in ['said(', 'get(', 'drop(']:
                if method in current_line:
                    # More precise check: see if the quote is within method(...)
                    method_pattern = method.replace('(', r'\s*\(')  # Allow spaces before parentheses
                    method_match = re.search(f'{method_pattern}[^)]*\\)', current_line)
                    if method_match:
                        # Check if our quote is within the method parentheses
                        method_start = current_line_start + method_match.start()
                        method_end = current_line_start + method_match.end()
                        if method_start <= match.start() <= method_end:
                            skip_line = True
                            break
            
            if skip_line:
                continue  # Skip this match as it's inside said(), get(), or drop()
            
            # Find line number for better reporting
            line_num = content[:match.start()].count('\n') + 1
            
            matches.append({
                'line_number': line_num,
                'full_text': full_match,
                'inner_text': quoted_text,
                'position': match.start()
            })
    
    return matches


def scan_directory(src_dir, pattern='*.lgc'):
    """Scan all .lgc files in directory for English strings"""
    src_path = Path(src_dir)
    
    if not src_path.exists():
        print(f"Directory {src_dir} does not exist!")
        return
    
    # Find all .lgc files
    lgc_files = list(src_path.glob(pattern))
    
    if not lgc_files:
        print(f"No files matching {pattern} found in {src_dir}")
        return
    
    total_english_strings = 0
    files_with_english = 0
    
    print(f"Scanning {len(lgc_files)} files for English strings...\n")
    print("=" * 80)
    
    for lgc_file in sorted(lgc_files):
        english_strings = find_quoted_strings_with_english(lgc_file)
        
        if english_strings:
            files_with_english += 1
            total_english_strings += len(english_strings)
            
            print(f"\nFile: {lgc_file.name}")
            print("-" * 50)
            
            for i, string_info in enumerate(english_strings, 1):
                print(f"{i:2d}. Line {string_info['line_number']:3d}: {string_info['full_text']}")
                
                # If the string is very long, show truncated version
                if len(string_info['inner_text']) > 60:
                    truncated = string_info['inner_text'][:57] + "..."
                    print(f"     Content: {truncated}")
                else:
                    print(f"     Content: {string_info['inner_text']}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY:")
    print(f"Files scanned: {len(lgc_files)}")
    print(f"Files with English strings: {files_with_english}")
    print(f"Total English strings found: {total_english_strings}")
    
    if total_english_strings == 0:
        print("🎉 No English strings found! All text appears to be properly converted.")
    elif total_english_strings > 0:
        print(f"⚠️  Found {total_english_strings} English strings that may need conversion to message indices.")


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Scan Logic files for quoted strings containing English letters',
        epilog='''
This script helps identify English text that still needs to be replaced with message indices.
It finds all quoted strings (handling escaped quotes) that contain English letters.
        '''
    )
    parser.add_argument("srcdir", help="Source directory containing Logic files")
    parser.add_argument("--pattern", default='*.lgc', help="File pattern to scan")
    parser.add_argument("--output", help="Optional output file to save the report")
    
    args = parser.parse_args()
    
    if args.output:
        # Redirect output to file
        import sys
        with open(args.output, 'w', encoding='utf-8') as f:
            sys.stdout = f
            scan_directory(args.srcdir, args.pattern)
            sys.stdout = sys.__stdout__
        print(f"Report saved to {args.output}")
    else:
        scan_directory(args.srcdir, args.pattern)


if __name__ == "__main__":
    main()
