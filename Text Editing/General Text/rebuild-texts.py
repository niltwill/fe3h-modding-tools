import struct
import json
import sys

def rebuild_texts_bin(json_path, original_bin_path, output_path):
    # Load edited strings
    with open(json_path, 'r', encoding='utf-8') as f:
        lines = json.load(f)

    with open(original_bin_path, 'rb') as f:
        header = f.read(32)
        header_data = struct.unpack('<IIIIIIII', header)
        val1, val2 = header_data[0], header_data[1]

    if val1 == 1 and val2 == 1:
        # === Format A ===
        text_pointer_length = header_data[3]
        count = header_data[4]

        if len(lines) != count:
            raise ValueError(f"Line count mismatch: expected {count}, got {len(lines)}")

        with open(original_bin_path, 'rb') as f:
            f.seek(32)
            pointers_data = f.read((count + 1) * 4)
            padding_length = text_pointer_length - ((count + 1) * 4)

        text_section = b''
        text_pointers = []
        offset = 0
        for line in lines:
            encoded = line.encode('utf-8') + b'\x00'
            text_pointers.append(offset)
            text_section += encoded
            offset += len(encoded)
        text_pointers.append(offset)

        with open(output_path, 'wb') as f:
            f.write(header)
            f.write(struct.pack(f'<{count + 1}I', *text_pointers))

            if padding_length > 0:
                with open(original_bin_path, 'rb') as orig:
                    orig.seek(32 + (count + 1) * 4)
                    dd_padding = orig.read(padding_length)
                    f.write(dd_padding)

            f.write(text_section)

        print(f"Rebuilt successfully: {output_path}")

    else:
        # === Format B ===
        count = val1
        if len(lines) != count:
            raise ValueError(f"Line count mismatch: expected {count}, got {len(lines)}")

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
            offset_length_pairs.append((offset, len(encoded)-1))  # length without trailing nulls
            data_section += encoded + (b'\x00' * nulls)
            offset += len(encoded) + nulls

        with open(output_path, 'wb') as f:
            f.write(struct.pack('<I', count))  # val1 = count
            for offset, length in offset_length_pairs:
                f.write(struct.pack('<II', offset + 0x04 + count * 8, length))  # adjust offset to point after table
            f.write(data_section)

        print(f"Rebuilt successfully: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("FE3H - Convert JSON text files back to binary (need to specify original binary too)")
        print("Usage: python rebuild-texts.py <edited.json> <original.bin> <output.bin>")
        sys.exit(1)

    json_path = sys.argv[1]
    original_bin_path = sys.argv[2]
    output_path = sys.argv[3]

    rebuild_texts_bin(json_path, original_bin_path, output_path)