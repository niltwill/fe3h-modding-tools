from pathlib import Path
from struct import unpack
import sys

# Define hex markers and other constants
MAGIC = b"KTSR"
KTSL2ASBIN_ID = 0x1A487B77
INFO_SECTION_ID = 0x368C88BD
PADDING_ID = 0xA8DB7261
INFO2_SECTION_ID = 0x70CBCCC5
HEADER_LENGTH = 64

# For a conditional part, the project rate is checked later
ProjectRate = {
    8000,
    11025,
    16000,
    22050,
    32000,
    44100,
    48000,
    88200,
    96000,
    176400,
    192000,
    352800,
    384000
}

# Read the binary file
def parse_ktsl2asbin(file_path):
    results = {
        "is_valid_ktsl2asbin": False,
        "info_sections": [],
        "info2_sections": [],
        "padding_offsets": [],
    }

    with open(file_path, "rb") as f:
        data = f.read()

    # Check magic and type ID
    if data[:4] != MAGIC:
        return results

    type_id = unpack("<I", data[4:8])[0]
    if type_id != KTSL2ASBIN_ID:
        return results

    results["is_valid_ktsl2asbin"] = True

    offset = HEADER_LENGTH # Skip header
    data_len = len(data)

    while offset + 4 <= data_len:
        section_id = unpack("<I", data[offset:offset+4])[0]

        if section_id == INFO_SECTION_ID:
            results["info_sections"].append(offset)
        elif section_id == PADDING_ID:
            results["padding_offsets"].append(offset)
        elif section_id == INFO2_SECTION_ID:
            results["info2_sections"].append(offset)

        offset += 4

    return results

