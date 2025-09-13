#!/usr/bin/env python3
"""
Scan a folder (non-recursive) for *.lgc files and extract strings from said("..."), said("...","..."),
and said("...","...","...") calls. Handles multiple said() calls per line.

Can output in different formats:
- list format: Creates list of lists like [["give","treasure"],["give","troll","treasure"]]
- pipe format: <arg1>[|<arg2>][|<arg3>] (original format)

Notes:
- Scans only the specified folder (non-recursive).
- Strings are unescaped for common sequences (\" -> ", \\ -> \\ , \n -> newline).
"""
from __future__ import annotations

import argparse
import re
import json
from pathlib import Path
from typing import List, Set


# Regex for said("arg1")(, "arg2")?(, "arg3")?
SAID_RE = re.compile(
    r"said\s*\(\s*\""  # opening quote for arg1
    r"((?:[^\"\\]|\\.)*)"  # arg1 in group 1
    r"\""  # closing quote for arg1
    r"(?:\s*,\s*\"((?:[^\"\\]|\\.)*)\")?"  # optional arg2 in group 2
    r"(?:\s*,\s*\"((?:[^\"\\]|\\.)*)\")?"  # optional arg3 in group 3
    r"\s*\)",
    re.IGNORECASE,
)


def unescape(s: str) -> str:
    """Unescape common C-style sequences inside LGC strings.
    Currently supports: \", \\, \n, \t, \r.
    """
    # Replace escaped sequences
    s = s.replace(r"\"", '"')
    s = s.replace(r"\\", "\\")
    s = s.replace(r"\n", "\n")
    s = s.replace(r"\t", "\t")
    s = s.replace(r"\r", "\r")
    return s


def extract_room_number(filename: str) -> int:
    """Extract room number from Logic file name (e.g., Logic83.lgc -> 83)."""
    # Match pattern LogicXXX.lgc where XXX is the room number
    match = re.match(r"Logic(\d+)\.lgc", filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return -1  # Unknown room


def scan_file(path: Path, acc: set[tuple[str, ...]], room_acc: dict[tuple[str, ...], set[int]]):
    """Scan a single file for said() calls and add tokens to accumulator with room tracking."""
    room_number = extract_room_number(path.name)
    
    # Read with tolerant decoding
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, 1):
            for m in SAID_RE.finditer(line):
                a1 = unescape(m.group(1) or "")
                a2 = m.group(2)
                a3 = m.group(3)
                parts = [a1]
                if a2 is not None:
                    parts.append(unescape(a2))
                if a3 is not None:
                    parts.append(unescape(a3))
                
                token_tuple = tuple(parts)
                acc.add(token_tuple)
                
                # Track which rooms contain this said() call
                if token_tuple not in room_acc:
                    room_acc[token_tuple] = set()
                room_acc[token_tuple].add(room_number)


def output_as_list(tokens: set[tuple[str, ...]]) -> List[List[str]]:
    """Convert set of tuples to list of lists format."""
    return [list(parts) for parts in sorted(tokens)]


def output_as_pipe(tokens: set[tuple[str, ...]]) -> List[str]:
    """Convert set of tuples to pipe-separated format."""
    return ["|".join(parts) for parts in sorted(tokens)]


def save_tokens_to_file(tokens: List[List[str]], room_acc: dict[tuple[str, ...], set[int]], output_file: str, format_type: str = "json"):
    """
    Save said tokens to a file.
    
    Args:
        tokens: List of token lists
        room_acc: Dictionary mapping token tuples to sets of room numbers
        output_file: Output file path
        format_type: Output format ("json", "python", "text", or "csv")
    """
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            if format_type.lower() == "csv":
                # CSV format: room_number, said_tokens
                import csv
                writer = csv.writer(outfile)
                writer.writerow(["room_number", "said_tokens"])  # Header
                
                # Create dictionary to store first occurrence of each said_tokens
                unique_tokens = {}
                total_entries = 0
                
                for token_list in tokens:
                    token_tuple = tuple(token_list)
                    rooms = room_acc.get(token_tuple, {-1})
                    said_tokens = " ".join(token_list)  # Space-separated tokens
                    
                    for room in sorted(rooms):
                        total_entries += 1
                        # Only keep the first occurrence of each said_tokens (with lowest room number)
                        if said_tokens not in unique_tokens:
                            unique_tokens[said_tokens] = room
                
                # Convert to list and sort by room number first, then by said tokens
                csv_rows = [(room, said_tokens) for said_tokens, room in unique_tokens.items()]
                csv_rows.sort(key=lambda x: (x[0], x[1]))  # Sort by room number first, then said_tokens
                
                # Print deduplication info
                unique_entries = len(csv_rows)
                if total_entries != unique_entries:
                    print(f"📊 Token deduplication: {total_entries} total entries → {unique_entries} unique said_tokens ({total_entries - unique_entries} duplicates removed)")
                
                # Write sorted unique rows
                for room, said_tokens in csv_rows:
                    writer.writerow([room, said_tokens])
                        
            elif format_type.lower() == "json":
                # Enhanced JSON with room information
                result = []
                for token_list in tokens:
                    token_tuple = tuple(token_list)
                    rooms = sorted(list(room_acc.get(token_tuple, {-1})))
                    result.append({
                        "tokens": token_list,
                        "rooms": rooms
                    })
                json.dump(result, outfile, indent=2, ensure_ascii=False)
                
            elif format_type.lower() == "python":
                outfile.write("# Said tokens with room information\n")
                outfile.write("said_tokens = [\n")
                for token_list in tokens:
                    token_tuple = tuple(token_list)
                    rooms = sorted(list(room_acc.get(token_tuple, {-1})))
                    token_str = "[" + ", ".join(f'"{token}"' for token in token_list) + "]"
                    outfile.write(f"    {{'tokens': {token_str}, 'rooms': {rooms}}},\n")
                outfile.write("]\n")
                
            else:  # text format with room numbers
                seen_sentences = set()
                for token_list in tokens:
                    token_tuple = tuple(token_list)
                    rooms = sorted(list(room_acc.get(token_tuple, {-1})))
                    
                    # Filter out "anyword" from the token list
                    filtered_tokens = [token for token in token_list if token.lower() != "anyword"]
                    
                    # Skip empty lists after filtering
                    if not filtered_tokens:
                        continue
                    
                    # Create space-separated sentence with room info
                    sentence = " ".join(filtered_tokens)
                    room_info = f"(rooms: {', '.join(str(r) for r in rooms)})"
                    full_line = f"{sentence} {room_info}"
                    
                    # Only write if we haven't seen this sentence before
                    if sentence not in seen_sentences:
                        seen_sentences.add(sentence)
                        outfile.write(full_line + "\n")
        
        print(f"Said tokens saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving tokens: {str(e)}")


