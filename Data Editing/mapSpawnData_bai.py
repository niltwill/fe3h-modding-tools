import json
import os
import re
import struct
import sys

ENTRY_SIZE = 44        # 0x2c bytes per CharacterBlock
FILE_HEADER_SIZE = 24  # 6 uint32s: 3 header + 3 pointers

# Struct format for a single CharacterBlock
ENTRY_FORMAT = "<10H8Bb11BI"


def load_enums(filepaths):
    enums = {}
    for filepath in filepaths:
        if not os.path.exists(filepath):
            print(f"Warning: Enum file {filepath} not found. Values will be raw integers.")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        for match in re.finditer(r'enum<\w+>\s+(\w+)\s*\{(.*?)\}', content, re.DOTALL):
            enum_name = match.group(1)
            enum_body = match.group(2)

            name_to_val = {}
            val_to_name = {}
            current_val = 0

            for line in enum_body.split('\n'):
                line = line.split('//')[0].strip()
                if not line:
                    continue
                line = line.strip(',;')

                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue

                    if '=' in part:
                        name, val = part.split('=', 1)
                        name = name.strip()
                        val = val.strip()
                        if val.startswith('0x'):
                            current_val = int(val, 16)
                        else:
                            try:
                                current_val = int(val)
                            except ValueError:
                                continue
                        name_to_val[name] = current_val
                        val_to_name[current_val] = name
                        current_val += 1
                    else:
                        name = part
                        name_to_val[name] = current_val
                        val_to_name[current_val] = name
                        current_val += 1

            enums[enum_name] = {
                "name_to_val": name_to_val,
                "val_to_name": val_to_name
            }
    return enums

def get_enum_name(enums, enum_name, val):
    if enum_name in enums and val in enums[enum_name]["val_to_name"]:
        return enums[enum_name]["val_to_name"][val]
    return val

def get_enum_val(enums, enum_name, name):
    if isinstance(name, int):
        return name
    if enum_name in enums and name in enums[enum_name]["name_to_val"]:
        return enums[enum_name]["name_to_val"][name]
    try:
        return int(name)
    except:
        return 0


def parse_bai_file(filename):
    with open(filename, "rb") as f:
        data = f.read()

    enums = load_enums(["3H_BaiArtsEnums.txt", "3H_BaiEnums.txt"])
    result = {
        "OriginalFileSize": len(data),
        "RouteSizes": [],
        "RouteTails": []  # hex strings of trailing bytes after last full entry
    }

    if len(data) < FILE_HEADER_SIZE:
        raise ValueError("File too small to be a valid BAI file.")

    h = struct.unpack_from("<6I", data, 0)
    result["Header"] = {
        "Header": h[0],
        "UnkPointer1": h[1],
        "UnkPointer2": h[2],
        "OriginalPtrs": [h[3], h[4], h[5]]
    }
    ptr_table = [h[3], h[4], h[5]]

    routes = []

    # Single route mode (all pointers zero)
    if all(p == 0 for p in ptr_table):
        result["SingleRouteMode"] = True
        start = FILE_HEADER_SIZE
        end = len(data)
        route_size = end - start
        num_entries = route_size // ENTRY_SIZE

        route_data = []
        for j in range(num_entries):
            base = start + j * ENTRY_SIZE
            fields = struct.unpack_from(ENTRY_FORMAT, data, base)
            entry = parse_entry(fields, enums)
            route_data.append(entry)
        routes.append(route_data)
        result["RouteSizes"].append(route_size)

        # Store trailing bytes
        tail_start = start + num_entries * ENTRY_SIZE
        tail = data[tail_start:end]
        result["RouteTails"].append(tail.hex() if tail else "")
    else:
        result["SingleRouteMode"] = False
        for i in range(3):
            # Pointers are relative to the end of the 24-byte file header
            start = FILE_HEADER_SIZE + ptr_table[i]
            if i < 2:
                end = FILE_HEADER_SIZE + ptr_table[i+1]
            else:
                end = len(data)

            route_size = end - start
            num_entries = route_size // ENTRY_SIZE

            route_data = []
            for j in range(num_entries):
                base = start + j * ENTRY_SIZE
                fields = struct.unpack_from(ENTRY_FORMAT, data, base)
                entry = parse_entry(fields, enums)
                route_data.append(entry)
            routes.append(route_data)
            result["RouteSizes"].append(route_size)

            # Store trailing bytes (partial entry or padding)
            tail_start = start + num_entries * ENTRY_SIZE
            tail = data[tail_start:end]
            result["RouteTails"].append(tail.hex() if tail else "")

    result["Routes"] = routes
    return result

