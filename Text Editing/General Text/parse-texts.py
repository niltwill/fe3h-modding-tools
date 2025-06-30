import glob
import json
import os
import struct
import sys

def parse_texts_bin(file_path):
    with open(file_path, 'rb') as f:
        # Read entire 32-byte header
        f.seek(0)
        header_data = struct.unpack('<IIIIIIII', f.read(32))
        val1, val2 = header_data[0], header_data[1]

        if val1 == 1 and val2 == 1:
            # Format A
            # For texts here:
            # nx\event\narration\text\
            # nx\event\talk_castle\text\
            # nx\event\talk_event\text\
            text_pointer_length = header_data[3]
            count = header_data[4]

            pointer_format = f'<{count + 1}I'
            text_pointers = struct.unpack(pointer_format, f.read(4 * (count + 1)))

            padding_length = text_pointer_length - ((count + 1) * 4)
            if padding_length > 0:
                f.read(padding_length)

            base_offset = 32 + text_pointer_length
            strings = []

            for i in range(count):
                f.seek(base_offset + text_pointers[i])
                string_bytes = bytearray()
                while True:
                    b = f.read(1)
                    if b == b'\x00' or b == b'':
                        break
                    string_bytes += b
                strings.append(string_bytes.decode('utf-8'))

            return strings

        else:
            # Format B: Offset/Length pairs starting at 0x04
            # For texts here: nx\event\talk_scinario\text\
            entry_count = val1
            f.seek(0x04)
            offset_length_pairs = struct.unpack(f'<{entry_count * 2}I', f.read(4 * entry_count * 2))

            strings = []
            for i in range(entry_count):
                offset = offset_length_pairs[i * 2]
                length = offset_length_pairs[i * 2 + 1]

                # Read the declared string bytes + up to 3 more to check for extra nulls
                f.seek(offset)
                data = f.read(length + 12)  # 12 extra bytes max

                string_data = data[:length + 64]    # to reach everything (hopefully)
                #trailing_data = data[length + 1:]  # check trailing nulls
                nulls = string_data.count(b'\x00')

                # Count trailing nulls (actual null separator bytes)
                """nulls = 0
                for b in trailing_data:
                    if b == 0x00:
                        nulls += 1
                    else:
                        break
                """
                try:
                    s = string_data.decode('utf-8')
                except UnicodeDecodeError:
                    s = string_data.decode('utf-8', errors='replace')

                #print(f"String {i}: {repr(s)} — Nulls after: {nulls}")
                stripped = s.split("\u0000", 1)[0]  # remove the extra text that is not needed
                strings.append({'text': stripped, 'nulls': nulls})

        return strings

def export_to_json(lines, input_file):
    base = os.path.splitext(input_file)[0]
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(lines, f, ensure_ascii=False, indent=2)
    print(f"Exported to {base}.json")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Convert text binary files to JSON")
        print("Usage (single): python parse-texts.py <file.bin>")
        print("Usage (batch):  python parse-texts.py <folder_or_pattern/*.bin>")
        sys.exit(1)

    input_patterns = sys.argv[1:]
    matched_files = []

    for pattern in input_patterns:
        matched = glob.glob(pattern)
        if not matched:
            print(f"No files matched: {pattern}")
        matched_files.extend(matched)

    if not matched_files:
        print("No valid input files found.")
        sys.exit(1)

    for file_path in matched_files:
        try:
            lines = parse_texts_bin(file_path)
            export_to_json(lines, file_path)
        except Exception as e:
            print(f"Failed to process {file_path}: {e}")