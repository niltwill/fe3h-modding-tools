import os
import sys

HEADER_SIZE = 64

def extract_ktsl2stbin(file_path, output_dir="output_ktsl2stbin"):
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    magic = b"KTSS"
    length = len(magic)

    with open(file_path, 'rb') as f:
        data = f.read()

    # Find all occurrences of "KTSS"
    positions = []
    pos = data.find(magic)
    while pos != -1:
        positions.append(pos)
        pos = data.find(magic, pos + length)

    # Extract and save chunks between each "KTSS" magic header
    for i in range(len(positions) - 1):
        start = positions[i]
        end = positions[i + 1]
        chunk = data[start:end-HEADER_SIZE] # header size must be removed

        output_filename = os.path.join(output_dir, f"{i+1}.ktss")
        with open(output_filename, 'wb') as out_file:
            out_file.write(chunk)
        print(f"Extracted: {output_filename}")

    # Handle the last chunk (from the last "KTSS" to the end of the file)
    if positions:
        last_chunk = data[positions[-1]:]
        output_filename = os.path.join(output_dir, f"{len(positions)}.ktss")
        with open(output_filename, 'wb') as out_file:
            out_file.write(last_chunk)
        print(f"Extracted: {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("FE3H - Extracts KTSS audio files from ktsl2stbin files")
        print("Usage: python extract-ktsl2stbin.py <file_path>")
        sys.exit(1)

    input_file = sys.argv[1]
    extr_dir = os.path.splitext(input_file)[0]
    extract_ktsl2stbin(input_file, extr_dir)
