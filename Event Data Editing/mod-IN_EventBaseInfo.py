import json
import os
import struct
import sys

# Enum definitions
enumSupport = {
    0: "C",
    1: "C_Plus",
    2: "B",
    3: "B_Plus",
    4: "A",
    5: "A_Plus",
    6: "S",
    7: "Goddess_Tower",
}

enumByleth_Gender = {
    0: "Male",
    1: "Female",
    15: "Both",
    255: "Not_Byleth",
}

enumAvailability = {
    0: "Pre_Timeskip_Only",
    1: "Post_Timeskip_Only",
    2: "Wedding_Ring_Needed", # educated guess
    255: "No_Restriction",
}

enumNames = {
    0: "Byleth_0",
    1: "Byleth_1",
    2: "Edelgard_2",
    3: "Dimitri_3",
    4: "Claude_4",
    5: "Hubert_5",
    6: "Ferdinand_6",
    7: "Linhardt_7",
    8: "Caspar_8",
    9: "Bernadetta_9",
    10: "Dorothea_10",
    11: "Petra_11",
    12: "Dedue_12",
    13: "Felix_13",
    14: "Ashe_14",
    15: "Sylvain_15",
    16: "Mercedes_16",
    17: "Annette_17",
    18: "Ingrid_18",
    19: "Lorenz_19",
    20: "Raphael_20",
    21: "Ignatz_21",
    22: "Lysithea_22",
    23: "Marianne_23",
    24: "Hilda_24",
    25: "Leonie_25",
    26: "Seteth_26",
    27: "Flayn_27",
    28: "Hanneman_28",
    29: "Manuela_29",
    30: "Gilbert_30",
    31: "Alois_31",
    32: "Catherine_32",
    33: "Shamir_33",
    34: "Cyril_34",
    35: "Jeralt_35",
    36: "Rhea_36",
    37: "Sothis_37",
    1040: "Yuri",
    1041: "Balthus",
    1042: "Constance",
    1043: "Hapi",
    1044: "ChurchOfSeirosDudeWithMinorCrest",
    1045: "Jeritza_Playable",
    1046: "Anna_Playable",
}

def get_enum_label(enum_dict, key):
    return enum_dict.get(key, f"{key}")

def get_enum_value(enum_dict, label):
    for key, value in enum_dict.items():
        if value == label:
            return key
    try:
        # If it's already a numeric string like "3", return as int
        return int(label)
    except ValueError:
        raise ValueError(f"Label '{label}' not found in enum.")

def parse_6163_file(filename):
    with open(filename, 'rb') as f:
        # Header
        number_of_entries, unknown1, unknown2, unknown3 = struct.unpack('<4I', f.read(16))
        #print(f"Header: Entries={number_of_entries}, Unknowns=({unknown1}, {unknown2}, {unknown3})")

        # These entries seem to have changed since game updates, as +2 bytes were added (it's no longer 26, but 28!)
        # It got rearranged too from the 010 Binary template, so I had to shuffle some of these entries around
        # Not sure about "MiscUnknown1" or "MiscUnknown2" (their values are: 0, 4, 255 - it's like a boolean [0=off,4=on] or ignored value [255])
        # MiscUnknown3 could be the DLC chapter or side story availability, as it's always 255 (off)?
        entries = []
        for i in range(number_of_entries):
            entry_data = f.read(28)
            (
                entry_number,
                *unknown_flags, # 8 unknown flags
                support_partner_1,
                unk_misc1,
                support_partner_2,
                unk_misc2,
                support_flag,
                byleth_gender,
                unk_byleth_toggle,
                availability_flag,
                unk_misc3,
                ch_avail_be, ch_avail_bl, ch_avail_gd, ch_avail_church,
                ch_deadline_be, ch_deadline_bl, ch_deadline_gd, ch_deadline_church,
                placeholder
            ) = struct.unpack('<H8B BBBBBBBBB 4B4B B', entry_data)

            entry = {
                "EntryNumber": entry_number,
                "UnknownFlags": unknown_flags,
                "SupportPartner1": get_enum_label(enumNames, support_partner_1),
                "MiscUnknown1": unk_misc1,
                "SupportPartner2": get_enum_label(enumNames, support_partner_2),
                "MiscUnknown2": unk_misc2,
                "SupportFlag": get_enum_label(enumSupport, support_flag),
                "BylethGender": get_enum_label(enumByleth_Gender, byleth_gender),
                "ToggleFlag": unk_byleth_toggle,
                "Availability": get_enum_label(enumAvailability, availability_flag),
                "MiscUnknown3": unk_misc3,
                "ChapterAvailability": {
                    "BE": ch_avail_be,
                    "BL": ch_avail_bl,
                    "GD": ch_avail_gd,
                    "Church": ch_avail_church
                },
                "ChapterDeadline": {
                    "BE": ch_deadline_be,
                    "BL": ch_deadline_bl,
                    "GD": ch_deadline_gd,
                    "Church": ch_deadline_church
                },
                "Placeholder": placeholder
            }
            entries.append(entry)

        return {
            "Header": {
                "NumberOfEntries": number_of_entries,
                "Unknown1": unknown1,
                "Unknown2": unknown2,
                "Unknown3": unknown3
            },
            "Entries": entries
        }