# Read info_sections (first)
def parse_info_sections(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    if data[:4] != MAGIC:
        raise ValueError("Invalid KTSR magic header")

    type_id = unpack("<I", data[4:8])[0]
    if type_id != KTSL2ASBIN_ID:
        raise ValueError("Not a ktsl2asbin file")

    offset = HEADER_LENGTH # Skip header
    data_len = len(data)
    info_sections = []

    while offset + 8 <= data_len:
        section_id = unpack("<I", data[offset:offset+4])[0]

        if section_id == INFO_SECTION_ID:
            section_size = unpack("<I", data[offset+4:offset+8])[0]
            link_id = unpack("<I", data[offset+8:offset+12])[0]
            channel_count = unpack("<H", data[offset+12:offset+14])[0]
            layer_count = unpack("<H", data[offset+14:offset+16])[0]
            padding_1 = unpack("<I", data[offset+16:offset+20])[0]
            cancel = unpack("<I", data[offset+20:offset+24])[0]
            unknown_data = section_size - 24

            info_sections.append({
                "offset": offset,
                "section_size": section_size,
                "link_id": link_id,
                "channel_count": channel_count,
                "layer_count": layer_count,
                "padding_1": padding_1,
                "cancel": cancel,
                "unknown_data_len": unknown_data
            })

            offset += section_size
        elif section_id == PADDING_ID:
            break
        else:
            offset += 4

    print(info_sections)
    return info_sections


# Read info_sections (second)
def parse_info2_sections(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    if data[:4] != MAGIC:
        raise ValueError("Invalid KTSR magic header")

    type_id = unpack("<I", data[4:8])[0]
    if type_id != KTSL2ASBIN_ID:
        raise ValueError("Not a ktsl2asbin file")

    offset = HEADER_LENGTH # Skip header
    data_len = len(data)
    info2_sections = []

    while offset + 8 <= data_len:
        section_id = unpack("<I", data[offset:offset+4])[0]

        if section_id == INFO2_SECTION_ID:
            section_size = unpack("<I", data[offset+4:offset+8])[0]
            link_id = unpack("<I", data[offset+8:offset+12])[0]
            unk1 = unpack("<I", data[offset+12:offset+16])[0]
            unk2 = unpack("<I", data[offset+16:offset+20])[0]
            unk3 = unpack("<I", data[offset+20:offset+24])[0]
            unk4 = unpack("<I", data[offset+24:offset+28])[0]
            header_size = unpack("<I", data[offset+28:offset+32])[0]
            type_id2 = unpack("<I", data[offset+32:offset+36])[0]
            section_size2 = unpack("<I", data[offset+36:offset+40])[0]
            unk4 = unpack("<I", data[offset+40:offset+44])[0]
            channel_count = unpack("<I", data[offset+44:offset+48])[0]
            transition_related = unpack("<I", data[offset+48:offset+52])[0]
            
            # here is an important conditional which separates certain ktsl2asbin files
            test_val = unpack("<I", data[offset+52:offset+56])[0]

            if test_val in ProjectRate:
                sample_rate = unpack("<I", data[offset+52:offset+56])[0]
                sample_count = unpack("<I", data[offset+56:offset+60])[0]
                unk6 = unpack("<I", data[offset+60:offset+64])[0]
                loop_start = unpack("<I", data[offset+64:offset+68])[0]
                unk7 = unpack("<I", data[offset+68:offset+72])[0]
                unk8 = unpack("<I", data[offset+72:offset+76])[0]
                unk9 = unpack("<I", data[offset+76:offset+80])[0]
                unk10 = unpack("<I", data[offset+80:offset+84])[0]
                unk11 = unpack("<I", data[offset+84:offset+88])[0]
                ktss_offset = unpack("<I", data[offset+88:offset+92])[0]
                ktss_size = unpack("<I", data[offset+92:offset+96])[0]
                
                # Change loop_start to invalid (unset) if it's "FF FF FF FF" in hex
                if loop_start == 4294967295:
                    loop_start = -1

                info2_sections.append({
                    "offset": offset,
                    "section_size": section_size,
                    "link_id": link_id,
                    "unk1": unk1,
                    "unk2": unk2,
                    "unk3": unk3,
                    "header_size": header_size,
                    "type_id2": type_id2,
                    "section_size2": section_size2,
                    "unk4": unk4,
                    "channel_count": channel_count,
                    "transition_related": transition_related,
                    "sample_rate": sample_rate,
                    "sample_count": sample_count,
                    "unk6": unk6,
                    "loop_start": loop_start,
                    "unk7": unk7,
                    "unk8": unk8,
                    "unk9": unk9,
                    "unk10": unk10,
                    "unk11": unk11,
                    "ktss_offset": ktss_offset,
                    "ktss_size": ktss_size
                })
                
            else:
                unk5 = unpack("<I", data[offset+52:offset+56])[0]
                sample_rate = unpack("<I", data[offset+56:offset+60])[0]
                sample_count = unpack("<I", data[offset+60:offset+64])[0]
                unk6 = unpack("<I", data[offset+64:offset+68])[0]
                loop_start = unpack("<I", data[offset+68:offset+72])[0]
                unk7 = unpack("<I", data[offset+72:offset+76])[0]
                unk8 = unpack("<I", data[offset+76:offset+80])[0]
                unk9 = unpack("<I", data[offset+80:offset+84])[0]
                ktss_offset = unpack("<I", data[offset+84:offset+88])[0]
                ktss_size = unpack("<I", data[offset+88:offset+92])[0]
                unk10 = unpack("<I", data[offset+92:offset+96])[0]

                # Change loop_start to invalid (unset) if it's "FF FF FF FF" in hex
                if loop_start == 4294967295:
                    loop_start = -1

                info2_sections.append({
                    "offset": offset,
                    "section_size": section_size,
                    "link_id": link_id,
                    "unk1": unk1,
                    "unk2": unk2,
                    "unk3": unk3,
                    "header_size": header_size,
                    "type_id2": type_id2,
                    "section_size2": section_size2,
                    "unk4": unk4,
                    "channel_count": channel_count,
                    "transition_related": transition_related,
                    "unk5": unk5,
                    "sample_rate": sample_rate,
                    "sample_count": sample_count,
                    "unk6": unk6,
                    "loop_start": loop_start,
                    "unk7": unk7,
                    "unk8": unk8,
                    "unk9": unk9,
                    "ktss_offset": ktss_offset,
                    "ktss_size": ktss_size,
                    "unk10": unk10,
                })

            offset += section_size
        else:
            offset += 4

    print(info2_sections)
    return info2_sections


# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Display verbose information about ktsl2asbin files")
        print("(This is used as basis for editing/understanding its structure)")
        print("Usage: python ktsl2asbin-info.py XXXX.ktsl2asbin")
        sys.exit(1)

    filename = sys.argv[1]
    parsed = parse_ktsl2asbin(filename)

    print("Is valid ktsl2asbin:", parsed["is_valid_ktsl2asbin"])
    if parsed["is_valid_ktsl2asbin"]:
        print("Info Sections at offsets:", parsed["info_sections"])
        print("Padding Section at offset:", parsed["padding_offsets"])
        print("Info2 Sections at offsets:", parsed["info2_sections"])

        print("")
        print("Info section 1.")
        parsed2 = parse_info_sections(filename)

        print("")
        print("Info section 2. (linked to ktsl2stbin)")
        parsed3 = parse_info2_sections(filename)

        print("")
        print("Linking info2_sections to info_sections via link_id:")

        # Create a lookup dictionary for info_section offsets by link_id
        info_link_map = {info["link_id"]: info["offset"] for info in parsed2}

        # Iterate over each info2_section and try to find the matching info_section
        for info2 in parsed3:
            link_id = info2["link_id"]
            info_offset = info_link_map.get(link_id, None)

            if info_offset is not None:
                print(f"Info2 @ offset {info2['offset']:08X} links to Info @ offset {info_offset:08X} (link_id = {link_id})")
            #else:
            #    print(f"Info2 @ offset {info2['offset']:08X} has unmatched link_id = {link_id}")