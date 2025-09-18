#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTF-8 to CP1255 Converter
Converts files from UTF-8 encoding to CP1255 (Hebrew Windows encoding).
UTF-8 uses 2 bytes per Hebrew character, CP1255 uses 1 byte per Hebrew character.
"""

import os
import sys
import argparse
from pathlib import Path

def convert_file_utf8_to_cp1255(input_file, output_file=None):
    """
    Convert a single file from UTF-8 to CP1255 encoding.
    
    Args:
        input_file (str): Path to the input UTF-8 file
        output_file (str, optional): Path to the output CP1255 file. 
                                   If None, will overwrite the input file.
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    
    try:
        # Read the file as UTF-8
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📖 Reading UTF-8 file: {input_file}")
        print(f"   File size (UTF-8): {os.path.getsize(input_file)} bytes")
        print(f"   Characters read: {len(content)}")
        
        # Count Hebrew characters (for information)
        hebrew_chars = 0
        for char in content:
            if '\u0590' <= char <= '\u05FF':  # Hebrew Unicode block
                hebrew_chars += 1
        
        print(f"   Hebrew characters: {hebrew_chars}")
        
        # Set output file path
        if output_file is None:
            output_file = input_file
        
        # Write the content as CP1255
        with open(output_file, 'w', encoding='cp1255') as f:
            f.write(content)
        
        print(f"💾 Writing CP1255 file: {output_file}")
        print(f"   File size (CP1255): {os.path.getsize(output_file)} bytes")
        
        # Calculate size difference
        utf8_size = len(content.encode('utf-8'))
        cp1255_size = len(content.encode('cp1255'))
        size_reduction = utf8_size - cp1255_size
        
        print(f"   Size reduction: {size_reduction} bytes ({size_reduction/utf8_size*100:.1f}%)")
        print(f"✅ Conversion successful!")
        
        return True
        
    except UnicodeDecodeError as e:
        print(f"❌ Error: Input file is not valid UTF-8: {e}")
        return False
    except UnicodeEncodeError as e:
        print(f"❌ Error: Cannot encode to CP1255 (unsupported characters): {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: Input file not found: {input_file}")
        return False
    except Exception as e:
        print(f"❌ Error converting file: {e}")
        return False

def convert_directory_utf8_to_cp1255(input_dir, output_dir=None, pattern="*.txt"):
    """
    Convert all matching files in a directory from UTF-8 to CP1255.
    
    Args:
        input_dir (str): Path to the input directory
        output_dir (str, optional): Path to the output directory. If None, overwrites files.
        pattern (str): File pattern to match (default: "*.txt")
    
    Returns:
        tuple: (successful_count, total_count)
    """
    
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"❌ Error: Input directory not found: {input_dir}")
        return (0, 0)
    
    if not input_path.is_dir():
        print(f"❌ Error: Input path is not a directory: {input_dir}")
        return (0, 0)
    
    # Find matching files
    files = list(input_path.glob(pattern))
    
    if not files:
        print(f"❌ No files matching pattern '{pattern}' found in {input_dir}")
        return (0, 0)
    
    print(f"🔍 Found {len(files)} files matching pattern '{pattern}'")
    print("=" * 60)
    
    successful_count = 0
    
    for file_path in files:
        print(f"\nProcessing: {file_path.name}")
        
        # Determine output file path
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            output_file = output_path / file_path.name
        else:
            output_file = None  # Overwrite original
        
        # Convert the file
        if convert_file_utf8_to_cp1255(str(file_path), str(output_file) if output_file else None):
            successful_count += 1
        
        print("-" * 40)
    
    print(f"\n✅ Directory conversion complete!")
    print(f"   Files processed: {len(files)}")
    print(f"   Successful conversions: {successful_count}")
    print(f"   Failed conversions: {len(files) - successful_count}")
    
    return (successful_count, len(files))

def show_file_encoding_info(file_path):
    """
    Show encoding information about a file.
    
    Args:
        file_path (str): Path to the file to analyze
    """
    
    print(f"📊 File encoding analysis: {file_path}")
    print("-" * 50)
    
    try:
        # Try to read as UTF-8
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                utf8_content = f.read()
            print(f"✅ UTF-8 readable: {len(utf8_content)} characters")
            
            # Count Hebrew characters
            hebrew_chars = sum(1 for char in utf8_content if '\u0590' <= char <= '\u05FF')
            print(f"   Hebrew characters: {hebrew_chars}")
            
            # Calculate byte sizes
            utf8_bytes = len(utf8_content.encode('utf-8'))
            print(f"   UTF-8 size: {utf8_bytes} bytes")
            
            try:
                cp1255_bytes = len(utf8_content.encode('cp1255'))
                print(f"   CP1255 size: {cp1255_bytes} bytes")
                print(f"   Size difference: {utf8_bytes - cp1255_bytes} bytes")
            except UnicodeEncodeError:
                print(f"   ❌ Cannot encode to CP1255 (unsupported characters)")
                
        except UnicodeDecodeError:
            print(f"❌ File is not valid UTF-8")
        
        # Try to read as CP1255
        try:
            with open(file_path, 'r', encoding='cp1255') as f:
                cp1255_content = f.read()
            print(f"✅ CP1255 readable: {len(cp1255_content)} characters")
        except UnicodeDecodeError:
            print(f"❌ File is not valid CP1255")
        
        # Show actual file size
        file_size = os.path.getsize(file_path)
        print(f"📁 Actual file size: {file_size} bytes")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")

def main():
    """Main function with command line interface."""
    
    parser = argparse.ArgumentParser(
        description='Convert files from UTF-8 to CP1255 encoding',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file (overwrite)
  python utf8_to_cp1255_converter.py file.txt
  
  # Convert single file to new file
  python utf8_to_cp1255_converter.py file.txt -o file_cp1255.txt
  
  # Convert all .txt files in directory
  python utf8_to_cp1255_converter.py -d ./texts
  
  # Convert all .lgc files to output directory
  python utf8_to_cp1255_converter.py -d ./src -p "*.lgc" -o ./output
  
  # Analyze file encoding
  python utf8_to_cp1255_converter.py file.txt --info
        """
    )
    
    parser.add_argument('input', nargs='?', help='Input file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-d', '--directory', action='store_true', 
                       help='Process directory instead of single file')
    parser.add_argument('-p', '--pattern', default='*.txt', 
                       help='File pattern for directory processing (default: *.txt)')
    parser.add_argument('--info', action='store_true',
                       help='Show encoding information about the file')
    
    args = parser.parse_args()
    
    print("🔄 UTF-8 to CP1255 Converter")
    print("=" * 60)
    print("Converts Hebrew text files from UTF-8 (2 bytes/char) to CP1255 (1 byte/char)")
    print()
    
    if not args.input:
        parser.print_help()
        return
    
    # Show file information
    if args.info:
        show_file_encoding_info(args.input)
        return
    
    # Process directory
    if args.directory:
        convert_directory_utf8_to_cp1255(args.input, args.output, args.pattern)
    else:
        # Process single file
        convert_file_utf8_to_cp1255(args.input, args.output)

if __name__ == "__main__":
    main()
