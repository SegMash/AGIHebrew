#!/usr/bin/env python3
"""
Detect broken CSV lines caused by newlines in message text
Reports room and message numbers where line breaks occur within quoted text
"""

import argparse
import csv
import os
import sys

def detect_broken_csv_lines(csv_file_path):
    """Detect and report broken CSV lines caused by newlines in messages"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ Error: CSV file '{csv_file_path}' not found")
        return False
    
    print(f"🔍 Checking CSV file: {csv_file_path}")
    print("=" * 50)
    
    issues_found = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check if first line is header
        first_line = lines[0].strip() if lines else ""
        has_header = first_line.lower().startswith('room,') or first_line.startswith('חדר,')
        start_line = 1 if has_header else 0
        
        if has_header:
            print(f"📋 Header detected: {first_line}")
            print()
        
        i = start_line
        while i < len(lines):
            line = lines[i].strip()
            line_num = i + 1
            
            if not line:  # Skip empty lines
                i += 1
                continue
            
            # Try to parse as CSV
            try:
                # Use csv.reader to properly handle quoted fields
                reader = csv.reader([line])
                row = next(reader)
                
                # Check if we have the expected number of columns (at least 4: room, idx, original, translation)
                if len(row) < 4:
                    # This might be a broken line - try to get room/message info from previous complete line
                    room_info = "Unknown"
                    msg_info = "Unknown"
                    
                    # Look backwards for the last complete line to get context
                    for j in range(i - 1, max(start_line - 1, -1), -1):
                        try:
                            prev_line = lines[j].strip()
                            if prev_line:
                                prev_reader = csv.reader([prev_line])
                                prev_row = next(prev_reader)
                                if len(prev_row) >= 4:
                                    try:
                                        room_info = f"Room {int(float(prev_row[0]))}"
                                        msg_info = f"Message {int(float(prev_row[1]))}"
                                        break
                                    except ValueError:
                                        continue
                        except:
                            continue
                    
                    issues_found += 1
                    print(f"⚠️  Line {line_num}: Incomplete row - only {len(row)} columns")
                    print(f"   Context: {room_info}, {msg_info} (from previous complete line)")
                    print(f"   Content: {line[:100]}{'...' if len(line) > 100 else ''}")
                    
                    # Try to find the continuation
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        print(f"   Next line ({line_num + 1}): {next_line[:100]}{'...' if len(next_line) > 100 else ''}")
                    print()
                
                elif len(row) >= 4:
                    # We have a complete row, check if room and idx are valid numbers
                    try:
                        room = int(float(row[0]))
                        idx = int(float(row[1]))
                        
                        # Check if the original or translation contains unescaped newlines
                        original = row[2] if len(row) > 2 else ""
                        translation = row[3] if len(row) > 3 else ""
                        
                        if '\n' in original or '\n' in translation:
                            issues_found += 1
                            print(f"⚠️  Line {line_num}: Room {room}, Message {idx} - Contains embedded newlines")
                            if '\n' in original:
                                print(f"   Original text has newlines: {repr(original[:100])}")
                            if '\n' in translation:
                                print(f"   Translation has newlines: {repr(translation[:100])}")
                            print()
                        
                    except (ValueError, IndexError):
                        # Room or idx is not a valid number
                        issues_found += 1
                        print(f"⚠️  Line {line_num}: Invalid room/message number format")
                        print(f"   Room: '{row[0]}', Index: '{row[1] if len(row) > 1 else 'N/A'}'")
                        print(f"   Content: {line[:100]}{'...' if len(line) > 100 else ''}")
                        print()
                
            except csv.Error as e:
                # CSV parsing error - likely due to broken quotes or newlines
                issues_found += 1
                print(f"❌ Line {line_num}: CSV parsing error - {e}")
                print(f"   Content: {line[:100]}{'...' if len(line) > 100 else ''}")
                
                # Check if this looks like a continuation line (starts with quote and comma)
                if line.startswith('",') or line.startswith('"') and ',' in line:
                    print(f"   ⚠️  This looks like a continuation of a broken message from previous line")
                
                # Try to extract room/message info if possible
                if i > start_line:
                    prev_line = lines[i - 1].strip()
                    try:
                        prev_reader = csv.reader([prev_line])
                        prev_row = next(prev_reader)
                        if len(prev_row) >= 2:
                            try:
                                room = int(float(prev_row[0]))
                                idx = int(float(prev_row[1]))
                                print(f"   ⚠️  Likely continuation of Room {room}, Message {idx}")
                            except ValueError:
                                pass
                    except:
                        pass
                
                print()
            
            i += 1
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    print("=" * 50)
    if issues_found == 0:
        print("✅ No issues found! CSV file appears to be properly formatted.")
    else:
        print(f"⚠️  Found {issues_found} potential issues in the CSV file.")
        print()
        print("💡 Common fixes:")
        print("   1. Check Google Sheets - ensure no manual line breaks in cells")
        print("   2. Re-download from Google Drive using the download script")
        print("   3. Manually fix quoted text that spans multiple lines")
    
    return issues_found == 0

def main():
    parser = argparse.ArgumentParser(
        description='Detect broken CSV lines caused by newlines in message text'
    )
    parser.add_argument('csv_file', help='Path to the CSV file to check')
    
    args = parser.parse_args()
    
    success = detect_broken_csv_lines(args.csv_file)
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