def parse_entry(fields, enums):
    return {
        "CharacterID": get_enum_name(enums, "CharID", fields[0]),
        "unknown": fields[1],
        "ClassID": get_enum_name(enums, "Class", fields[2]),
        "Weapons": {
            "Item1": get_enum_name(enums, "ItemsBai", fields[3]),
            "Item2": get_enum_name(enums, "ItemsBai", fields[4]),
            "Item3": get_enum_name(enums, "ItemsBai", fields[5]),
            "Item4": get_enum_name(enums, "ItemsBai", fields[6]),
            "Item5": get_enum_name(enums, "ItemsBai", fields[7]),
            "Item6": get_enum_name(enums, "ItemsBai", fields[8]),
            "ItemFlags": get_enum_name(enums, "DroppableItem", fields[9]),
        },
        "Skills": {
            "Ability1": get_enum_name(enums, "AbilityID", fields[10]),
            "Ability2": get_enum_name(enums, "AbilityID", fields[11]),
            "Ability3": get_enum_name(enums, "AbilityID", fields[12]),
            "Ability4": get_enum_name(enums, "AbilityID", fields[13]),
            "Ability5": get_enum_name(enums, "AbilityID", fields[14]),
        },
        "X": fields[15],
        "Y": fields[16],
        "Rotation": get_enum_name(enums, "Rotation", fields[17]),
        "FixedLevel": fields[18],
        "Allegiance": get_enum_name(enums, "Team", fields[19]),
        "SpawnType": get_enum_name(enums, "ScriptSpawn", fields[20]),
        "CharacterFlags": get_enum_name(enums, "MovementFlags", fields[21]),
        "BattallionFlag": get_enum_name(enums, "TrueFalse", fields[22]),
        "IsCommander": get_enum_name(enums, "CommanderStatus", fields[23]),
        "Battalion": get_enum_name(enums, "BattalionID", fields[24]),
        "BattalionLv": fields[25],
        "Spell1": get_enum_name(enums, "SpellIDBai", fields[26]),
        "Spell2": get_enum_name(enums, "SpellIDBai", fields[27]),
        "CombatArt": get_enum_name(enums, "ArtID", fields[28]),
        "UnitGender": get_enum_name(enums, "Gender", fields[29]),
        "Padding": fields[30]
    }


def get_empty_entry():
    return {
        "CharacterID": "None", "unknown": 0, "ClassID": "NoClass",
        "Weapons": {
            "Item1": "None_Item", "Item2": "None_Item", "Item3": "None_Item",
            "Item4": "None_Item", "Item5": "None_Item", "Item6": "None_Item",
            "ItemFlags": "no_Drop"
        },
        "Skills": {
            "Ability1": "NoAbility", "Ability2": "NoAbility", "Ability3": "NoAbility",
            "Ability4": "NoAbility", "Ability5": "NoAbility"
        },
        "X": 0, "Y": 0, "Rotation": "RightButSlightlyUp", "FixedLevel": 0,
        "Allegiance": "Player_Blue", "SpawnType": "ScriptedSpawn", "CharacterFlags": "No_movement_AI",
        "BattallionFlag": "Disabled", "IsCommander": "Commander_Unit", "Battalion": "No_Battalion",
        "BattalionLv": 0, "Spell1": "NoSpell", "Spell2": "NoSpell", "CombatArt": "None_Art",
        "UnitGender": "UnitDefault", "Padding": 0
    }

def entry_to_bytes(entry, enums):
    w = entry["Weapons"]
    s = entry["Skills"]

    return struct.pack(
        ENTRY_FORMAT,
        get_enum_val(enums, "CharID", entry["CharacterID"]),
        entry["unknown"],
        get_enum_val(enums, "Class", entry["ClassID"]),
        get_enum_val(enums, "ItemsBai", w["Item1"]),
        get_enum_val(enums, "ItemsBai", w["Item2"]),
        get_enum_val(enums, "ItemsBai", w["Item3"]),
        get_enum_val(enums, "ItemsBai", w["Item4"]),
        get_enum_val(enums, "ItemsBai", w["Item5"]),
        get_enum_val(enums, "ItemsBai", w["Item6"]),
        get_enum_val(enums, "DroppableItem", w["ItemFlags"]),
        get_enum_val(enums, "AbilityID", s["Ability1"]),
        get_enum_val(enums, "AbilityID", s["Ability2"]),
        get_enum_val(enums, "AbilityID", s["Ability3"]),
        get_enum_val(enums, "AbilityID", s["Ability4"]),
        get_enum_val(enums, "AbilityID", s["Ability5"]),
        entry["X"],
        entry["Y"],
        get_enum_val(enums, "Rotation", entry["Rotation"]),
        entry["FixedLevel"],
        get_enum_val(enums, "Team", entry["Allegiance"]),
        get_enum_val(enums, "ScriptSpawn", entry["SpawnType"]),
        get_enum_val(enums, "MovementFlags", entry["CharacterFlags"]),
        get_enum_val(enums, "TrueFalse", entry["BattallionFlag"]),
        get_enum_val(enums, "CommanderStatus", entry["IsCommander"]),
        get_enum_val(enums, "BattalionID", entry["Battalion"]),
        entry["BattalionLv"],
        get_enum_val(enums, "SpellIDBai", entry["Spell1"]),
        get_enum_val(enums, "SpellIDBai", entry["Spell2"]),
        get_enum_val(enums, "ArtID", entry["CombatArt"]),
        get_enum_val(enums, "Gender", entry["UnitGender"]),
        entry["Padding"]
    )


