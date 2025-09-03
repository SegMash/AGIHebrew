#!/usr/bin/env python3
"""
Read the VIEWDIR file and print each 3-byte unsigned integer (u24) in decimal.

Also supports dumping view resource text payloads, either as hex or as text.
"""
from __future__ import annotations

import argparse
from pathlib import Path


ABSENT = 0xFFFFFF  # 24-bit sentinel for missing entry


def u24_from_bytes(b: bytes) -> int:
    if len(b) != 3:
        raise ValueError("u24_from_bytes requires exactly 3 bytes")
    return (b[0] << 16) | (b[1] << 8) | b[2]


def get_view_offset_and_size(index: int, viewdir_path: Path) -> tuple[int, int]:
    """Return (offset, size) for a view index using VIEWDIR.

    - Offset is the BE u24 at index*3.
    - Size is the total size of the resource in VOL.0: next_valid_offset - offset.
      Next valid offset is the next entry with value != 0xFFFFFF.
    """
    if index < 0:
        raise IndexError("index must be non-negative")
    if not viewdir_path.exists():
        raise FileNotFoundError(f"VIEWDIR not found at {viewdir_path}")

    data = viewdir_path.read_bytes()
    count = len(data) // 3
    if index >= count:
        raise IndexError(f"index {index} out of range (VIEWDIR has {count} entries)")

    def entry(i: int) -> int:
        base = i * 3
        return u24_from_bytes(data[base:base+3])

    cur = entry(index)
    if cur == ABSENT:
        raise ValueError(f"index {index} has no view (offset=0xFFFFFF)")

    # Find next valid offset
    next_off = None
    for j in range(index + 1, count):
        v = entry(j)
        if v != ABSENT:
            next_off = v
            break
    if next_off is None:
        raise ValueError(f"no subsequent valid entry after index {index} to derive size")

    size = next_off - cur
    if size < 0:
        raise ValueError(f"computed negative size for index {index}: next={next_off}, cur={cur}")
    return cur, size


def _extract_text_data(offset: int, total_size: int, vol_path: Path) -> bytes:
    """Extract and return the text data bytes contained in the view resource.

    Steps:
    - Read uint16 at (offset+7) as text_offset (big-endian)
    - Jump to (offset + text_offset + 3)
    - Read a 2-byte little-endian length L, then return the next L bytes
    """
    if not vol_path.exists():
        raise FileNotFoundError(f"VOL.0 not found at {vol_path}")
    with vol_path.open('rb') as f:
        # Read the 2-byte text offset at offset+7 (big-endian)
        f.seek(offset + 7)
        hdr = f.read(2)
        if len(hdr) != 2:
            raise ValueError("could not read 2-byte text offset at offset+7")
        text_offset = (hdr[0] << 8) | hdr[1]
        # If the combined 16-bit offset is out of bounds, try using only the low byte.
        if text_offset > total_size:
            text_offset = hdr[1]
            if text_offset > total_size:
                raise ValueError(f"text_offset {text_offset} out of bounds for resource size {total_size}")

        start = offset + text_offset + 3
        # Bounds check for length field
        if start + 2 > offset + total_size:
            raise ValueError("insufficient data for 2-byte text length")
        f.seek(start)
        len_bytes = f.read(2)
        if len(len_bytes) != 2:
            raise ValueError("could not read 2-byte text length at start of text block")
        # Skip the 2-byte length and compute remaining bytes as the text length
        payload_start = start + 2
        # Remaining bytes from payload_start to end of resource
        text_len = total_size - (payload_start - offset)
        if text_len < 0:
            raise ValueError(
                f"negative computed text length: total_size={total_size}, payload_start={payload_start}, offset={offset}"
            )
        # Optional debug print of computed length
        # print(f"computed text length for offset {offset}: {text_len}")
        f.seek(payload_start)
        data = f.read(text_len)
        if len(data) != text_len:
            raise ValueError(f"could not read payload of {text_len} bytes at text block")
    return data


def print_view_bytes(offset: int, total_size: int, vol_path: Path, print_func=print) -> None:
    """Print the extracted text data as a continuous lowercase hex string."""
    data = _extract_text_data(offset, total_size, vol_path)
    print_func(data.hex())


def print_view_text(offset: int, total_size: int, vol_path: Path, print_func=print) -> None:
    """Print the extracted text data as characters 0-255 until a null terminator.

    Decoding uses latin-1 so each byte maps 1:1 to a Unicode code point.
    """
    data = _extract_text_data(offset, total_size, vol_path)
    end = data.find(b"\x00")
    if end != -1:
        data = data[:end]
    # Map bytes 0..255 directly to Unicode code points 0..255
    text = data.decode('latin-1', errors='replace')
    print_func(text)


def print_view_full(offset: int, total_size: int, vol_path: Path, print_func=print) -> None:
    """Dump the entire resource bytes from VOL.0 starting at offset for total_size bytes as hex."""
    if not vol_path.exists():
        raise FileNotFoundError(f"VOL.0 not found at {vol_path}")
    with vol_path.open('rb') as f:
        f.seek(offset+3)
        total_size -= 3
        data = f.read(total_size)
        if len(data) != total_size:
            raise ValueError(f"could not read {total_size} bytes from offset {offset}")
    print_func(data.hex())


