#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import glob
import argparse
from datetime import datetime

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Merge Hebrew translated CSV files into a single file')
    parser.add_argument('--srcdir', required=True, help='Source directory containing the *_part*.csv files')
    parser.add_argument('--output', default='messages_merged_hebrew.csv', help='Output file name (default: messages_merged_hebrew.csv)')
    
    args = parser.parse_args()
    
    # Validate source directory
    if not os.path.exists(args.srcdir):
        print(f"Error: Source directory '{args.srcdir}' does not exist")
        return
    
    # Define source folder and output file
    source_folder = args.srcdir
    output_file = args.output

    # Find all matching CSV files
    file_pattern = os.path.join(source_folder, "*_part*.csv")
    files = glob.glob(file_pattern)

    # Extract numbers and sort files numerically
    def extract_number(filename):
        match = re.search(r'part(\d+)\.csv$', filename)
        if match:
            return int(match.group(1))
        return 0

    # Sort files by their numeric part
    files.sort(key=extract_number)

    if files:
        # Create output file
        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Process each file
            print(f"Processing {len(files)} files in numerical order...")
            
            for file_path in files:
                file_name = os.path.basename(file_path)
                
                # Read and append content
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    # Add newline if file doesn't end with one
                    if content and not content.endswith('\n'):
                        outfile.write('\n')
                
                print(f"Added content from: {file_name}")
        
        print(f"Merge complete! All files have been combined into: {output_file}")
    else:
        print(f"No matching *_part*.csv files found in {source_folder}")

if __name__ == "__main__":
    main()
