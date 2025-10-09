#!/usr/bin/env python3
"""
Replace object names with numbers in AGI logic files.

Currently supports:
    get("Object Name")      -> get(iNN)
    has("Object Name")      -> has(iNN)
    drop("Object Name")     -> drop(iNN)
    obj.in.room("Object Name", currentRoom) -> obj.in.room(iNN, currentRoom)
    put("Object Name", <target/room/...>) -> put(iNN, <target/room/...>)

Enhancements:
    * Supports optional trailing '*' in source (e.g., "Dog Hair*") by attempting
        a lookup without the asterisk if the exact form isn't found.
    * Case-sensitive exact match first; fallback match without trailing '*'.
"""

import argparse
import csv
import os
import re
import shutil
from pathlib import Path


def load_object_mapping(csv_file):
    """Load object name to number mapping from CSV file"""
    mapping = {}
    try:
        with open(csv_file, 'r', encoding='windows-1255') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            
            for row in reader:
                if len(row) >= 2:
                    number = row[0].strip()
                    name = row[1].strip()
                    
                    # Skip special rows
                    if number == 'max_num_of_animated' or not number.isdigit():
                        continue
                        
                    mapping[name] = number
                    
        print(f"✅ Loaded {len(mapping)} object mappings from CSV (Windows-1255 encoding)")
        return mapping
        
    except Exception as e:
        print(f"❌ Error loading CSV file: {e}")
        return None


def backup_src_folder(src_folder):
    """Create backup of source folder"""
    backup_folder = src_folder.parent / "src_before_replace_objects"
    
    if backup_folder.exists():
        print(f"❌ Error: Backup folder '{backup_folder}' already exists!")
        print("   Please remove or rename the existing backup folder before proceeding.")
        return False
    
    try:
        shutil.copytree(src_folder, backup_folder)
        print(f"✅ Created backup: {backup_folder}")
        return True
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False


def replace_object_references(content, object_mapping):
    """Replace object names with numbers in supported command patterns."""
    total_changes = 0

    # 1. get/has/drop commands
    cmd_pattern = r'\b(get|has|drop)\s*\(\s*["\']([^"\']+)["\']\s*\)'

    def replace_simple(match):
        nonlocal total_changes
        command = match.group(1)
        object_name = match.group(2)
        number = object_mapping.get(object_name)
        if number is None and object_name.endswith('*'):
            base = object_name.rstrip('*').strip()
            if base in object_mapping:
                number = object_mapping[base]
        if number is not None:
            total_changes += 1
            return f"{command}(i{number})"
        return match.group(0)

    content = re.sub(cmd_pattern, replace_simple, content)

    # 2. obj.in.room("Name", <rest>) pattern
    # Capture object name and the remainder (comma + rest of args until closing paren)
    room_pattern = r'\bobj\.in\.room\s*\(\s*["\']([^"\']+)["\'](\s*,[^)]*?)\)'

    def replace_room(match):
        nonlocal total_changes
        object_name = match.group(1)
        remainder = match.group(2)
        number = object_mapping.get(object_name)
        if number is None and object_name.endswith('*'):
            base = object_name.rstrip('*').strip()
            if base in object_mapping:
                number = object_mapping[base]
        if number is not None:
            total_changes += 1
            return f"obj.in.room(i{number}{remainder})"
        return match.group(0)

    content = re.sub(room_pattern, replace_room, content)

    # 3. put("Name", <rest>) pattern (similar to obj.in.room but without prefix)
    put_pattern = r'\bput\s*\(\s*["\']([^"\']+)["\'](\s*,[^)]*?)\)'

    def replace_put(match):
        nonlocal total_changes
        object_name = match.group(1)
        remainder = match.group(2)
        number = object_mapping.get(object_name)
        if number is None and object_name.endswith('*'):
            base = object_name.rstrip('*').strip()
            if base in object_mapping:
                number = object_mapping[base]
        if number is not None:
            total_changes += 1
            return f"put(i{number}{remainder})"
        return match.group(0)

    content = re.sub(put_pattern, replace_put, content)

    return content, total_changes


def process_logic_file(file_path, object_mapping):
    """Process a single logic file"""
    try:
        # Read file with UTF-8 first, then Windows-1255 fallback
        content = None
        encodings = ['utf-8', 'windows-1255', 'latin-1']
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"⚠️  Could not read file: {file_path}")
            return 0

        # Replace object references in supported patterns
        new_content, changes_made = replace_object_references(content, object_mapping)

        # Write back if changes were made (prefer Windows-1255 for AGI files)
        if changes_made > 0:
            write_encoding = 'windows-1255' if used_encoding in ['windows-1255', 'latin-1'] else 'utf-8'
            with open(file_path, 'w', encoding=write_encoding) as f:
                f.write(new_content)
            print(f"   📝 {file_path.name}: {changes_made} replacements (encoding: {used_encoding}→{write_encoding})")

        return changes_made
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0


def scan_and_replace_objects(src_folder, csv_file):
    """Main function to scan and replace object names"""
    src_path = Path(src_folder)
    csv_path = Path(csv_file)
    
    # Validate inputs
    if not src_path.exists() or not src_path.is_dir():
        print(f"❌ Error: Source folder '{src_folder}' does not exist or is not a directory")
        return False
    
    if not csv_path.exists():
        print(f"❌ Error: CSV file '{csv_file}' does not exist")
        return False
    
    # Load object mapping
    object_mapping = load_object_mapping(csv_file)
    if not object_mapping:
        return False
    
    # Create backup
    if not backup_src_folder(src_path):
        return False
    
    # Find all .lgc files
    logic_files = list(src_path.glob("*.lgc"))
    if not logic_files:
        print(f"⚠️  No .lgc files found in {src_folder}")
        return False
    
    print(f"\n🔍 Processing {len(logic_files)} logic files...")
    print("=" * 50)
    
    total_changes = 0
    files_modified = 0
    
    for logic_file in sorted(logic_files):
        changes = process_logic_file(logic_file, object_mapping)
        total_changes += changes
        if changes > 0:
            files_modified += 1
    
    # Summary
    print("=" * 50)
    print(f"📊 SUMMARY:")
    print(f"   Files processed: {len(logic_files)}")
    print(f"   Files modified: {files_modified}")
    print(f"   Total replacements: {total_changes}")
    print(f"   Backup created: {src_path.parent}/src_before_replace_objects")
    
    if total_changes > 0:
        print(f"\n✅ Object replacement completed successfully!")
        print(f"   Example: has(\"Oil Lamp\") → has(i{object_mapping.get('Oil Lamp', 'XX')})")
    else:
        print(f"\n⚠️  No object names found to replace")
    
    return True


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Replace object names with numbers in AGI logic files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("src_folder", help="Source folder containing .lgc files")
    parser.add_argument("csv_file", help="CSV file with object number/name mapping")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    
    args = parser.parse_args()
    
    print("🔄 AGI Object Name to Number Replacer")
    print("=" * 40)
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - No files will be modified")
        print("=" * 40)
        # TODO: Implement dry run functionality
        print("⚠️  Dry run mode not implemented yet")
        return
    
    success = scan_and_replace_objects(args.src_folder, args.csv_file)
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()
