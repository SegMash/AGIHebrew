#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to find and merge multi-line print statements in KQ1 Logic files.
Searches for print statements that span multiple lines and merges them into single lines:
- From: print("text1 " "text2");
- To:   print("text1 text2");
"""

import os
import re
import glob
import shutil
from datetime import datetime

def find_and_merge_multiline_prints(file_path):
    """
    Find all multi-line print statements in a Logic file and merge them.
    
    Args:
        file_path (str): Path to the Logic file
        
    Returns:
        tuple: (modified_lines, merge_count, merge_details)
    """
    
    try:
        with open(file_path, 'r', encoding='Windows-1255') as file:
            lines = file.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None, 0, []
    
    modified_lines = []
    merge_details = []
    merge_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if line starts with print("
        if line.startswith('print("'):
            # Check if this line also ends with "); - single line print
            if line.endswith('");'):
                # Single line print, keep as is
                modified_lines.append(lines[i])
                i += 1
                continue
            
            # This might be a multi-line print
            start_line = i + 1  # 1-based line numbering
            original_lines = [lines[i]]
            
            # Look for continuation lines
            j = i + 1
            found_end = False
            
            while j < len(lines):
                current_line = lines[j]
                original_lines.append(current_line)
                
                # Check if this line ends the print statement
                if current_line.strip().endswith('");'):
                    found_end = True
                    end_line = j + 1  # 1-based line numbering
                    break
                
                j += 1
            
            # If we found a complete multi-line print statement
            if found_end and j > i:
                # Merge the multi-line print into a single line
                merged_line = merge_print_statement(original_lines)
                if merged_line:
                    modified_lines.append(merged_line)
                    merge_count += 1
                    
                    # Record merge details
                    original_text = ''.join(original_lines).strip()
                    merge_details.append({
                        'start_line': start_line,
                        'end_line': end_line,
                        'original': original_text,
                        'merged': merged_line.strip()
                    })
                    
                    print(f"  Merged lines {start_line}-{end_line}")
                else:
                    # Failed to merge, keep original lines
                    modified_lines.extend(original_lines)
                
                i = j + 1  # Continue from after the end of this statement
            else:
                # Incomplete statement, keep original line
                modified_lines.append(lines[i])
                i += 1
        else:
            # Not a print statement, keep as is
            modified_lines.append(lines[i])
            i += 1
    
    return modified_lines, merge_count, merge_details

def merge_print_statement(statement_lines):
    """
    Merge multi-line print statement into a single line.
    
    Args:
        statement_lines (list): List of lines forming the print statement
        
    Returns:
        str: Merged single-line print statement
    """
    
    # Join all lines and remove extra whitespace
    full_statement = ''.join(line.rstrip() for line in statement_lines)
    
    # Extract the content between print(" and ");
    match = re.match(r'(\s*)print\("(.*)"\);', full_statement, re.DOTALL)
    if not match:
        return None
    
    indentation = match.group(1)
    content = match.group(2)
    
    # Remove quotes and concatenation artifacts
    # Replace patterns like '" "' with just a space
    content = re.sub(r'"\s*"', ' ', content)
    
    # Clean up multiple spaces
    content = re.sub(r'\s+', ' ', content)
    
    # Create the merged line
    merged_line = f'{indentation}print("{content}");\n'
    
    return merged_line

def process_file(file_path, create_backup=False):
    """
    Process a single Logic file to merge multi-line print statements.
    
    Args:
        file_path (str): Path to the Logic file
        create_backup (bool): Whether to create a backup
        
    Returns:
        dict: Processing result
    """
    
    filename = os.path.basename(file_path)
    result = {
        'file': filename,
        'success': False,
        'merge_count': 0,
        'backup_created': False,
        'error': None
    }
    
    # Find and merge multi-line prints
    modified_lines, merge_count, merge_details = find_and_merge_multiline_prints(file_path)
    
    if modified_lines is None:
        result['error'] = "Could not read file"
        return result
    
    result['merge_count'] = merge_count
    result['merge_details'] = merge_details
    
    if merge_count == 0:
        result['success'] = True
        result['error'] = "No multi-line prints found"
        return result
    
    # Create backup if requested
    if create_backup:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.backup_{timestamp}"
            shutil.copy2(file_path, backup_path)
            result['backup_created'] = True
            result['backup_path'] = backup_path
        except Exception as e:
            result['error'] = f"Could not create backup: {e}"
            return result
    
    # Write the modified file
    try:
        with open(file_path, 'w', encoding='Windows-1255') as file:
            file.writelines(modified_lines)
        result['success'] = True
    except Exception as e:
        result['error'] = f"Could not write file: {e}"
        
        # If writing failed and we created a backup, restore it
        if result['backup_created']:
            try:
                shutil.copy2(result['backup_path'], file_path)
                print(f"  Restored original file from backup")
            except Exception as restore_e:
                print(f"  ERROR: Could not restore backup: {restore_e}")
    
    return result

def process_src_directory(src_dir, create_backups=False, dry_run=False):
    """
    Process all Logic files in the src directory.
    
    Args:
        create_backups (bool): Whether to create backups
        dry_run (bool): If True, only show what would be done without making changes
    """
    
    # Validate src_dir
    if not os.path.exists(src_dir):
        print(f"Error: Source directory '{src_dir}' not found.")
        return
    
    # Find Logic files
    logic_files = glob.glob(os.path.join(src_dir, "*.lgc"))

    if not logic_files:
        print(f"No Logic files found in {src_dir}")
        return

    # If backup requested, backup the whole src directory before any changes
    backup_dir = None
    if create_backups and not dry_run:
        backup_dir = os.path.join(os.path.dirname(src_dir), "src_before_merge_multilines")
        if os.path.exists(backup_dir):
            print(f"ERROR: Backup directory '{backup_dir}' already exists. Please remove or rename it before running this script.")
            return
        try:
            shutil.copytree(src_dir, backup_dir)
            print(f"💾 Backup of src directory created at '{backup_dir}'")
        except Exception as e:
            print(f"Error: Could not backup src directory: {e}")
            return

    mode_text = "DRY RUN - " if dry_run else ""
    print(f"{mode_text}Processing {len(logic_files)} Logic files in {src_dir}")
    print("=" * 70)

    total_files = len(logic_files)
    processed_files = 0
    total_merges = 0
    files_with_merges = 0

    for i, file_path in enumerate(sorted(logic_files), 1):
        filename = os.path.basename(file_path)
        print(f"{i:2d}/{total_files}: {filename}")

        if dry_run:
            # Just analyze without modifying
            _, merge_count, merge_details = find_and_merge_multiline_prints(file_path)
            if merge_count > 0:
                files_with_merges += 1
                total_merges += merge_count
                print(f"    📋 Would merge {merge_count} multi-line print(s)")
                for detail in merge_details:
                    print(f"      Lines {detail['start_line']}-{detail['end_line']}")
            else:
                print(f"    ⏭️  No multi-line prints found")
        else:
            # Actually process the file
            result = process_file(file_path, create_backup=False)

            if result['success']:
                if result['merge_count'] > 0:
                    processed_files += 1
                    files_with_merges += 1
                    total_merges += result['merge_count']
                    print(f"    ✅ Merged {result['merge_count']} multi-line print(s)")
                else:
                    print(f"    ⏭️  No multi-line prints found")
            else:
                print(f"    ❌ FAILED: {result['error']}")

        print()

    print("=" * 70)
    print(f"Summary:")
    print(f"  Total files: {total_files}")
    if dry_run:
        print(f"  Files that would be modified: {files_with_merges}")
        print(f"  Total merges that would be performed: {total_merges}")
    else:
        print(f"  Files processed: {processed_files}")
        print(f"  Files with merges: {files_with_merges}")
        print(f"  Total merges performed: {total_merges}")
        if create_backups:
            print(f"  Backup directory: {backup_dir}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Find and merge multi-line print statements in KQ1 Logic files')
    parser.add_argument('--srcdir', type=str, required=True, help='Source directory containing Logic files (mandatory)')
    parser.add_argument('--file', '-f', type=str, help='Process a specific file')
    parser.add_argument('--all', '-a', action='store_true', help='Process all Logic files in src directory')
    parser.add_argument('--backup', action='store_true', help='Create backup files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    args = parser.parse_args()

    if args.file:
        # Process specific file
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            return
        
        print(f"Processing file: {args.file}")
        print("=" * 40)
        
        if args.dry_run:
            _, merge_count, merge_details = find_and_merge_multiline_prints(args.file)
            if merge_count > 0:
                print(f"📋 Would merge {merge_count} multi-line print(s):")
                for detail in merge_details:
                    print(f"  Lines {detail['start_line']}-{detail['end_line']}:")
                    print(f"    From: {detail['original'][:80]}...")
                    print(f"    To:   {detail['merged'][:80]}...")
            else:
                print("⏭️  No multi-line prints found")
        else:
            result = process_file(args.file, args.backup)
            
            if result['success']:
                if result['merge_count'] > 0:
                    print(f"✅ Merged {result['merge_count']} multi-line print(s)")
                    if result['backup_created']:
                        print(f"💾 Backup created: {result['backup_path']}")
                else:
                    print(f"⏭️  No multi-line prints found")
            else:
                print(f"❌ FAILED: {result['error']}")
    
    elif args.all or not any([args.file]):
        # Process all files (requires --srcdir)
        process_src_directory(args.srcdir, args.backup, args.dry_run)
    
    else:
        print("Multi-line Print Statement Merger")
        print("=" * 35)
        print("Usage:")
        print("  python find_and_merge_multiline_prints.py --all --srcdir <src_directory>   # Process all Logic files")
        print("  python find_and_merge_multiline_prints.py --file <path> --srcdir <src_directory>  # Process specific file")
        print("  python find_and_merge_multiline_prints.py --dry-run --srcdir <src_directory>      # Preview changes")
        print("  python find_and_merge_multiline_prints.py --backup --srcdir <src_directory>       # Create backups")

if __name__ == "__main__":
    main()
