import json
import math
import os
import struct
import sys

ENTRY_SIZE = 0x18

def float_from_binary(value):
    """Convert binary float value to JSON representation, handling NaN case"""
    # Check if the raw bytes represent 0xFFFFFFFF (special NaN pattern)
    raw_bytes = struct.pack('<f', value)
    if raw_bytes == b'\xFF\xFF\xFF\xFF':
        return "NaN_FFFF"
    elif math.isnan(value):
        return "NaN"
    return value

def float_to_binary(value):
    """Convert JSON value to binary float, handling NaN cases"""
    if value == "NaN_FFFF":
        # Return the specific 0xFFFFFFFF pattern
        return struct.unpack('<f', b'\xFF\xFF\xFF\xFF')[0]
    elif value == "NaN" or (isinstance(value, float) and math.isnan(value)):
        return float('nan')
    return float(value)

def parse_bai_file(filename):

    if filename.strip().lower().endswith(".bai"):
        print("Input file must have .bai extension, not .bsi!")
        exit(1)

    with open(filename, "rb") as f:
        data = f.read()

    result = {}
    offset = 0

    # Header (12 bytes)
    header_fields = struct.unpack_from("<3I", data, offset)
    result["Header"] = {
        "Header": header_fields[0],
        "UnkPointer1": header_fields[1],
        "UnkPointer2": header_fields[2],
    }
    offset += 12

    # PTR Table (3x 4 bytes = 12 bytes)
    ptr_table = struct.unpack_from("<3I", data, offset)
    result["RelativeOffsets"] = [{"offset": hex(o)} for o in ptr_table]
    offset += 12

    # Check if all pointers are 0x00 - indicates single route structure
    if all(ptr == 0 for ptr in ptr_table):
        # Single route mode - process all data from offset 0x18 to EOF as one route
        total_data_size = len(data) - 0x18
        total_entries = total_data_size // ENTRY_SIZE
        remaining_bytes = total_data_size % ENTRY_SIZE

        route_data = []
        for j in range(total_entries):
            base = 0x18 + j * ENTRY_SIZE
            chunk = struct.unpack_from("<HHffH10s", data, base)
            character = {
                "CharacterID": chunk[0],
                "Padding": chunk[1],
                "Coord1": float_from_binary(chunk[2]),
                "Coord2": float_from_binary(chunk[3]),
                "RoomID": chunk[4],
                "UnknownBytes": list(chunk[5]),
            }
            route_data.append(character)

        # Parse any remaining trailing bytes after the last entry
        trailing_data = []
        if remaining_bytes > 0:
            trailing_offset = 0x18 + total_entries * ENTRY_SIZE
            trailing_bytes = struct.unpack_from(f"<{remaining_bytes}B", data, trailing_offset)
            trailing_data = list(trailing_bytes)

        result["Routes"] = [route_data]  # Single route in array
        result["RouteTrailingData"] = [trailing_data]  # Store trailing bytes
        result["SingleRouteMode"] = True
    else:
        # Normal three-route mode
        total_entry_count = (len(data) - 0x18) // ENTRY_SIZE
        entries_per_route = total_entry_count // 3

        characters_by_route = []
        route_trailing_data = []

        for i in range(3):
            route_offset = ptr_table[i] + 24
            route_data = []
            for j in range(entries_per_route):
                base = route_offset + j * ENTRY_SIZE
                chunk = struct.unpack_from("<HHffH10s", data, base)
                character = {
                    "CharacterID": chunk[0],
                    "Padding": chunk[1],
                    "Coord1": float_from_binary(chunk[2]),
                    "Coord2": float_from_binary(chunk[3]),
                    "RoomID": chunk[4],
                    "UnknownBytes": list(chunk[5]),
                }
                route_data.append(character)
            characters_by_route.append(route_data)

            # Parse the 20 trailing bytes after this route block
            trailing_offset = route_offset + entries_per_route * ENTRY_SIZE
            trailing_bytes = struct.unpack_from("<20B", data, trailing_offset)
            route_trailing_data.append(list(trailing_bytes))

        result["Routes"] = characters_by_route
        result["RouteTrailingData"] = route_trailing_data
        result["SingleRouteMode"] = False
    return result


