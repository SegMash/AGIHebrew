import argparse
import csv
import os
import re
import shutil

import config
from config import messages_csv_filename
from config import messages_keys


def update(s, index, translation):
    """
    Replace any string literal that matches the original text with the translation.
    Handles escaped quotes properly.
    """
    # Escape the translation for use in the replacement
    escaped_translation = translation.replace('\\', '\\\\').replace('"', r'\"')
    
    # First, try the original #message pattern for backward compatibility
    original_pattern = f'#message {index} ".*"'
    s = re.sub(original_pattern, f'#message {index} "{escaped_translation}"', s)
    
    # Now also replace any standalone string that matches the original text
    # We need to get the original text for this entry - but we don't have it here
    # So let's modify this to accept the original text as well
    
    return s


def update_with_original(s, index, original_text, translation):
    """
    Replace string literals with message indices.
    For #message patterns: keep the translation
    For standalone strings: replace with message index (e.g., m173)
    """
    # Escape the translation for use in the replacement
    escaped_translation = translation.replace('\\', '\\\\').replace('"', r'\"')
    
    # First, handle #message patterns - keep the actual translation here
    original_pattern = f'#message {index} ".*"'
    s = re.sub(original_pattern, f'#message {index} "{escaped_translation}"', s)
    
    # Then, replace any string literal that matches the original text with message index
    #if original_text:
    #    # Escape the original text for regex matching
    #    escaped_original = re.escape(original_text)
    #    # Pattern to match the exact string in quotes
    #    string_pattern = f'"{escaped_original}"'
    #    # Replace with message index (no quotes around the index)
    #    replacement = f'm{index}'
    #    s = re.sub(string_pattern, replacement, s)
        
        # If original text contains multiple spaces, try with normalized single spaces
    #    if '  ' in original_text:  # Check if there are double spaces
    #        normalized_text = re.sub(r'\s+', ' ', original_text)  # Replace multiple spaces with single space
    #        escaped_normalized = re.escape(normalized_text)
    #        normalized_pattern = f'"{escaped_normalized}"'
    #        s = re.sub(normalized_pattern, replacement, s)
    
    return s


def get_number(entry, attr):
    # Use English key directly since our CSV has English headers
    return int(float(entry[attr]))


def messages_import(srcdir, pattern, csvdir):
    sierra_orig_dir = os.path.join(srcdir, config.sierra_original)
    try:
        os.mkdir(sierra_orig_dir)
    except:
        pass

    with open(os.path.join(csvdir, messages_csv_filename), newline='', encoding='utf-8') as csvfile:
        # Read the CSV file without expecting headers
        reader = csv.reader(csvfile, skipinitialspace=True)
        texts = []
        
        for row in reader:
            if len(row) >= 4:  # Ensure we have at least room, idx, original, translation
                # Create dictionary with expected column names
                entry = {
                    'room': row[0],
                    'idx': row[1], 
                    'original': row[2],
                    'translation': row[3] if len(row) > 3 else '',
                    'comments': row[4] if len(row) > 4 else ''
                }
                texts.append(entry)
            elif len(row) > 0:  # Skip empty rows but warn about incomplete rows
                print(f"Warning: Skipping incomplete row: {row}")
    
    rooms = sorted(list(set([get_number(entry, 'room') for entry in texts])))
    
    for room in rooms:
        entries = [entry for entry in texts if get_number(entry, 'room') == room]
        

        if set([entry['translation'] for entry in entries]) == {''}:
            # there is no translated entry, no need to do anything, skip this room
            continue

        

        filename = f"Logic{room}.lgc"
        full_filename = os.path.join(srcdir, filename)

        sierra_orig_file = os.path.join(sierra_orig_dir, filename)
        if os.path.exists(sierra_orig_file):
            # there is a copy of the original file - let's copy it over, to start from clean, and have translation changes applied
            shutil.copy2(sierra_orig_file, srcdir)
        else:
            # save a copy of the original sierra file (because we haven't already done so)
            shutil.copy2(full_filename, sierra_orig_dir)

        with open(full_filename, encoding=config.encoding) as f:
            logic = f.read()

        for entry in entries:
            if entry['translation']:
                # Check for space mismatches between original and translation
                original_has_spaces = entry['original'].strip() != entry['original']
                translation_has_spaces = entry['translation'].strip() != entry['translation']
                
                #if original_has_spaces != translation_has_spaces:
                #    print("WARNING: space problems at ", entry)
                #    print(f"  Original: '{entry['original']}' (has spaces: {original_has_spaces})")
                #    print(f"  Translation: '{entry['translation']}' (has spaces: {translation_has_spaces})")
                
                logic = update_with_original(logic, get_number(entry, 'idx'), entry['original'], entry['translation'])

        with open(full_filename, 'w', encoding=config.encoding, newline='\n') as f:
            f.write(logic)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Imports text messages from csv file to logic files ',
                                     epilog='''
Logic files have all the texts messages (strings) at the end of the file.
You should have already run the export script, and translate the csv file.
This imports all these messages to from a csv file, back to the logic files. 
''')
    parser.add_argument("srcdir", help="src directory containing the logic files")
    parser.add_argument("--pattern", default='*.lgc', help="logic files pattern")
    parser.add_argument("csvdir", help="directory to read messages.csv")
    args = parser.parse_args()

    messages_import(args.srcdir, args.pattern, args.csvdir)

