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
    
def read_b1(f):
    return struct.unpack('<B', f.read(1))[0]

def write_u16(f, val):
    f.write(struct.pack('<H', val))
    
def write_b1(f, val):
    f.write(struct.pack('<B', val))

def parse_6160_file(filename):
    with open(filename, 'rb') as f:
        # Read Header
        number_of_entries = read_u32(f)
        unknown1 = read_u32(f)
        unknown2 = read_u32(f)
        unknown3 = read_u32(f)

        # Read Entry Blocks
        entries = []
        for i in range(number_of_entries):
            unk1 = read_u16(f)
            unk2 = read_u16(f)
            padding = read_u16(f)
            unk3 = read_u16(f)
            unk_val1 = read_b1(f)
            unk_val2 = read_b1(f)
            unk_val3 = read_b1(f)
            unk_val4 = read_b1(f)
            unk_val5 = read_b1(f)
            unk_val6 = read_b1(f)
            unk_val7 = read_b1(f)
            unk_val8 = read_b1(f)
            unk5 = read_u16(f)
            unk6 = read_u16(f)
            entries.append({
                "Unk1": unk1,
                "Unk2": unk2,
                "Padding": padding,
                "Unk3": unk3,
                "Unk_Value1": unk_val1,
                "Unk_Value2": unk_val2,
                "Unk_Value3": unk_val3,
                "Unk_Value4": unk_val4,
                "Unk_Value5": unk_val5,
                "Unk_Value6": unk_val6,
                "Unk_Value7": unk_val7,
                "Unk_Value8": unk_val8,
                "Unk5": unk5,
                "Unk6": unk6
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

def rebuild_6160_file(json_file, output_file):
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
        
        for entry in entries:
            write_u16(f, entry.get("Unk1", 0))
            write_u16(f, entry.get("Unk2", 0))
            write_u16(f, entry.get("Padding", 0))
            write_u16(f, entry.get("Unk3", 0))
            write_b1(f, entry.get("Unk_Value1", 0))
            write_b1(f, entry.get("Unk_Value2", 0))
            write_b1(f, entry.get("Unk_Value3", 0))
            write_b1(f, entry.get("Unk_Value4", 0))
            write_b1(f, entry.get("Unk_Value5", 0))
            write_b1(f, entry.get("Unk_Value6", 0))
            write_b1(f, entry.get("Unk_Value7", 0))
            write_b1(f, entry.get("Unk_Value8", 0))
            write_u16(f, entry.get("Unk5", 0))
            write_u16(f, entry.get("Unk6", 0))

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
        print("FE3H: 6160")
        print("For file: nx/event/talk_event/data/6160.bin")
        print("")
        print("Usage:")
        print("  To dump:   python mod-6160.py dump <6160.bin> [output.json]")
        print("  To build:  python mod-6160.py build <input.json> [6160.bin]")
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
            result = parse_6160_file(input_file)
            save_to_json(result, output_file)
            print(f"Dumped to: {output_file}")
        except Exception as e:
            print(f"Error while dumping: {e}")

    elif mode == "build":
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".bin"

        try:
            rebuild_6160_file(input_file, output_file)
            print(f"Built to: {output_file}")
        except Exception as e:
            print(f"Error while building: {e}")

    else:
        print("Unknown mode. Use 'dump' or 'build'.")

if __name__ == "__main__":
    main()