def rebuild_6163_file(json_data, output_filename):
    with open(output_filename, 'wb') as f:
        header = json_data["Header"]
        entries = json_data["Entries"]

        # Write header
        number_of_entries = header["NumberOfEntries"]
        unknown1 = header["Unknown1"]
        unknown2 = header["Unknown2"]
        unknown3 = header["Unknown3"]
        f.write(struct.pack('<4I', number_of_entries, unknown1, unknown2, unknown3))

        for entry in entries:
            entry_number = entry["EntryNumber"]
            unknown_flags = entry["UnknownFlags"]  # List of 8 bytes

            support_partner_1 = get_enum_value(enumNames, entry["SupportPartner1"])
            unk_misc1 = entry["MiscUnknown1"]
            support_partner_2 = get_enum_value(enumNames, entry["SupportPartner2"])
            unk_misc2 = entry["MiscUnknown2"]
            support_flag = get_enum_value(enumSupport, entry["SupportFlag"])
            byleth_gender = get_enum_value(enumByleth_Gender, entry["BylethGender"])
            unk_byleth_toggle = entry["ToggleFlag"]
            availability_flag = get_enum_value(enumAvailability, entry["Availability"])
            unk_misc3 = entry["MiscUnknown3"]

            ch_avail = entry["ChapterAvailability"]
            ch_deadline = entry["ChapterDeadline"]

            placeholder = entry["Placeholder"]

            # Pack and write the 28-byte entry
            entry_data = struct.pack(
                '<H8B BBBBBBBBB 4B4B B',
                entry_number,
                *unknown_flags,
                support_partner_1,
                unk_misc1,
                support_partner_2,
                unk_misc2,
                support_flag,
                byleth_gender,
                unk_byleth_toggle,
                availability_flag,
                unk_misc3,
                ch_avail["BE"],
                ch_avail["BL"],
                ch_avail["GD"],
                ch_avail["Church"],
                ch_deadline["BE"],
                ch_deadline["BL"],
                ch_deadline["GD"],
                ch_deadline["Church"],
                placeholder
            )
            f.write(entry_data)

        # Align to 16 bytes (add some padding as needed)
        current_size = f.tell()
        padding_needed = (16 - (current_size % 16)) % 16
        if padding_needed:
            f.write(b'\x00' * padding_needed)

def main():
    if len(sys.argv) < 3:
        print("FE3H: IN_EventBaseInfo (support-related)")
        print("For file: romfs/patch4/nx/event/talk_event/data/IN_EventBaseInfo.bin")
        print("")
        print("Usage:")
        print("  To dump:   python mod-IN_EventBaseInfo.py dump <IN_EventBaseInfo.bin> [output.json]")
        print("  To build:  python mod-IN_EventBaseInfo.py build <input.json> [IN_EventBaseInfo.bin]")
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
            result = parse_6163_file(input_file)
            with open(output_file, 'w', encoding='utf-8') as out_file:
                json.dump(result, out_file, indent=2)
            print(f"Dumped to: {output_file}")
        except Exception as e:
            print(f"Error while dumping: {e}")

    elif mode == "build":
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".bin"

        try:
            with open(input_file, 'r', encoding='utf-8') as jf:
                parsed_json = json.load(jf)
                rebuild_6163_file(parsed_json, output_file)
                print(f"Built to: {output_file}")
        except Exception as e:
            print(f"Error while building: {e}")

    else:
        print("Unknown mode. Use 'dump' or 'build'.")

if __name__ == "__main__":
    main()
