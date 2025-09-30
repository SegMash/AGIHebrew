#!/usr/bin/env python3
"""
Apply object texts from a file to VOL.0 by updating VIEW resource text in-place.

Input file format (UTF-8):
  <index>|<text>

Notes:
- Text is encoded as Windows-1255 and written directly to VOL.0
- Lines without a '|' or with non-numeric index are skipped with a warning.
- Use --dry-run to preview without writing.
- Use --start-index/--end-index to restrict updates to a range of indices.
- Text longer than the original capacity will be rejected to avoid corruption.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ABSENT = 0xFFFFFF


def u24_from_bytes(b: bytes) -> int:
    if len(b) != 3:
        raise ValueError("u24_from_bytes requires exactly 3 bytes")
    return (b[0] << 16) | (b[1] << 8) | b[2]


def get_offset_and_size_with_fallback(index: int, viewdir_path: Path, vol_path: Path) -> tuple[int, int]:
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

    # find next valid offset
    next_off = None
    for j in range(index + 1, count):
        v = entry(j)
        if v != ABSENT:
            next_off = v
            break
    if next_off is not None:
        size = next_off - cur
    else:
        vol_size = vol_path.stat().st_size
        size = max(0, vol_size - cur)
    if size <= 0:
        raise ValueError("computed non-positive resource size")
    return cur, size


def compute_text_payload_region(offset: int, total_size: int, vol_path: Path) -> tuple[int, int, bool]:
    """Return (payload_start, capacity, has_trailing_nul).

    - Reads 2 bytes at offset+7 as big-endian text_offset.
      If > total_size, retry with low byte only (hdr[1]).
    - Text block start = offset + text_offset + 3
    - Skip 2 bytes of (unreliable) length header => payload_start
    - Capacity = total_size - (payload_start - offset)
    - has_trailing_nul is True if the current payload's last byte is 0x00
    """
    with vol_path.open('rb') as f:
        f.seek(offset + 8)
        hdr = f.read(2)
        if len(hdr) != 2:
            raise ValueError("could not read 2-byte text offset at offset+7")
        text_offset = (hdr[1] << 8) | hdr[0]
        if text_offset > total_size:
            text_offset = hdr[1]
            if text_offset > total_size:
                raise ValueError(f"text_offset {text_offset} out of bounds for resource size {total_size}")
        start = offset + text_offset + 3
        if start + 2 > offset + total_size:
            raise ValueError("insufficient data for 2-byte text length")
        payload_start = start + 2
        capacity = total_size - (payload_start - offset)
        if capacity <= 0:
            raise ValueError("no capacity for text payload")

        # Inspect the existing payload tail to see if there is a trailing NUL
        f.seek(payload_start)
        current = f.read(capacity)
        has_trailing_nul = len(current) > 0 and current[-1] == 0
    return payload_start, capacity, has_trailing_nul


def update_view_text(index: int, message: str, srcdir: Path, dry_run: bool = False) -> bool:
    """Update a view text in VOL.0 at the same location, padding if shorter.
    
    Returns True if successful, False if error.
    """
    viewdir_path = srcdir / "VIEWDIR"
    vol_path = srcdir / "VOL.0"
    
    try:
        off, total = get_offset_and_size_with_fallback(index, viewdir_path, vol_path)
        payload_start, capacity, has_nul = compute_text_payload_region(off, total, vol_path)

        try:
            new_bytes = message[::-1].encode('cp1255')  # Windows-1255
        except LookupError:
            print(f"ERROR index {index}: Python does not support cp1255 encoding on this system")
            return False

        # If there is a trailing NUL, reserve one byte at the end for it
        if has_nul and capacity > 0:
            content_cap = capacity - 1
        else:
            content_cap = capacity

        if len(new_bytes) > content_cap:
            print(f"ERROR index {index}: Message too long: {len(new_bytes)} bytes (capacity {content_cap}; total payload {capacity} incl. trailing NUL={has_nul})")
            return False

        # Build the buffer to write
        pad_len = content_cap - len(new_bytes)
        buf = new_bytes + (b" " * pad_len)
        if has_nul and capacity > 0:
            buf += b"\x00"

        if dry_run:
            print(f"Would write {len(buf)} bytes at {payload_start} for index {index} (capacity={capacity}, content_cap={content_cap}, trailing_nul={has_nul})")
            return True

        with vol_path.open('r+b') as f:
            f.seek(payload_start)
            wrote = f.write(buf)
            if wrote != len(buf):
                print(f"ERROR index {index}: Short write: expected {len(buf)} wrote {wrote}")
                return False
        
        print(f"Updated index {index}: {len(buf)} bytes at {payload_start} (message bytes={len(new_bytes)}, padded={pad_len}, trailing_nul={has_nul})")
        return True
        
    except Exception as e:
        print(f"ERROR index {index}: {e}")
        return False


def iter_lines(path: Path):
    # Try UTF-8 first, fall back to Windows-1255 for Hebrew text
    encodings_to_try = ["utf-8", "windows-1255"]
    
    for encoding in encodings_to_try:
        try:
            with path.open("r", encoding=encoding) as f:
                for lineno, raw in enumerate(f, start=1):
                    line = raw.strip("\r\n")
                    if not line:
                        continue
                    parts = line.split("|", 1)
                    if len(parts) != 2:
                        yield lineno, None, None, f"missing '|' separator"
                        continue
                    idx_str, msg = parts[0].strip(), parts[1].lstrip()
                    if not idx_str.isdigit():
                        yield lineno, None, None, f"non-numeric index '{idx_str}'"
                        continue
                    yield lineno, int(idx_str), msg, None
            return  # Successfully read with this encoding
        except UnicodeDecodeError:
            continue  # Try next encoding
    
    # If all encodings failed, raise an error
    raise UnicodeDecodeError(f"Could not decode file {path} with any of the attempted encodings: {encodings_to_try}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Apply object texts to VOL.0 by updating VIEW resources in-place")
    ap.add_argument("srcdir", help="Source directory containing VIEWDIR and VOL.0 files")
    ap.add_argument("--file", type=Path, help="Input file path (required)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write; just report what would happen")
    ap.add_argument("--start-index", type=int, help="Only process entries with index >= this value")
    ap.add_argument("--end-index", type=int, help="Only process entries with index <= this value")
    args = ap.parse_args()

    if not args.file:
        raise SystemExit("Error: --file argument is required")
    
    srcdir = Path(args.srcdir)
    if not srcdir.exists():
        raise SystemExit(f"Source directory not found: {srcdir}")
    
    path = args.file
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")

    total = 0
    ok = 0
    skipped = 0
    for lineno, idx, msg, err in iter_lines(path):
        if err is not None:
            print(f"WARN line {lineno}: {err}")
            skipped += 1
            continue
        if args.start_index is not None and idx < args.start_index:
            continue
        if args.end_index is not None and idx > args.end_index:
            continue

        total += 1
        # Reverse the message before inserting (right-to-left storage expectation)
        rev_msg = msg[::-1]
        
        success = update_view_text(idx, rev_msg, srcdir, args.dry_run)
        if success:
            ok += 1

    print(f"Done. processed={total}, ok={ok}, skipped={skipped}")


if __name__ == "__main__":
    main()
