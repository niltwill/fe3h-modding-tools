import json
import struct
import sys
import os

def read_u32(f):
    return struct.unpack('<I', f.read(4))[0]

def write_u32(f, val):
    f.write(struct.pack('<I', val))

def read_u16(f):
    return struct.unpack('<H', f.read(2))[0]

def write_u16(f, val):
    f.write(struct.pack('<H', val))

def parse_6164_file(filename):
    with open(filename, 'rb') as f:
        # Read Header
        number_of_entries = read_u32(f)
        unknown1 = read_u32(f)
        unknown2 = read_u32(f)
        unknown3 = read_u32(f)

        # Read Entry Blocks
        entries = []
        for i in range(number_of_entries):
            entry_number = read_u16(f)
            unk1 = read_u16(f)
            unk2 = read_u16(f)
            unk3 = read_u16(f)
            entries.append({
                "EntryNumber": entry_number,
                "Unk1": unk1,
                "Unk2": unk2,
                "Unk3": unk3
            })

        return {
            "Header": {
                "NumberOfEntries": number_of_entries,
                "Unknown1": unknown1,
                "Unknown2": unknown2,
                "Unknown3": unknown3
            },
            "Entries": entries
        }

def rebuild_6164_file(json_file, output_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    header = data.get("Header", {})
    entries = data.get("Entries", [])
    entry_count = header.get("NumberOfEntries", -1)

    # Sanity check
    if len(entries) != entry_count:
        print("Warning: Entry count mismatch! Header says {}, but got {} entries."
              .format(header.get("NumberOfEntries"), len(entries)))

    with open(output_file, 'wb') as f:
        # Write Header
        write_u32(f, header.get("NumberOfEntries", 0))
        write_u32(f, header.get("Unknown1", 0))
        write_u32(f, header.get("Unknown2", 0))
        write_u32(f, header.get("Unknown3", 0))

        # Write Entries
        for entry in entries:
            write_u16(f, entry.get("EntryNumber", 0))
            write_u16(f, entry.get("Unk1", 0))
            write_u16(f, entry.get("Unk2", 0))
            write_u16(f, entry.get("Unk3", 0))

        # Add 8-byte padding if needed
        current_size = f.tell()
        padding_needed = (16 - (current_size % 16)) % 16
        if padding_needed:
            f.write(b'\x00' * padding_needed)

def save_to_json(parsed_data, output_filename):
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=2)

def main():
    if len(sys.argv) < 3:
        print("FE3H: IN_CubeStageBaseInfo")
        print("For file: romfs/patch4/nx/event/talk_event/data/IN_CubeStageBaseInfo.bin")
        print("")
        print("Usage:")
        print("  To dump:   python mod-IN_CubeStageBaseInfo.py dump <IN_CubeStageBaseInfo.bin> [output.json]")
        print("  To build:  python mod-IN_CubeStageBaseInfo.py build <input.json> [IN_CubeStageBaseInfo.bin]")
        print("")
        print("Note: The output file is optional, if not given, the input's filename will be used in the same directory")
        return

    mode = sys.argv[1].lower()
    input_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) >= 4 else None

    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        return

    if mode == "dump":
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".json"

        try:
            result = parse_6164_file(input_file)
            save_to_json(result, output_file)
            print(f"Dumped to: {output_file}")
        except Exception as e:
            print(f"Error while dumping: {e}")

    elif mode == "build":
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".bin"

        try:
            rebuild_6164_file(input_file, output_file)
            print(f"Built to: {output_file}")
        except Exception as e:
            print(f"Error while building: {e}")

    else:
        print("Unknown mode. Use 'dump' or 'build'.")

if __name__ == "__main__":
    main()
