#!/usr/bin/env python3
"""
Scan WORDS.TOK.EXTENDED file for duplicate words
Reports words that appear multiple times with different indices
"""

import argparse
import os
import sys
from collections import defaultdict

def scan_words_extended_for_duplicates(words_extended_path):
    """Scan WORDS.TOK.EXTENDED file for duplicate words"""
    
    if not os.path.exists(words_extended_path):
        print(f"❌ Error: File '{words_extended_path}' not found")
        return False
    
    print(f"🔍 Scanning WORDS.TOK.EXTENDED file: {words_extended_path}")
    print("=" * 60)
    
    word_occurrences = defaultdict(list)  # word -> [(index, line_number), ...]
    total_lines = 0
    total_words = 0
    
    try:
        # Try multiple encodings for AGI files
        encodings = ['Windows-1255']
        lines = None
        
        for encoding in encodings:
            try:
                with open(words_extended_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                print(f"✅ Successfully read file using {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if lines is None:
            # Fallback to binary mode
            with open(words_extended_path, 'rb') as f:
                content = f.read().decode('latin-1', errors='replace')
                lines = content.splitlines(keepends=True)
            print("✅ Read file in binary mode with latin-1 fallback")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            total_lines += 1
            
            # Skip header line
            if line.startswith('WORDS.TOK:') or not line:
                continue
            
            # Parse word entry: word\0index
            if '\0' in line:
                parts = line.split('\0')
                if len(parts) == 2:
                    word = parts[0]
                    try:
                        index = int(parts[1])
                        word_occurrences[word].append((index, line_num))
                        total_words += 1
                    except ValueError:
                        print(f"⚠️  Line {line_num}: Invalid index format - {parts[1]}")
                else:
                    print(f"⚠️  Line {line_num}: Invalid format - {line}")
            else:
                print(f"⚠️  Line {line_num}: Missing null separator - {line}")
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Find duplicates
    duplicates_found = 0
    exact_duplicates = 0
    index_conflicts = 0
    
    print(f"📊 File Statistics:")
    print(f"   Total lines: {total_lines}")
    print(f"   Total words: {total_words}")
    print(f"   Unique words: {len(word_occurrences)}")
    print()
    
    # Check for duplicate words
    for word, occurrences in word_occurrences.items():
        if len(occurrences) > 1:
            duplicates_found += 1
            
            # Check if all occurrences have the same index
            indices = [occ[0] for occ in occurrences]
            if len(set(indices)) == 1:
                # Same word, same index - exact duplicates
                exact_duplicates += 1
                print(f"🔄 Exact Duplicate: '{word[::-1]}' (index {indices[0]})")
                print(f"   Appears {len(occurrences)} times on lines: {[occ[1] for occ in occurrences]}")
            else:
                # Same word, different indices - index conflict
                index_conflicts += 1
                print(f"⚠️  Index Conflict: '{word[::-1]}' mapped to multiple indices: {sorted(set(indices))}")
                for index, line_num in occurrences:
                    print(f"   Line {line_num}: index {index}")
            print()
    
    # Summary
    print("=" * 60)
    if duplicates_found == 0:
        print("✅ No duplicate words found! File is clean.")
    else:
        print(f"⚠️  Found {duplicates_found} duplicate words:")
        print(f"   📋 Exact duplicates (same word, same index): {exact_duplicates}")
        print(f"   ⚠️  Index conflicts (same word, different indices): {index_conflicts}")
        
        if exact_duplicates > 0:
            print(f"\n💡 Exact duplicates can be safely removed to clean up the file.")
        
        if index_conflicts > 0:
            print(f"\n❌ Index conflicts need manual review!")
            print(f"   These indicate the same word is mapped to different game actions.")
    
    # Check for common patterns
    print(f"\n🔍 Pattern Analysis:")
    
    # Hebrew words with prefixes
    hebrew_words = [word for word in word_occurrences.keys() if any(ord(c) > 127 for c in word)]
    print(f"   Hebrew words: {len(hebrew_words)}")
    
    # Words with Hebrew prefixes
    prefix_words = [word for word in hebrew_words if word.startswith(('ה', 'ב', 'ל', 'מ', 'כ', 'ש'))]
    print(f"   Words with Hebrew prefixes: {len(prefix_words)}")
    
    # English words
    english_words = [word for word in word_occurrences.keys() if word.isascii()]
    print(f"   English words: {len(english_words)}")
    
    return duplicates_found == 0

def main():
    parser = argparse.ArgumentParser(
        description='Scan WORDS.TOK.EXTENDED file for duplicate words'
    )
    parser.add_argument('words_extended_path', 
                       help='Path to WORDS.TOK.EXTENDED file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed information about all words')
    
    args = parser.parse_args()
    
    success = scan_words_extended_for_duplicates(args.words_extended_path)
    
    if args.verbose:
        print(f"\n📋 Detailed word list:")
        word_occurrences = defaultdict(list)
        
        with open(args.words_extended_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith('WORDS.TOK:') or not line:
                    continue
                if '\0' in line:
                    parts = line.split('\0')
                    if len(parts) == 2:
                        word = parts[0]
                        try:
                            index = int(parts[1])
                            word_occurrences[word].append((index, line_num))
                        except ValueError:
                            pass
        
        for word in sorted(word_occurrences.keys()):
            occurrences = word_occurrences[word]
            if len(occurrences) == 1:
                index, line_num = occurrences[0]
                print(f"   {word} -> {index}")
            else:
                print(f"   {word} -> {[occ[0] for occ in occurrences]} (DUPLICATE)")
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