def get_view_offset_and_size_with_fallback(index: int, viewdir_path: Path, vol_path: Path) -> tuple[int, int]:
    """Like get_view_offset_and_size, but if there's no subsequent valid entry,
    fall back to (VOL.0 size - offset) for the size.
    """
    if not viewdir_path.exists():
        raise FileNotFoundError(f"VIEWDIR not found at {viewdir_path}")
    if not vol_path.exists():
        raise FileNotFoundError(f"VOL.0 not found at {vol_path}")

    data = viewdir_path.read_bytes()
    count = len(data) // 3
    if index < 0 or index >= count:
        raise IndexError(f"index {index} out of range (VIEWDIR has {count} entries)")

    def entry(i: int) -> int:
        base = i * 3
        return u24_from_bytes(data[base:base+3])

    cur = entry(index)
    if cur == ABSENT:
        raise ValueError(f"index {index} has no view (offset=0xFFFFFF)")

    # find next valid
    next_off = None
    for j in range(index + 1, count):
        v = entry(j)
        if v != ABSENT:
            next_off = v
            break
    if next_off is not None:
        return cur, next_off - cur
    # fallback: use vol file size
    vol_size = vol_path.stat().st_size
    size = max(0, vol_size - cur)
    return cur, size


def list_all_view_texts(viewdir_path: Path, vol_path: Path, start: int | None = None, end: int | None = None, print_func=print) -> None:
    """Iterate VIEWDIR indexes in [start, end] and print "<index>|<text>" for each entry.

    - Text is extracted via _extract_text_data and decoded as latin-1, trimmed at NUL.
    - Absent entries (0xFFFFFF) are skipped.
    - For the last present entry (no next offset), size falls back to (VOL.0 size - offset).
    """
    if not viewdir_path.exists():
        raise FileNotFoundError(f"VIEWDIR not found at {viewdir_path}")
    if not vol_path.exists():
        raise FileNotFoundError(f"VOL.0 not found at {vol_path}")

    data = viewdir_path.read_bytes()
    count = len(data) // 3

    # Resolve range
    if start is None:
        start = 0
    if end is None:
        end = count - 1
    if start < 0 or end < 0 or start >= count or end >= count:
        raise IndexError(f"range out of bounds: start={start}, end={end}, count={count}")
    if start > end:
        raise ValueError(f"start ({start}) cannot be greater than end ({end})")
    vol_size = vol_path.stat().st_size

    def entry(i: int) -> int:
        base = i * 3
        return u24_from_bytes(data[base:base+3])

    for i in range(start, end + 1):
        cur = entry(i)
        if cur == ABSENT:
            print_func(f"{i}|")
            continue
        # find next valid offset
        next_off = None
        for j in range(i + 1, count):
            v = entry(j)
            if v != ABSENT:
                next_off = v
                break
        total_size = (next_off - cur) if next_off is not None else max(0, vol_size - cur)
        try:
            raw = _extract_text_data(cur, total_size, vol_path)
            end = raw.find(b"\x00")
            if end != -1:
                raw = raw[:end]
            text = raw.decode('latin-1', errors='replace')
            print_func(f"{i}|{text}")
        except Exception:
            # On any error extracting/decoding, print empty text for that index
            print_func(f"{i}|")


def get_view_offset(index: int, viewdir_path: Path) -> int:
    # Back-compat: return only offset
    off, _ = get_view_offset_and_size(index, viewdir_path)
    return off


def main() -> None:
    ap = argparse.ArgumentParser(description="Print 3-byte unsigned integers from VIEWDIR or dump view text")
    ap.add_argument("srcdir", help="Source directory containing VIEWDIR and VOL.0 files")
    ap.add_argument("index", nargs='?', type=int, help="Optional view index to print offset/size or dump data/text")
    ap.add_argument("-o", "--output", help="Output file path (if not specified, prints to stdout)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dump", action="store_true", help="With index, dump text bytes as hex from VOL.0")
    g.add_argument("--text", action="store_true", help="With index, print text decoded from the dumped bytes (latin-1), stopping at NUL")
    g.add_argument("--dump-all", action="store_true", help="With index, dump the entire resource bytes from VOL.0 as hex")
    ap.add_argument("--list-texts", action="store_true", help="List indexes as '<index>|<text>' in range [--start, --end]")
    ap.add_argument("--start", type=int, help="Start index for --list-texts (inclusive)")
    ap.add_argument("--end", type=int, help="End index for --list-texts (inclusive)")
    args = ap.parse_args()

    srcdir = Path(args.srcdir)
    viewdir_path = srcdir / "VIEWDIR"
    vol_path = srcdir / "VOL.0"
    
    # Setup output - either file or stdout
    output_file = None
    if args.output:
        output_path = Path(args.output)
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_file = open(output_path, 'w', encoding='utf-8')
    
    def print_output(text):
        """Print to either the output file or stdout"""
        if output_file:
            print(text, file=output_file)
        else:
            print(text)
    
    try:
        if not viewdir_path.exists():
            raise FileNotFoundError(f"VIEWDIR not found at {viewdir_path}")

        if args.list_texts:
            list_all_view_texts(viewdir_path, vol_path, args.start, args.end, print_output)
            return

        if args.index is not None:
            # For dump modes, use fallback sizing to handle the last entry gracefully
            if args.dump_all or args.dump or args.text:
                off, size = get_view_offset_and_size_with_fallback(args.index, viewdir_path, vol_path)
            else:
                off, size = get_view_offset_and_size(args.index, viewdir_path)

            if args.dump_all:
                print_view_full(off, size, vol_path, print_output)
            elif args.text:
                print_view_text(off, size, vol_path, print_output)
            elif args.dump:
                print_view_bytes(off, size, vol_path, print_output)
            else:
                print_output(f"{off} {size}")
            return

        data = viewdir_path.read_bytes()
        # Iterate in steps of 3 bytes
        n = len(data) // 3
        for i in range(n):
            chunk = data[i * 3 : i * 3 + 3]
            val = u24_from_bytes(chunk)
            print_output(f"{i}:{val}")
    
    finally:
        if output_file:
            output_file.close()


if __name__ == "__main__":
    main()