def repack_to_bai(json_file, output_file=None):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    header = data["Header"]
    ptr_table = [int(entry["offset"], 16) for entry in data["RelativeOffsets"]]
    routes = data["Routes"]
    route_trailing_data = data.get("RouteTrailingData", [[], [], []])  # Default to empty if missing
    single_route_mode = data.get("SingleRouteMode", False)

    if single_route_mode:
        # Single route mode - calculate buffer size from route entries plus any trailing data
        total_entries = len(routes[0])
        trailing_bytes_count = len(route_trailing_data[0]) if route_trailing_data and route_trailing_data[0] else 0
        buffer_size = 0x18 + total_entries * ENTRY_SIZE + trailing_bytes_count
    else:
        # Normal three-route mode - calculate buffer size accounting for 20 bytes after each route block
        entries_per_route = len(routes[0])
        assert all(len(route) == entries_per_route for route in routes), "Mismatched route entry counts."

        max_end = 0
        for i in range(3):
            base_offset = ptr_table[i] + 24
            end_offset = base_offset + entries_per_route * ENTRY_SIZE + 20  # Add 20 bytes for trailing data
            if end_offset > max_end:
                max_end = end_offset
        buffer_size = max_end

    buffer = bytearray(buffer_size)

    # Write Header
    struct.pack_into("<3I", buffer, 0, header["Header"], header["UnkPointer1"], header["UnkPointer2"])

    # Write PTR Table
    for i in range(3):
        struct.pack_into("<I", buffer, 0x0C + i * 4, ptr_table[i])

    if single_route_mode:
        # Single route mode - write all entries sequentially from offset 0x18
        for j, entry in enumerate(routes[0]):
            off = 0x18 + j * ENTRY_SIZE
            unknown_bytes = bytes(entry["UnknownBytes"])
            if len(unknown_bytes) != 10:
                raise ValueError(f"Invalid UnknownBytes length at index {j}")
            struct.pack_into("<HHffH10s", buffer, off,
                entry["CharacterID"],
                entry["Padding"],
                float_to_binary(entry["Coord1"]),
                float_to_binary(entry["Coord2"]),
                entry["RoomID"],
                unknown_bytes
            )

        # Write any trailing data after the last entry
        if route_trailing_data and route_trailing_data[0]:
            trailing_offset = 0x18 + len(routes[0]) * ENTRY_SIZE
            trailing_bytes = bytes(route_trailing_data[0])
            for i, byte_val in enumerate(trailing_bytes):
                struct.pack_into("<B", buffer, trailing_offset + i, byte_val)
    else:
        # Normal three-route mode - write routes and their trailing data
        for i in range(3):
            base_offset = ptr_table[i] + 24
            # Write route entries
            for j, entry in enumerate(routes[i]):
                off = base_offset + j * ENTRY_SIZE
                unknown_bytes = bytes(entry["UnknownBytes"])
                if len(unknown_bytes) != 10:
                    raise ValueError(f"Invalid UnknownBytes length at route {i}, index {j}")
                struct.pack_into("<HHffH10s", buffer, off,
                    entry["CharacterID"],
                    entry["Padding"],
                    float_to_binary(entry["Coord1"]),
                    float_to_binary(entry["Coord2"]),
                    entry["RoomID"],
                    unknown_bytes
                )

            # Write trailing 20 bytes for this route
            if i < len(route_trailing_data) and route_trailing_data[i]:
                trailing_offset = base_offset + entries_per_route * ENTRY_SIZE
                trailing_bytes = bytes(route_trailing_data[i])
                if len(trailing_bytes) != 20:
                    raise ValueError(f"Invalid trailing data length for route {i}: expected 20, got {len(trailing_bytes)}")
                struct.pack_into("<20B", buffer, trailing_offset, *trailing_bytes)

    if not output_file:
        output_file = os.path.splitext(json_file)[0] + "_repacked.bai"

    with open(output_file, "wb") as f:
        f.write(buffer)

    print(f"Repacked: {output_file}")


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python monasterySpawnData_bai.py dump <input.bai>")
        print("  python monasterySpawnData_bai.py repack <input.json>")
        print("  [common\scenario\castle\*.bai]")
        return

    mode = sys.argv[1].lower()
    input_file = sys.argv[2]

    if mode == "dump":
        parsed_data = parse_bai_file(input_file)
        output_file = os.path.splitext(input_file)[0] + ".json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=4)
        print(f"Dumped: {output_file}")

    elif mode == "repack":
        repack_to_bai(input_file)

    else:
        print(f"Unknown mode: {mode}")
        print("Use 'dump' or 'repack'.")

if __name__ == "__main__":
    main()