def print_statistics(tokens: List[List[str]], room_acc: dict[tuple[str, ...], set[int]]):
    """Print statistics about the extracted said tokens."""
    if not tokens:
        print("No said tokens found.")
        return
    
    print(f"\nStatistics:")
    print("-" * 30)
    print(f"Total unique said() calls: {len(tokens)}")
    
    # Count by number of parameters
    param_counts = {}
    all_words = set()
    all_rooms = set()
    
    for token_list in tokens:
        param_count = len(token_list)
        param_counts[param_count] = param_counts.get(param_count, 0) + 1
        all_words.update(token_list)
        
        # Add rooms for this token
        token_tuple = tuple(token_list)
        rooms = room_acc.get(token_tuple, set())
        all_rooms.update(rooms)
    
    print("Said calls by parameter count:")
    for count in sorted(param_counts.keys()):
        print(f"  {count} parameters: {param_counts[count]} calls")
    
    print(f"Unique words used: {len(all_words)}")
    print(f"Rooms with said() calls: {len(all_rooms)} rooms")
    
    # Show room distribution
    if all_rooms:
        valid_rooms = [r for r in all_rooms if r != -1]
        if valid_rooms:
            print(f"Room range: {min(valid_rooms)} - {max(valid_rooms)}")
    
    # Show some example words
    sorted_words = sorted(list(all_words))
    if len(sorted_words) <= 20:
        print(f"All words: {sorted_words}")
    else:
        print(f"Sample words: {sorted_words[:20]}...")


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract said(\"...\") strings from .lgc files in a folder")
    ap.add_argument("folder", type=Path, help="Folder to scan for *.lgc files")
    ap.add_argument("--output", "-o", type=str, help="Output file to save said tokens")
    ap.add_argument("--format", "-f", type=str, choices=['json', 'python', 'text', 'pipe', 'csv'], default='list',
                   help="Output format: json, python, text, pipe, csv, or list (default: list)")
    ap.add_argument("--stats", "-s", action="store_true", help="Show statistics about extracted tokens")
    ap.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    # Non-recursive by design
    args = ap.parse_args()

    folder: Path = args.folder
    if not folder.exists() or not folder.is_dir():
        raise SystemExit(f"Folder not found or not a directory: {folder}")

    files = sorted(p for p in folder.glob("*.lgc") if p.is_file())
    
    if args.verbose:
        print(f"Scanning {len(files)} .lgc files in {folder}")

    acc: set[tuple[str, ...]] = set()
    room_acc: dict[tuple[str, ...], set[int]] = {}
    
    for path in files:
        if args.verbose:
            print(f"Processing: {path.name}")
        scan_file(path, acc, room_acc)

    if not acc:
        print("No said() tokens found in the specified directory.")
        return

    # Convert to desired format
    if args.format == 'pipe':
        # Original pipe-separated format with room info
        for token_tuple in sorted(acc):
            rooms = sorted(list(room_acc.get(token_tuple, {-1})))
            token_str = "|".join(token_tuple)
            room_str = ",".join(str(r) for r in rooms)
            print(f"{token_str} (rooms: {room_str})")
    else:
        # List of lists format
        token_lists = output_as_list(acc)
        
        if args.format == 'list' and not args.output:
            # Print as Python list format to console with room info
            print("# Said tokens with room information")
            for token_list in token_lists:
                token_tuple = tuple(token_list)
                rooms = sorted(list(room_acc.get(token_tuple, {-1})))
                print(f"{token_list} -> rooms: {rooms}")
        elif not args.output:
            # Print sample to console with room info
            print(f"Found {len(token_lists)} unique said() token combinations:")
            for i, tokens in enumerate(token_lists[:10]):
                token_tuple = tuple(tokens)
                rooms = sorted(list(room_acc.get(token_tuple, {-1})))
                room_str = ", ".join(str(r) for r in rooms)
                print(f"{i+1:3}: {tokens} (rooms: {room_str})")
            if len(token_lists) > 10:
                print(f"... and {len(token_lists) - 10} more")
        
        # Save to file if requested
        if args.output:
            save_tokens_to_file(token_lists, room_acc, args.output, args.format)
        
        # Show statistics if requested
        if args.stats:
            print_statistics(token_lists, room_acc)


if __name__ == "__main__":
    main()
