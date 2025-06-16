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

def peek_u32(f):
    pos = f.tell()
    val = read_u32(f)
    f.seek(pos)
    return val

def parse_6161_file(filename):
    with open(filename, 'rb') as f:
        # Read Header
        number_of_entries = read_u32(f)
        unknown1 = read_u32(f)
        unknown2 = read_u32(f)
        unknown3 = read_u32(f)

        entries_type1 = []
        entries_type2 = []

        while True:
            # Stop if end of file
            bytes_remaining = f.peek(1)
            if not bytes_remaining:
                break

            pos = f.tell()
            possible_entry_number = peek_u32(f)

            if possible_entry_number == 0xFFFFFFFF:
                # Entry Type 2
                unk1 = read_u32(f)
                unk2 = read_u32(f)
                unk3 = read_u32(f)
                data = struct.unpack('<4I', f.read(16))  # 4 * uint32
                entries_type2.append({
                    "Unk1": unk1,
                    "Unk2": unk2,
                    "Unk3": unk3,
                    "Data": list(data)
                })
            else:
                # Entry Type 1
                entry_number = read_u16(f)
                unk1 = read_u32(f)
                unk2 = read_u32(f)
                padding1 = read_u16(f)
                unk3 = read_u32(f)
                unk4 = read_u32(f)
                unk5 = read_u32(f)
                padding2 = read_u32(f)
                entries_type1.append({
                    "EntryNumber": entry_number,
                    "Unk1": unk1,
                    "Unk2": unk2,
                    "Padding1": padding1,
                    "Unk3": unk3,
                    "Unk4": unk4,
                    "Unk5": unk5,
                    "Padding2": padding2
                })

        return {
            "Header": {
                "NumberOfEntries": number_of_entries,
                "Unknown1": unknown1,
                "Unknown2": unknown2,
                "Unknown3": unknown3
            },
            "EntriesType1": entries_type1,
            "EntriesType2": entries_type2
        }

def rebuild_6161_file(json_file, output_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    header = data.get("Header", {})
    entries_type1 = data.get("EntriesType1", [])
    entries_type2 = data.get("EntriesType2", [])

    total_entries = len(entries_type1) + len(entries_type2)
    if header.get("NumberOfEntries", -1) != total_entries:
        print(f"Warning: Header NumberOfEntries={header.get('NumberOfEntries')} does not match actual count ({total_entries}).")

    with open(output_file, 'wb') as f:
        # Write Header
        write_u32(f, total_entries)
        write_u32(f, header.get("Unknown1", 0))
        write_u32(f, header.get("Unknown2", 0))
        write_u32(f, header.get("Unknown3", 0))

        # Write Entry Type 1
        for entry in entries_type1:
            write_u16(f, entry.get("EntryNumber", 0))
            write_u32(f, entry.get("Unk1", 0))
            write_u32(f, entry.get("Unk2", 0))
            write_u16(f, entry.get("Padding1", 0))
            write_u32(f, entry.get("Unk3", 0))
            write_u32(f, entry.get("Unk4", 0))
            write_u32(f, entry.get("Unk5", 0))
            write_u32(f, entry.get("Padding2", 0))

        # Write Entry Type 2
        for entry in entries_type2:
            write_u32(f, 0xFFFFFFFF)  # entry marker
            write_u32(f, entry.get("Unk2", 0))
            write_u32(f, entry.get("Unk3", 0))
            for val in entry.get("Data", [0, 0, 0, 0]):
                write_u32(f, val)

        # Final 16-byte alignment padding
        current_size = f.tell()
        padding_needed = (16 - (current_size % 16)) % 16
        if padding_needed:
            f.write(b'\x00' * padding_needed)

def save_to_json(parsed_data, output_filename):
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=2)

def main():
    if len(sys.argv) < 3:
        print("FE3H: 6161")
        print("For file: nx/event/talk_event/data/6161.bin")
        print("")
        print("Usage:")
        print("  To dump:   python mod-6161.py dump <6161.bin> [output.json]")
        print("  To build:  python mod-6161.py build <input.json> [6161.bin]")
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
            result = parse_6161_file(input_file)
            save_to_json(result, output_file)
            print(f"Dumped to: {output_file}")
        except Exception as e:
            print(f"Error while dumping: {e}")

    elif mode == "build":
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".bin"

        try:
            rebuild_6161_file(input_file, output_file)
            print(f"Built to: {output_file}")
        except Exception as e:
            print(f"Error while building: {e}")

    else:
        print("Unknown mode. Use 'dump' or 'build'.")

if __name__ == "__main__":
    main()
