import json
import struct
import sys
import os

MAGIC = 0x2963

def write_credits_from_json(json_path):
    with open(json_path, "r", encoding="utf-8", errors="surrogateescape") as f:
        lines = json.load(f)

    ptrs = []
    data = bytearray()
    current_offset = 8 + 4 * len(lines)  # header (8 bytes) + ptrs

    for line in lines:
        ptrs.append(current_offset)
        encoded = line.encode("utf-8", errors="surrogateescape")
        data.extend(encoded)
        current_offset += len(encoded)

    output_path = json_path.replace(".json", ".bin")
    with open(output_path, "wb") as out:
        out.write(struct.pack("<I", MAGIC))
        out.write(struct.pack("<I", len(lines)))
        for ptr in ptrs:
            out.write(struct.pack("<I", ptr))
        out.write(data)

    print(f"Rebuilt credit file written to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Use case: common/common/caption/68 - Credit.bin")
        print("Usage: python rebuild-credits.py <credits_file.json>")
    else:
        write_credits_from_json(sys.argv[1])
