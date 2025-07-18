import os
import sys

HEADER_SIZE = 64

def extract_offset(file_path, number, chunk_size=1048576):  # 1 MB chunk size
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    magic = b"KTSS"
    length = len(magic)
    positions = []

    with open(file_path, 'rb') as f:
        offset = 0
        buffer = b""
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            buffer += chunk
            pos = buffer.find(magic)
            while pos != -1:
                positions.append(offset + pos)
                pos = buffer.find(magic, pos + length)

            offset += len(buffer) - length
            buffer = buffer[-length:]

    if number <= 0 or number > len(positions):
        print(f"Error: Number {number} is out of range. There are only {len(positions)} KTSS numbers in the file.")
        return

    offset = positions[number - 1]
    offset -= HEADER_SIZE
    offset += 8

    with open(file_path, 'rb') as f:
        f.seek(offset)
        link_id_bytes = f.read(4)
        if len(link_id_bytes) < 4:
            print("Error: Could not read 4 bytes for Link ID.")
            return
        link_id = int.from_bytes(link_id_bytes, byteorder='little')

    offset -= 8
    print(f"KTSS offset (with header): {offset}")
    offset += HEADER_SIZE
    print(f"KTSS offset (without header): {offset}")
    print(f"Link ID at KTSS #{number}: {link_id}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python position-ktss.py <file.ktsl2stbin> <ktss_index>")
        sys.exit(1)

    input_file = sys.argv[1]
    try:
        number = int(sys.argv[2])
    except ValueError:
        print("Error: KTSS number must be an integer.")
        sys.exit(1)

    extract_offset(input_file, number)
