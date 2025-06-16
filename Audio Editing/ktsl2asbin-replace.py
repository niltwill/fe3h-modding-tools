import mmap
import sys
from pathlib import Path
from struct import pack, unpack

# Define hex markers and other constants
MAGIC = b"KTSR"
KTSL2ASBIN_ID = 0x1A487B77
INFO2_SECTION_ID = 0x70CBCCC5
HEADER_LENGTH = 64

# For a conditional part, the project rate is checked later
ProjectRate = {
    8000, 11025, 16000, 22050, 32000, 44100, 48000,
    88200, 96000, 176400, 192000, 352800, 384000
}
# Read the binary file
def parse_ktsl2asbin(data):
    results = {
        "is_valid_ktsl2asbin": False,
        "info2_sections": [],
    }

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

        if section_id == INFO2_SECTION_ID:
            results["info2_sections"].append(offset)

        offset += 4

    return results

# Read info_sections (second)
def parse_info2_sections(data):
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

    return info2_sections


# Main
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("FE3H - Replace a KTGCADPCM audio in a ktsl2asbin file")
        print("First specify the source ktsl2asbin file, then the vgmstream file")
        print("You must also specify the desired index to replace (numeric value)")
        print("Usage: python ktsl2asbin-replace.py XXXX.ktsl2asbin XXXX.vgmstream <index>")
        sys.exit(1)

    filename = sys.argv[1]
    new_audio = sys.argv[2]
    index = int(sys.argv[3])

    with open(filename, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        parsed = parse_ktsl2asbin(data)
        info2_data = parse_info2_sections(data)

    #parsed = parse_ktsl2asbin(filename)
    #print("Is valid ktsl2asbin:", parsed["is_valid_ktsl2asbin"])
    if parsed["is_valid_ktsl2asbin"]:

        info2_offsets = parsed["info2_sections"]
        max_index = len(info2_offsets)

        if index > max_index:
            print(f"Error: Your index was larger than the max (last entry): {max_index}")
            exit(1)

        cur_index = info2_offsets[index-1]
        next_index = 0

        #info2_data = parse_info2_sections(filename)
        cur_entry = info2_data[index-1]

        #print(cur_entry) # for reference only
        #print("")

        offset_start = cur_index
        #print(offset_start)
        offset_end = cur_entry["section_size"]
        #print(offset_end)
 
        # read the new audio binary data
        with open(new_audio, "rb") as f:
            new_audio_data = f.read()

        # read original ktsl2asbin content
        with open(filename, "rb") as f:
            original_data = f.read()

        # calculate new binary
        before = original_data[:offset_start]
        after = original_data[offset_start + offset_end:]
        new_ktsl2asbin = before + new_audio_data + after

        # new "section_size" is also needed
        new_section_size = len(new_audio_data)
        new_section_size_bytes = new_section_size.to_bytes(4, "little")
        new_ktsl2asbin = (
            new_ktsl2asbin[:offset_start + 4] +
            new_section_size_bytes +
            new_ktsl2asbin[offset_start + 8:]
        )

        # write to the file (in-place)
        with open(filename, "wb") as f:
            f.write(new_ktsl2asbin)

        print(f"Replaced index {index} successfully.")

        ## update file size info too
        with open(filename, "rb") as f:
            data = bytearray(f.read())

        # Update total file size at offsets 24 and 28
        final_size = len(data)
        size_bytes = pack("<I", final_size)

        data[24:28] = size_bytes  # First size field (decompressed size)
        data[28:32] = size_bytes  # Second size field (compressed size)

        # write to the file again (in-place)
        with open(filename, "wb") as f:
            f.write(data)

        #print(f"Updated header file size at offsets 24 and 28 with {final_size} bytes.")
    else:
        print(f"Error: Not a valid ktsl2asbin file: {filename}")
        exit(1)
