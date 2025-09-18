#!/usr/bin/env python
"""
Script to split a large text file into smaller files with a specified number of lines.
The script creates a subfolder to store the split files.
"""

import os
import argparse
import sys

def split_file(input_file, output_dir=None, lines_per_file=250):
    """
    Split a large text file into smaller files with a specified number of lines.
    
    Args:
        input_file (str): Path to the input text file
        output_dir (str, optional): Directory to save the split files. If None, 
                                    will create a subfolder with the input file's name
        lines_per_file (int, optional): Maximum number of lines per output file
    """
    # Get the input file name without extension to use as folder name
    input_basename = os.path.basename(input_file)
    input_name = os.path.splitext(input_basename)[0]
    
    # Create output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(input_file), f"{input_name}_split")
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Reading input file: {input_file}")
    print(f"Splitting into files with {lines_per_file} lines each")
    print(f"Output directory: {output_dir}")
    
    # Open the input file and read all lines
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    print(f"Total lines in input file: {total_lines}")
    
    # Calculate the number of output files needed
    num_files = (total_lines + lines_per_file - 1) // lines_per_file
    
    # Split the lines into multiple files
    for i in range(num_files):
        start_line = i * lines_per_file
        end_line = min((i + 1) * lines_per_file, total_lines)
        
        # Create output file name with part number
        output_file = os.path.join(output_dir, f"{input_name}_part{i+1}.csv")
        
        # Write lines to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines[start_line:end_line])
        
        print(f"Created file {output_file} with lines {start_line+1} to {end_line}")
    
    print(f"Split complete! Created {num_files} files in {output_dir}")

def main():
    parser = argparse.ArgumentParser(
        description="Split a large text file into smaller files with a specified number of lines"
    )
    parser.add_argument(
        "input_file", 
        help="Path to the input text file"
    )
    parser.add_argument(
        "--output-dir", "-o", 
        help="Directory to save the split files (optional)"
    )
    parser.add_argument(
        "--lines", "-l", 
        type=int, 
        default=500,
        help="Number of lines per output file (default: 500)"
    )
    
    args = parser.parse_args()
    
    try:
        split_file(args.input_file, args.output_dir, args.lines)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
