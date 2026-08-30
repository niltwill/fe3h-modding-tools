#!/usr/bin/env python3
"""
captions.py - FE3H caption file parser and rebuilder
Caption files live at: common/common/caption/
E.g.: 29336-29441, 29830-30013 (English)

Usage:
  python captions.py dump <file.bin>   - export to <file.json>
  python captions.py build <file.json> - rebuild to <file.bin>
                                         (overwrites; back up first)
"""

import json
import struct
import sys
from pathlib import Path

MAGIC = 0x2962

def _align4(n: int) -> int:
    """Round n up to the next multiple of 4."""
    return (n + 3) & ~3


def _block_size(text: str) -> int:
    """Byte size of one entry block, 4-byte aligned."""
    # 8 bytes timing + encoded text + 1 null byte, padded to 4-byte boundary
    return _align4(8 + len(text.encode("utf-8")) + 1)


def dump(bin_path: Path) -> None:
    data = bin_path.read_bytes()

    magic = struct.unpack_from("<I", data, 0)[0]
    if magic != MAGIC:
        sys.exit(f"Not a caption file (magic 0x{magic:X}, expected 0x{MAGIC:X})")

    count = struct.unpack_from("<I", data, 4)[0]
    ptrs = [struct.unpack_from("<I", data, 8 + i * 4)[0] for i in range(count)]

    entries = []
    for i, ptr in enumerate(ptrs):
        start_time = struct.unpack_from("<f", data, ptr)[0]
        duration = struct.unpack_from("<f", data, ptr + 4)[0]

        # Read until null - don't rely on block boundaries
        text_start = ptr + 8
        null_pos = data.index(b"\x00", text_start)
        text = data[text_start:null_pos].decode("utf-8", errors="replace")

        entries.append({
            "index": i,
            "start_time": round(start_time, 6),
            "duration": round(duration, 6),
            "text": text,
        })

    json_path = bin_path.with_suffix(".json")
    json_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Exported {len(entries)} entries -> {json_path}")


def build(json_path: Path) -> None:
    entries = json.loads(json_path.read_text(encoding="utf-8"))

    # Compute fresh pointer table
    header_size = 8 + 4 * len(entries)          # magic + count + ptr table
    ptrs  = []
    offset = header_size
    for entry in entries:
        ptrs.append(offset)
        offset += _block_size(entry["text"])

    # Write
    buf = bytearray()
    buf += struct.pack("<I", MAGIC)
    buf += struct.pack("<I", len(entries))
    for ptr in ptrs:
        buf += struct.pack("<I", ptr)

    for i, entry in enumerate(entries):
        text_bytes = entry["text"].encode("utf-8")
        block_size = _block_size(entry["text"])
        block = bytearray(block_size)          # zero-filled (handles all padding)
        struct.pack_into("<f", block, 0, float(entry["start_time"]))
        struct.pack_into("<f", block, 4, float(entry["duration"]))
        block[8 : 8 + len(text_bytes)] = text_bytes
        # null terminator is already 0x00 from bytearray
        buf += block

    bin_path = json_path.with_suffix(".bin")
    bin_path.write_bytes(bytes(buf))
    print(f"Rebuilt {len(entries)} entries -> {bin_path}")

    # Sanity check: verify all pointers land on timing data we can re-parse
    _verify(bytes(buf), entries)


def _verify(data: bytes, original_entries: list) -> None:
    count = struct.unpack_from("<I", data, 4)[0]
    ptrs  = [struct.unpack_from("<I", data, 8 + i * 4)[0] for i in range(count)]
    ok = True
    for i, (ptr, orig) in enumerate(zip(ptrs, original_entries)):
        null_pos = data.index(b"\x00", ptr + 8)
        text = data[ptr + 8 : null_pos].decode("utf-8", errors="replace")
        if text != orig["text"]:
            print(f"  MISMATCH entry {i}: {repr(text)} ≠ {repr(orig['text'])}")
            ok = False
    if ok:
        print(f"Verification passed ({count} entries round-tripped correctly).")


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in ("dump", "build"):
        print(__doc__)
        sys.exit(1)

    cmd  = sys.argv[1]
    path = Path(sys.argv[2])

    if not path.exists():
        sys.exit(f"File not found: {path}")

    if cmd == "dump":
        if path.suffix.lower() != ".bin":
            sys.exit("dump expects a .bin file")
        dump(path)
    else:
        if path.suffix.lower() != ".json":
            sys.exit("build expects a .json file")
        build(path)


if __name__ == "__main__":
    main()
