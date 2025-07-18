import os
import sys
from struct import pack

HEADER_SIZE = 64
MAGIC = b"KTSS"

def find_ktss_offsets(file_path, chunk_size=1048576):
    """Scan the file for all KTSS magic positions."""
    positions = []
    length = len(MAGIC)

    with open(file_path, 'rb') as f:
        offset = 0
        buffer = b""
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            buffer += chunk
            pos = buffer.find(MAGIC)
            while pos != -1:
                positions.append(offset + pos)
                pos = buffer.find(MAGIC, pos + length)
            offset += len(buffer) - length
            buffer = buffer[-length:]  # keep tail in case MAGIC is split

    return positions

def copy_ktss_chunk(file_path, index):
    positions = find_ktss_offsets(file_path)
    total_chunks = len(positions)

    if index <= 0 or index > total_chunks:
        print(f"Error: Index {index} is invalid. Found {total_chunks} KTSS chunks.")
        return

    with open(file_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

    start_offset = positions[index - 1] - HEADER_SIZE

    # Determine end offset
    if index < total_chunks:
        end_offset = positions[index] - HEADER_SIZE
    else:
        end_offset = file_size  # last chunk goes to EOF

    with open(file_path, 'rb') as f:
        f.seek(start_offset)
        chunk_data = f.read(end_offset - start_offset)

    with open(file_path, 'ab') as f:
        f.write(chunk_data)

    print(f"KTSS chunk #{index} copied to EOF. Bytes [{start_offset}:{end_offset}]")
    
    # === Update file size fields ===
    with open(file_path, "rb") as f:
        data = bytearray(f.read())

    final_size = len(data)
    size_bytes = pack("<I", final_size)

    data[24:28] = size_bytes
    data[28:32] = size_bytes
    print(f"Updated header file size at offsets 24 and 28 with {final_size} bytes.")

    with open(file_path, "wb") as f:
        f.write(data)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python copy_ktsl2stbin_chunk.py <file.ktsl2stbin> <ktss_index>")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        index = int(sys.argv[2])
    except ValueError:
        print("Error: KTSS index must be an integer.")
        sys.exit(1)

    copy_ktss_chunk(file_path, index)
