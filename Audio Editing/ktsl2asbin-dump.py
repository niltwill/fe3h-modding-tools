from struct import unpack
import os
import sys

MAGIC = b"KTSR"
KTSL2ASBIN_ID = 0x1A487B77
INFO2_SECTION_ID = 0x70CBCCC5
HEADER_LENGTH = 64

ProjectRate = {
    8000, 11025, 16000, 22050, 32000, 44100, 48000,
    88200, 96000, 176400, 192000, 352800, 384000
}

def parse_info2_sections(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    if data[:4] != MAGIC or unpack("<I", data[4:8])[0] != KTSL2ASBIN_ID:
        raise ValueError("Not a valid .ktsl2asbin file")

    offset = HEADER_LENGTH
    data_len = len(data)
    info2_sections = []

    while offset + 8 <= data_len:
        section_id = unpack("<I", data[offset:offset+4])[0]

        if section_id == INFO2_SECTION_ID:
        
            # save offset values for easier writability (for editing later)
            section_size_offset = offset+4
            link_id_offset = offset+8
            channel_count_offset = offset+44

            section_size = unpack("<I", data[offset+4:offset+8])[0]
            link_id = unpack("<I", data[offset+8:offset+12])[0]
            unk1 = unpack("<I", data[offset+12:offset+16])[0]
            unk2 = unpack("<I", data[offset+16:offset+20])[0]
            unk3 = unpack("<I", data[offset+20:offset+24])[0]
            unk4 = unpack("<I", data[offset+24:offset+28])[0]
            header_size = unpack("<I", data[offset+28:offset+32])[0]
            type_id2 = unpack("<I", data[offset+32:offset+36])[0]
            section_size2 = unpack("<I", data[offset+36:offset+40])[0]
            unk4b = unpack("<I", data[offset+40:offset+44])[0]
            channel_count = unpack("<I", data[offset+44:offset+48])[0]
            transition_related = unpack("<I", data[offset+48:offset+52])[0]

            test_val = unpack("<I", data[offset+52:offset+56])[0]

            if test_val in ProjectRate:
                sample_rate = test_val
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

                if loop_start == 0xFFFFFFFF:
                    loop_start = -1

                # save offset values for easier writability (second part)
                sample_rate_offset = offset+52
                sample_count_offset = offset+56
                loop_start_offset = offset+64
                ktss_offset_offset = offset+88
                ktss_size_offset = offset+92

                info2_sections.append({
                    "offset": offset,
                    "section_size (" + str(section_size_offset) + ")": section_size,
                    "link_id (" + str(link_id_offset) + ")": link_id,
                    "channel_count (" + str(channel_count_offset) + ")": channel_count,
                    "sample_rate (" + str(sample_rate_offset) + ")": sample_rate,
                    "sample_count (" + str(sample_count_offset) + ")": sample_count,
                    "loop_start (" + str(loop_start_offset) + ")": loop_start,
                    "ktss_offset (" + str(ktss_offset_offset) + ")": ktss_offset,
                    "ktss_size (" + str(ktss_size_offset) + ")": ktss_size
                })
            else:
                # Other variant
                unk5 = test_val
                sample_rate = unpack("<I", data[offset+56:offset+60])[0]
                sample_count = unpack("<I", data[offset+60:offset+64])[0]
                unk6 = unpack("<I", data[offset+64:offset+68])[0]
                loop_start = unpack("<I", data[offset+68:offset+72])[0]
                unk7 = unpack("<I", data[offset+72:offset+76])[0]
                unk8 = unpack("<I", data[offset+76:offset+80])[0]
                unk9 = unpack("<I", data[offset+80:offset+84])[0]
                ktss_offset = unpack("<I", data[offset+84:offset+88])[0]
                ktss_size = unpack("<I", data[offset+88:offset+92])[0]

                if loop_start == 0xFFFFFFFF:
                    loop_start = -1

                # save offset values for easier writability (second part)
                sample_rate_offset = offset+56
                sample_count_offset = offset+60
                loop_start_offset = offset+68
                ktss_offset_offset = offset+84
                ktss_size_offset = offset+88

                info2_sections.append({
                    "offset": offset,
                    "section_size (" + str(section_size_offset) + ")": section_size,
                    "link_id (" + str(link_id_offset) + ")": link_id,
                    "channel_count (" + str(channel_count_offset) + ")": channel_count,
                    "sample_rate (" + str(sample_rate_offset) + ")": sample_rate,
                    "sample_count (" + str(sample_count_offset) + ")": sample_count,
                    "loop_start (" + str(loop_start_offset) + ")": loop_start,
                    "ktss_offset (" + str(ktss_offset_offset) + ")": ktss_offset,
                    "ktss_size (" + str(ktss_size_offset) + ")": ktss_size
                })

            offset += section_size
        else:
            offset += 4

    return info2_sections

# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("This dumps a TXT file which can be edited for the ktsl2stbin equivalent")
        print("It also dumps all the voice lines in a folder for VGMStream")
        print("NOTE: Not all ktsl2asbin files have these voice lines embedded in them")
        print("Usage: python ktsl2asbin-dump.py file.ktsl2asbin")
        sys.exit(1)

    filename = sys.argv[1]
    info2 = parse_info2_sections(filename)
    output_txt = os.path.splitext(filename)[0] + ".txt"

    with open(output_txt, 'w', encoding='utf-8') as f:
        for i, section in enumerate(info2):
            print(f"[Info2 #{i+1}]", file=f)
            for k, v in section.items():
                print(f"  {k}: {v}", file=f)
            print("", file=f)
            
    # Save each Info2 voice data block as a binary file
    output_dir = os.path.splitext(filename)[0]
    os.makedirs(output_dir, exist_ok=True)

    with open(filename, "rb") as bin_file:
        for i, section in enumerate(info2):
            offset = section["offset"]
            # Extract offset value from the key that starts with "section_size ("
            section_size_key = next(k for k in section if k.startswith("section_size ("))
            section_size = section[section_size_key]

            bin_file.seek(offset)
            chunk = bin_file.read(section_size)

            output_path = os.path.join(output_dir, f"{i+1:03}.vgmstream")
            with open(output_path, "wb") as out_file:
                out_file.write(chunk)