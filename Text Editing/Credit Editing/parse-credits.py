import json
import struct
import sys
import os

MAGIC = 0x2963

def parse_credit_bin(bin_path):
    with open(bin_path, "rb") as f:
        data = f.read()

    magic, num_ptrs = struct.unpack_from("<II", data, 0)
    if magic != MAGIC:
        raise ValueError(f"Unexpected magic number: {hex(magic)} (expected {hex(MAGIC)})")

    # Read pointers
    ptrs = list(struct.unpack_from(f"<{num_ptrs}I", data, 8))

    # Extract strings
    lines = []
    for i in range(num_ptrs):
        start = ptrs[i]
        end = ptrs[i + 1] if i + 1 < num_ptrs else len(data)
        raw_text = data[start:end]
        line = raw_text.decode("utf-8", errors="surrogateescape")

        lines.append(line)

    # Write JSON
    out_path = bin_path.replace(".bin", ".json")
    with open(out_path, "w", encoding="utf-8", errors="surrogateescape") as f:
        json.dump(lines, f, indent=2, ensure_ascii=False)

    print(f"Parsed credit file written to: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Use case: common/common/caption/68 - Credit.bin")
        print("Usage: python parse-credits.py <credit_file.bin>")
    else:
        parse_credit_bin(sys.argv[1])
