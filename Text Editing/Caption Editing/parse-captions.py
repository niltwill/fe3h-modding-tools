import json
import struct
import sys

def read_float(data, offset):
    return struct.unpack_from('<f', data, offset)[0]

def read_uint32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

def parse_captions(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    offset = 0
    magic = read_uint32(data, offset)
    offset += 4

    if magic != 0x2962:
        print(f"Invalid magic number: 0x{magic:X}")
        return

    ptr_count = read_uint32(data, offset)
    offset += 4

    ptr_table = []
    for _ in range(ptr_count):
        ptr = read_uint32(data, offset)
        ptr_table.append(ptr)
        offset += 4

    captions = []

    for i, ptr in enumerate(ptr_table):
        start_time = read_float(data, ptr)
        duration = read_float(data, ptr + 4)

        text_start = ptr + 8
        text_end = ptr_table[i + 1] if i + 1 < len(ptr_table) else len(data)
        text_bytes = data[text_start:text_end]
        text = text_bytes.split(b'\x00')[0].decode('utf-8', errors='replace')

        captions.append({
            "index": i,
            "start_time": round(start_time, 3),
            "duration": round(duration, 3),
            "text": text
        })

    json_path = file_path.replace(".bin", ".json")
    with open(json_path, "w", encoding="utf-8") as out_file:
        json.dump(captions, out_file, indent=2, ensure_ascii=False)

    print(f"Exported {len(captions)} captions to: {json_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Caption files for cutscenes, at: common/common/caption/")
        print("E.g.: 29336-29441, 29830-30013 (English)")
        print("Usage: python parse_captions.py <caption_file.bin>")
    else:
        parse_captions(sys.argv[1])
