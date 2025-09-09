#!/usr/bin/env python3
"""
Replace get/drop object names with object indices in logic files
"""

import argparse
import csv
import glob
import os
import re
import sys

def parse_objects_csv(csv_file):
    """Parse CSV file and return mapping of words to numbers"""
    objects = {}
    
    # Try different encodings
    for encoding in ['windows-1255', 'utf-8', 'utf-8-sig']:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                for line_num, row in enumerate(reader, 1):
                    if len(row) < 3:
                        continue
                        
                    # Skip lines that don't start with a number
                    try:
                        number = int(row[0])
                    except ValueError:
                        continue
                    
                    english = row[1].strip().strip('"')
                    hebrew = row[2].strip().strip('"')
                    
                    if english:
                        objects[english] = number
                    if hebrew:
                        objects[hebrew] = number
            break
        except UnicodeDecodeError:
            continue
    
    return objects

def replace_get_drop_statements(file_path, objects, lang):
    """Replace get/drop statements in a logic file"""
    with open(file_path, 'r', encoding='windows-1255') as f:
        content = f.read()
    
    original_content = content
    changes_made = False
    
    # Pattern to match get("word") and drop("word")
    pattern = r'(get|drop)\("([^"]+)"\)'
    
    def replace_function(match):
        nonlocal changes_made
        command = match.group(1)  # get or drop
        word = match.group(2)     # the word inside quotes
        
        if word in objects:
            changes_made = True
            return f'{command}(i{objects[word]})'
        else:
            print(f"❌ Error: Object '{word}' not found in CSV file")
            print(f"   File: {file_path}")
            print(f"   Line contains: {match.group(0)}")
            sys.exit(1)
    
    content = re.sub(pattern, replace_function, content)
    
    if changes_made:
        with open(file_path, 'w', encoding='windows-1255') as f:
            f.write(content)
        return True
    
    return False

def main():
    parser = argparse.ArgumentParser(
        description='Replace get/drop object names with indices in logic files'
    )
    parser.add_argument('srcdir', help='Directory containing logic files (*.lgc)')
    parser.add_argument('csvfile', help='CSV file with object mappings')
    parser.add_argument('--lang', choices=['Hebrew', 'English'], required=True,
                       help='Language to process (Hebrew or English)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csvfile):
        print(f"❌ Error: CSV file '{args.csvfile}' not found")
        sys.exit(1)
    
    if not os.path.exists(args.srcdir):
        print(f"❌ Error: Source directory '{args.srcdir}' not found")
        sys.exit(1)
    
    # Parse objects from CSV
    print(f"📋 Parsing objects from {args.csvfile}...")
    objects = parse_objects_csv(args.csvfile)
    print(f"   Found {len(objects)} object mappings")
    
    # Find all logic files
    logic_files = glob.glob(os.path.join(args.srcdir, "*.lgc"))
    if not logic_files:
        print(f"❌ Error: No .lgc files found in '{args.srcdir}'")
        sys.exit(1)
    
    print(f"🔍 Processing {len(logic_files)} logic files...")
    
    total_files_changed = 0
    
    for logic_file in sorted(logic_files):
        try:
            if replace_get_drop_statements(logic_file, objects, args.lang):
                print(f"   ✅ Updated: {os.path.basename(logic_file)}")
                total_files_changed += 1
            else:
                print(f"   ⚪ No changes: {os.path.basename(logic_file)}")
        except Exception as e:
            print(f"❌ Error processing {logic_file}: {e}")
            sys.exit(1)
    
    print(f"\n🎉 Complete! Updated {total_files_changed} files")

if __name__ == '__main__':
    main()