def repack_to_bai(json_file, output_file=None):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    enums = load_enums(["3H_BaiArtsEnums.txt", "3H_BaiEnums.txt"])

    header = data["Header"]
    routes = data["Routes"]
    single_route_mode = data.get("SingleRouteMode", False)

    # Use stored route sizes if available; fall back to tight packing
    route_sizes = data.get("RouteSizes", [])
    route_tails = data.get("RouteTails", [])

    if not route_sizes:
        if single_route_mode:
            route_sizes = [len(routes[0]) * ENTRY_SIZE]
            route_tails = [""]
        else:
            route_sizes = [len(routes[i]) * ENTRY_SIZE for i in range(3)]
            route_tails = ["" for _ in range(3)]

    # Ensure we have enough tail entries
    while len(route_tails) < len(route_sizes):
        route_tails.append("")

    # Ensure each route has enough space for its current entries
    for i in range(len(routes)):
        required = len(routes[i]) * ENTRY_SIZE
        if required > route_sizes[i]:
            route_sizes[i] = required
            route_tails[i] = ""  # No tail if we expanded

    # Calculate start offsets and total file size
    if single_route_mode:
        route_starts = [FILE_HEADER_SIZE]
        total_size = FILE_HEADER_SIZE + route_sizes[0]
    else:
        route_starts = [FILE_HEADER_SIZE]
        for i in range(1, 3):
            route_starts.append(route_starts[i-1] + route_sizes[i-1])
        total_size = route_starts[-1] + route_sizes[-1]

    buf = bytearray(total_size)

    # Write file header
    if single_route_mode:
        ptrs = [0, 0, 0]
    else:
        ptrs = [route_starts[i] - FILE_HEADER_SIZE for i in range(3)]

    struct.pack_into("<6I", buf, 0,
        header["Header"], header["UnkPointer1"], header["UnkPointer2"],
        ptrs[0], ptrs[1], ptrs[2])

    # Write each route
    for i, route in enumerate(routes):
        start = route_starts[i]
        boundary_size = route_sizes[i]
        num_slots = boundary_size // ENTRY_SIZE

        # Pad with empty entries to fill all slots
        padded_route = list(route)
        while len(padded_route) < num_slots:
            padded_route.append(get_empty_entry())

        for j, entry in enumerate(padded_route[:num_slots]):
            base = start + j * ENTRY_SIZE
            buf[base:base+ENTRY_SIZE] = entry_to_bytes(entry, enums)

        # Write preserved tail bytes (padding / partial data)
        data_end = start + num_slots * ENTRY_SIZE
        boundary_end = start + boundary_size
        if data_end < boundary_end:
            tail_hex = route_tails[i]
            if tail_hex:
                tail_bytes = bytes.fromhex(tail_hex)
                # Only write as many bytes as fit in the remaining space
                tail_len = min(len(tail_bytes), boundary_end - data_end)
                buf[data_end:data_end+tail_len] = tail_bytes[:tail_len]
            # Zero out any remaining space (shouldn't happen if sizes match)
            written_to = data_end + (len(tail_bytes) if tail_hex else 0)
            if written_to < boundary_end:
                buf[written_to:boundary_end] = b'\x00' * (boundary_end - written_to)

    if not output_file:
        output_file = os.path.splitext(json_file)[0] + "_repacked.bai"

    with open(output_file, "wb") as f:
        f.write(buf)

    print(f"Repacked: {output_file}  ({len(buf)} bytes)")


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python mapSpawnData_bai.py dump <input.bai>")
        print("  python mapSpawnData_bai.py repack <input.json>")
        return

    mode = sys.argv[1].lower()
    input_file = sys.argv[2]

    if mode == "dump":
        parsed = parse_bai_file(input_file)
        out = os.path.splitext(input_file)[0] + ".json"

        json_str = json.dumps(parsed, indent=4)

        def compact_int_arrays(match):
            inner = match.group(1)
            if not inner.strip():
                return "[]"
            nums = [x.strip() for x in inner.split(',')]
            return "[" + ", ".join(nums) + "]"

        json_str = re.sub(r'\[\s*((?:\d+\s*,\s*)*\d+)\s*\]', compact_int_arrays, json_str)

        with open(out, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Dumped: {out}")

    elif mode == "repack":
        repack_to_bai(input_file)

    else:
        print(f"Unknown mode: {mode}")
        print("Use 'dump' or 'repack'.")

if __name__ == "__main__":
    main()
