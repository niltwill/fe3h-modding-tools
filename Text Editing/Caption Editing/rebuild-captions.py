import json
import struct
import sys
import os

def write_captions_from_json(json_path):
    bin_path = json_path.replace(".json", ".bin")
    original_bin_path = json_path.replace(".json", "-original.bin")

    # Load the JSON file
    with open(json_path, "r", encoding="utf-8") as f:
        captions = json.load(f)

    # Load the original .bin file to get pointer table
    if not os.path.exists(original_bin_path):
        print(f"Error: Cannot find original binary file at '{original_bin_path}'")
        return

    with open(original_bin_path, "rb") as f:
        f.seek(0)
        magic = struct.unpack("<I", f.read(4))[0]
        if magic != 0x2962:
            raise ValueError("Invalid magic number in original binary.")

        count = struct.unpack("<I", f.read(4))[0]
        ptr_table = [struct.unpack("<I", f.read(4))[0] for _ in range(count)]

        # Calculate expected block sizes from ptr differences
        f.seek(0, 2)
        file_size = f.tell()
        expected_sizes = []
        for i in range(count):
            start = ptr_table[i]
            end = ptr_table[i + 1] if i + 1 < count else file_size
            expected_sizes.append(end - start)

    # Now rebuild using exact sizes
    rebuilt_blocks = []
    ptrs = []
    current_offset = 8 + 4 * count  # header size

    for i, entry in enumerate(captions):
        start_time = float(entry["start_time"])
        duration = float(entry["duration"])
        text = entry["text"]

        block = bytearray()
        block += struct.pack("<f", start_time)
        block += struct.pack("<f", duration)
        block += text.encode("utf-8") + b'\x00'

        needed_size = expected_sizes[i]
        padding = needed_size - len(block)

        if padding < 0:
            raise ValueError(f"Entry {i} is too large by {-padding} bytes.")

        block += b'\x00' * padding

        ptrs.append(current_offset)
        rebuilt_blocks.append(block)
        current_offset += len(block)

    # Write new binary file
    with open(bin_path, "wb") as f:
        f.write(struct.pack("<I", 0x2962))  # magic
        f.write(struct.pack("<I", len(captions)))  # count
        for ptr in ptrs:
            f.write(struct.pack("<I", ptr))
        for block in rebuilt_blocks:
            f.write(block)

    print(f"Rebuilt caption file written to: {bin_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Caption files for cutscenes, at: common/common/caption/")
        print("E.g.: 29336-29441, 29830-30013 (English)")
        print("Usage: python rebuild-captions.py <caption_file.json>")
        print("Make sure you also have the original BIN file saved as <caption_file>-original.bin")
        print("This does NOT support adding new entries or removing any, just for corrections/edits.")
    else:
        write_captions_from_json(sys.argv[1])