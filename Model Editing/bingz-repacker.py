import os
import struct
import sys

def repack_sections(input_dir, original_file, output_file_path):
    """
    Repacks section files from a folder back into a .bin file, using the 
    original file to determine the exact entry count and header behavior.
    """
    if not os.path.exists(original_file):
        print(f"Error: Original file '{original_file}' not found.")
        return

    # Read the original file to get the exact entry count
    with open(original_file, 'rb') as f:
        entry_count_data = f.read(4)
        original_entry_count = struct.unpack('<I', entry_count_data)[0]

    entry_count = original_entry_count
    print(f"Original entry count: {entry_count}")

    # Find all section files in the directory
    section_files = {}
    if not os.path.exists(input_dir):
        print(f"Error: Input folder '{input_dir}' not found.")
        return

    for filename in os.listdir(input_dir):
        if filename.startswith('section_'):
            parts = filename[len('section_'):].split('.', 1)
            if parts[0].isdigit():
                section_id = int(parts[0])
                section_files[section_id] = filename

    # Read all section data
    sections = []
    for i in range(entry_count):
        if i in section_files:
            filepath = os.path.join(input_dir, section_files[i])
            with open(filepath, 'rb') as f:
                data = f.read()
            sections.append(data)
            print(f"  Section {i:2d}: {section_files[i]} ({len(data)} bytes)")
        else:
            # Preserve empty sections
            sections.append(b'')
            print(f"  Section {i:2d}: (empty)")

    # Calculate pointers
    # Empty sections point to the current stream offset (the start of the next valid section)
    pointers = []
    sizes = []

    # Header: 4 bytes (entry_count) + entry_count * 8 bytes
    current_offset = 4 + entry_count * 8

    for i, data in enumerate(sections):
        pointers.append(current_offset)
        sizes.append(len(data))
        current_offset += len(data)

    # 5. Write the output file
    with open(output_file_path, 'wb') as f:
        # Write entry count
        f.write(struct.pack('<I', entry_count))

        # Write header entries: (pointer, size) for each section
        for i in range(entry_count):
            f.write(struct.pack('<II', pointers[i], sizes[i]))

        # Write section data in order
        for data in sections:
            if data:
                f.write(data)

    print(f"\nRepacking complete.")
    print(f"  Output: {output_file_path}")
    print(f"  Total size: {current_offset} bytes (0x{current_offset:08X})")

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        input_folder = sys.argv[1]
        original_file = sys.argv[2]

        if len(sys.argv) >= 4:
            output_file = sys.argv[3]
        else:
            # Default output matches original filename
            output_file = os.path.basename(original_file)
            print(f"No output file provided. Using: {output_file}")

        repack_sections(input_folder, original_file, output_file)
    else:
        print("Usage: python bingz-repacker.py <input_folder> <original_file> [output_file]")
