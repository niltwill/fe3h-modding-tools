from pathlib import Path
from struct import unpack
from struct import pack, pack_into
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
            #link_id2 = unpack("<I", data[offset+172:offset+176])[0] #unless editing, not needed twice
            unknown_data = section_size - 24

            info_sections.append({
                "offset": offset,
                "section_id": section_id,
                "section_size": section_size,
                "link_id": link_id,
                "channel_count": channel_count,
                "layer_count": layer_count,
                "padding_1": padding_1,
                "cancel": cancel,
                #"link_id2": link_id2,
                "unknown_data_len": unknown_data
            })

            offset += section_size
        elif section_id == PADDING_ID:
            break
        else:
            section_size = unpack("<I", data[offset+4:offset+8])[0]
            offset += section_size

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
                    "section_id": section_id,
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
                    "section_id": section_id,
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
            section_size = unpack("<I", data[offset+4:offset+8])[0]
            offset += section_size

    return info2_sections


def insert_bytes_at_offset(file_path, insert_offset, new_data):
    with open(file_path, "rb") as f:
        original = f.read()

    updated = original[:insert_offset] + new_data + original[insert_offset:]

    with open(file_path, "wb") as f:
        f.write(updated)

    return len(new_data)  # return size of inserted data

def copy_info_sections_by_link_id(file_path, link_id):
    info_sections = parse_info_sections(file_path)
    info2_sections = parse_info2_sections(file_path)

    info_entry = next((info for info in info_sections if info["link_id"] == link_id), None)
    info2_entry = next((info for info in info2_sections if info["link_id"] == link_id), None)

    if not info_entry or not info2_entry:
        print(f"Could not find INFO and/or INFO2 section with link_id {link_id}")
        return

    with open(file_path, "rb") as f:
        original_data = f.read()

    info_bytes = original_data[info_entry["offset"] : info_entry["offset"] + info_entry["section_size"]]
    info2_bytes = original_data[info2_entry["offset"] : info2_entry["offset"] + info2_entry["section_size"]]

    info_section = info_entry["section_size"]
    info2_section = info2_entry["section_size"]

    # Find the last INFO section
    last_info = max(info_sections, key=lambda x: x["offset"])
    info_insert_offset = last_info["offset"] + last_info["section_size"]
    
    # Find the last INFO2 section
    last_info2 = max(info2_sections, key=lambda x: x["offset"])
    info2_insert_offset = last_info2["offset"] + last_info2["section_size"]

    if info_insert_offset < info2_insert_offset:
        # INFO comes before INFO2, so insert INFO2 first to avoid shifting

        # 1. Insert INFO2 (original, unmodified bytes)
        insert_bytes_at_offset(file_path, info2_insert_offset, info2_bytes)

        # 2. Insert INFO (original, unmodified bytes)
        insert_bytes_at_offset(file_path, info_insert_offset, info_bytes)

        print(f"INFO and INFO2 sections for link_id {link_id} duplicated and inserted.")
        print(f"New INFO offset:  {info_insert_offset}")
        print(f"New INFO2 offset: {info2_insert_offset}")

    else:
        # INFO2 comes before INFO, so insert INFO first

        # 1. Insert INFO (original, unmodified bytes)
        info_size = insert_bytes_at_offset(file_path, info_insert_offset, info_bytes)

        # 2. Insert INFO2 (offset needs adjustment because INFO was inserted before it)
        # The insertion point for INFO2 is shifted by the size of the INFO section.
        adjusted_info2_offset = info2_insert_offset + info_size
        insert_bytes_at_offset(file_path, adjusted_info2_offset, info2_bytes)

        print(f"INFO and INFO2 sections for link_id {link_id} duplicated and inserted.")
        print(f"New INFO offset:  {info_insert_offset}")
        print(f"New INFO2 offset: {adjusted_info2_offset}")

    # Update file size fields
    with open(file_path, "rb") as f:
        data = bytearray(f.read())

    final_size = len(data)
    size_bytes = pack("<I", final_size)

    data[24:28] = size_bytes
    data[28:32] = size_bytes
    print(f"Updated header file size at offsets 24 and 28 with {final_size} bytes.")

    with open(file_path, "wb") as f:
        f.write(data)


# Main
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python copy_ktsl2asbin_chunk.py <file.ktsl2asbin> <link_id>")
        sys.exit(1)

    filename = sys.argv[1]
    link_id = int(sys.argv[2], 0)  # allows hex or decimal

    copy_info_sections_by_link_id(filename, link_id)
