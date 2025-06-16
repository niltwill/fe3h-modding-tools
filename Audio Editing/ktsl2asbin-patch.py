import sys
import re
import struct

def parse_info2_txt(txt_path):
    sections = {}
    current_id = None

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Start of a new section
            match_header = re.match(r"\[Info2\s+#(\d+)]", line)
            if match_header:
                current_id = int(match_header.group(1))
                sections[current_id] = []
                continue

            # Match lines like: sample_rate (51704): 48000
            match_field = re.match(r"(.+?)\s+\((\d+)\):\s+(-?\d+)", line)
            if match_field and current_id is not None:
                field_name = match_field.group(1).strip()
                offset = int(match_field.group(2))
                value = int(match_field.group(3))
                sections[current_id].append((field_name, offset, value))

    return sections

def apply_patches(bin_path, output_path, patches, index_filter=None):
    with open(bin_path, "rb") as f:
        data = bytearray(f.read())

    count = 0
    for section_id, fields in patches.items():
        if index_filter is not None and section_id != index_filter:
            continue
        for field_name, offset, value in fields:
            if offset + 4 > len(data):
                print(f"Warning: Offset {offset} out of bounds, skipping {field_name}")
                continue

            # Convert placeholders
            if field_name == "loop_start" and value == -1:
                value = 0xFFFFFFFF

            unsigned_fields = {
                "link_id", "ktss_offset", "ktss_size", "sample_rate",
                "sample_count", "loop_start", "channel_count", "transition_related"
            }

            fmt = "<I" if field_name in unsigned_fields or value >= 0 else "<i"

            try:
                data[offset:offset+4] = struct.pack(fmt, value)
                print(f"Patching {field_name} at offset {offset} with value {value}")
                count += 1
            except struct.error:
                print(f"ERROR: Value {value} at offset {offset} too large for format {fmt}, skipping.")

    # Update total file size at offsets 24 and 28
    final_size = len(data)
    size_bytes = struct.pack("<I", final_size)

    data[24:28] = size_bytes  # First size field
    data[28:32] = size_bytes  # Second size field
    print(f"Updated header file size at offsets 24 and 28 with {final_size} bytes.")

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"\nPatched {count} values.")
    if index_filter is not None:
        print(f"Only modified [Info2 #{index_filter}]")


# === MAIN ===
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ktsl2asbin-patch.py <info2_dump.txt> <input.ktsl2asbin> [index]")
        sys.exit(1)

    txt_path = sys.argv[1]
    bin_path = sys.argv[2]
    index = int(sys.argv[3]) if len(sys.argv) > 3 else None

    output_path = bin_path.replace(".ktsl2asbin", "_patched.ktsl2asbin")

    patches = parse_info2_txt(txt_path)
    apply_patches(bin_path, output_path, patches, index_filter=index)
    