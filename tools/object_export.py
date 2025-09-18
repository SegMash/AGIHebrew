import argparse
import csv
import os

import config


def read_le(l, idx):
    return l[idx] + l[idx + 1] * 256


def xor_lob(lob):
    return [b^ord((config.xoring_key[idx % len(config.xoring_key)])) for (idx, b) in enumerate(lob)]


def read_objects(gamedir):
    objects = []
    with open(os.path.join(gamedir, config.objectfile), "rb") as f:
        mem = list(f.read())
    
    flen = len(mem)
    
    # Check if first pointer exceeds file size - if so, it's encrypted
    if read_le(mem, 0) > flen:
        print("Decrypting objects...")
        mem = xor_lob(mem)
        print("done.")
    
    # Platform specific padding size (assuming DOS = 3)
    padsize = 3
    
    # Calculate number of objects
    num_objects = read_le(mem, 0) // padsize
    print(f"num_objects = {num_objects} (padsize = {padsize})")
    
    if num_objects > 256:
        print("Warning: Too many objects detected")
        return ([], 0)
    
    # Get version info - assuming version >= 0x2000 for modern AGI
    spos = padsize  # For version >= 0x2000
    
    # Read max animated objects (byte 2)
    max_num_of_animated = mem[2] if len(mem) > 2 else 0
    
    # Build object list
    for i in range(num_objects):
        so = spos + (i * padsize)  # Calculate object entry position
        
        if so + 2 >= flen:
            break
            
        # Read object entry
        offset = read_le(mem, so) + spos
        location = mem[so + 2] if so + 2 < flen else 0
        
        # Read object name
        name = ""
        if offset < flen:
            # Read null-terminated string from offset
            name_idx = offset
            while name_idx < flen and mem[name_idx] != 0:
                name += chr(mem[name_idx])
                name_idx += 1
        else:
            print(f"Warning: object {i} name beyond file size ({offset:04x} > {flen:04x})")
            name = ""
        
        # Special handling for invalid "?" objects in ego's inventory
        EGO_OWNED = 255  # Common value for ego-owned objects
        if name == "?" and location == EGO_OWNED:
            location = 0
            
        objects.append({'index': i, 'location': location, 'name': name})
    
    print(f"Reading objects: {len(objects)} objects read.")
    return (objects, max_num_of_animated)


def object_export(gamedir, csvdir):
    # Check if output file already exists
    output_file_path = os.path.join(csvdir, config.object_csv_filename)
    if os.path.exists(output_file_path):
        print(f"❌ Error: Output file '{output_file_path}' already exists!")
        print(f"   To prevent accidental overwriting, please:")
        print(f"   1. Delete or rename the existing file, or")
        print(f"   2. Choose a different output directory")
        exit(1)

    (objects, max_num_of_animated) = read_objects(gamedir)
    with open(output_file_path, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=config.object_keys.values())
        dict_writer.writeheader()

        dict_writer.writerow({
            config.object_keys['room']: 'max_num_of_animated',
            config.object_keys['original']: max_num_of_animated,
            config.object_keys['comments']: "אין לשנות שורה זו",
        })

        for entry in objects:
            dict_writer.writerow({
                config.object_keys['room']: entry['index'],  # Object number (index)
                config.object_keys['original']: entry['name']  # Object name
            })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Exports object file content to csv file',)
    parser.add_argument("gamedir", help="directory containing the game files")
    parser.add_argument("csvdir", help="directory to write {}".format(config.object_csv_filename))
    args = parser.parse_args()

    object_export(args.gamedir, args.csvdir)

