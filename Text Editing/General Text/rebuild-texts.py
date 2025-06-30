import glob
import json
import os
import struct
import sys

def align16(x):
    return (x + 15) & ~15

def rebuild_format_a(lines, output_path):
    count = len(lines)

    # Encode text and generate pointers
    text_section = b''
    text_pointers = []
    offset = 0
    for line in lines:
        encoded = line.encode('utf-8') + b'\x00'
        text_pointers.append(offset)
        text_section += encoded
        offset += len(encoded)
    text_pointers.append(offset)  # Add final pointer

    # Build pointer table
    pointer_table = struct.pack(f'<{count + 1}I', *text_pointers)
    pointer_section_size = align16(len(pointer_table))
    padding_needed = pointer_section_size - len(pointer_table)
    if padding_needed != 0:
        pointer_table += b'\xDD' * padding_needed

    # Build header: 1, 1, 32, pointer_section_size, count, + 12 bytes of 'EE'
    header = struct.pack('<IIIII', 1, 1, 32, pointer_section_size, count)
    header += b'\xEE' * 12  # 12 bytes

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(pointer_table)
        f.write(text_section)

    print(f"Rebuilt Format A successfully: {output_path}")

def rebuild_format_b(lines, output_path):
    count = len(lines)

    offset = 0
    offset_length_pairs = []
    data_section = b''

    for entry in lines:
        if isinstance(entry, dict):
            text = entry['text']
            nulls = entry.get('nulls', 1)
        else:
            text = entry
            nulls = 0  # fallback

        encoded = text.encode('utf-8')
        offset_length_pairs.append((offset + 4 + count * 8, len(encoded) - 1))  # adjusted offset
        data_section += encoded + (b'\x00' * nulls)
        offset += len(encoded) + nulls

    with open(output_path, 'wb') as f:
        f.write(struct.pack('<I', count))
        for offset_val, length in offset_length_pairs:
            f.write(struct.pack('<II', offset_val, length))
        f.write(data_section)

    print(f"Rebuilt Format B successfully: {output_path}")

def process_file(fmt, json_path, output_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        lines = json.load(f)

    if fmt == 'A':
        rebuild_format_a(lines, output_path)
    elif fmt == 'B':
        rebuild_format_b(lines, output_path)
    else:
        print(f"Invalid format for file {json_path}. Skipped.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("FE3H - Convert JSON text files back to binary")
        print("Usage (single): python rebuild-texts.py <A|B> <input.json> <output.bin>")
        print("Usage (batch):  python rebuild-texts.py <A|B> <folder_or_wildcard/*.json>")
        print()
        print("Format A: narration\\text, talk_castle\\text, talk_event\\text")
        print("Format B: talk_scinario\\text")
        sys.exit(1)

    fmt = sys.argv[1].upper()
    input_patterns = sys.argv[2:]
    expanded_files = []

    for pattern in input_patterns:
        expanded = glob.glob(pattern)
        if not expanded:
            print(f"No matching files for pattern: {pattern}")
        expanded_files.extend(expanded)

    if not expanded_files:
        print("No valid JSON input files found.")
        sys.exit(1)

    for json_path in expanded_files:
        if len(sys.argv) == 4 and len(expanded_files) == 1:
            output_path = sys.argv[3]
        else:
            base_name = os.path.splitext(os.path.basename(json_path))[0]
            output_path = os.path.join(os.path.dirname(json_path), base_name + ".bin")
        process_file(fmt, json_path, output_path)