from pathlib import Path
from struct import unpack
import sys

# Define hex markers and other constants
MAGIC = b"KTSR"
KTSL2STBIN_ID = 0xFCDD9402
KTSS_SECTION_ID = 0x15F4D409
KTSS_DATA_ID = 0x5353544B
HEADER_LENGTH = 64

# Read the binary file
def parse_ktsl2stbin(file_path):
    results = {
        "is_valid_ktsl2stbin": False,
        "ktss_sections": [],
    }

    with open(file_path, "rb") as f:
        data = f.read()

    # Check magic and type ID
    if data[:4] != MAGIC:
        return results

    type_id = unpack("<I", data[4:8])[0]
    if type_id != KTSL2STBIN_ID:
        return results

    results["is_valid_ktsl2stbin"] = True

    offset = HEADER_LENGTH # Skip header
    data_len = len(data)

    while offset + 4 <= data_len:
        section_id = unpack("<I", data[offset:offset+4])[0]

        if section_id == KTSS_SECTION_ID:
            results["ktss_sections"].append(offset)

        offset += 4

    return results

# Read ktss_sections (first)
def parse_ktss_sections(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    if data[:4] != MAGIC:
        raise ValueError("Invalid KTSR magic header")

    type_id = unpack("<I", data[4:8])[0]
    if type_id != KTSL2STBIN_ID:
        raise ValueError("Not a ktsl2stbin file")

    offset = HEADER_LENGTH # Skip header
    data_len = len(data)
    ktss_sections = []

    while offset + 8 <= data_len:
        section_id = unpack("<I", data[offset:offset+4])[0]

        if section_id == KTSS_SECTION_ID:
            section_size = unpack("<I", data[offset+4:offset+8])[0]
            link_id = unpack("<I", data[offset+8:offset+12])[0]
            section_headersize = unpack("<I", data[offset+12:offset+16])[0]
            kns_size = unpack("<I", data[offset+16:offset+20])[0]
            padding_1 = 44

            ktss_sections.append({
                "offset": offset,
                "section_size": section_size,
                "link_id": link_id,
                "section_headersize": section_headersize,
                "kns_size": kns_size,
                "padding_1": padding_1
            })

            offset += section_size
        else:
            offset += 4

    print(ktss_sections)
    return ktss_sections

# Read ktss_sections (actual data)
def parse_ktss_sections2(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    if data[:4] != MAGIC:
        raise ValueError("Invalid KTSR magic header")

    type_id = unpack("<I", data[4:8])[0]
    if type_id != KTSL2STBIN_ID:
        raise ValueError("Not a ktsl2stbin file")

    offset = HEADER_LENGTH # Skip header
    data_len = len(data)
    ktss_sections2 = []

    while offset + 8 <= data_len:
        section_id = unpack("<I", data[offset:offset+4])[0]

        if section_id == KTSS_DATA_ID:
            section_size = unpack("<I", data[offset+4:offset+8])[0]
            padding_1 = 24
            new_offset = offset+8+padding_1
            codec_id = unpack("<B", data[new_offset:new_offset+1])[0]
            unk1 = unpack("<B", data[new_offset+1:new_offset+2])[0]
            unk2 = unpack("<B", data[new_offset+2:new_offset+3])[0]
            unk3 = unpack("<B", data[new_offset+3:new_offset+4])[0]
            codec_start_offset = unpack("<I", data[new_offset+4:new_offset+8])[0]
            layer_count = unpack("<B", data[new_offset+8:new_offset+9])[0]
            channel_count = unpack("<B", data[new_offset+9:new_offset+10])[0]
            unk4 = unpack("<H", data[new_offset+10:new_offset+12])[0]
            sample_rate = unpack("<I", data[new_offset+12:new_offset+16])[0]
            sample_count = unpack("<I", data[new_offset+16:new_offset+20])[0]
            loop_start_sample = unpack("<I", data[new_offset+20:new_offset+24])[0]
            loop_length = unpack("<I", data[new_offset+24:new_offset+28])[0]
            padding_2 = unpack("<I", data[new_offset+28:new_offset+32])[0]
            audio_offset = unpack("<I", data[new_offset+32:new_offset+36])[0]
            audio_size = unpack("<I", data[new_offset+36:new_offset+40])[0]
            unk5 = unpack("<I", data[new_offset+40:new_offset+44])[0]
            packet_count = unpack("<I", data[new_offset+44:new_offset+48])[0]
            packet_size = unpack("<H", data[new_offset+48:new_offset+50])[0]
            unk6 = unpack("<H", data[new_offset+50:new_offset+52])[0]
            input_sample_rate = unpack("<I", data[new_offset+52:new_offset+56])[0]
            skip = unpack("<H", data[new_offset+56:new_offset+58])[0]
            stream_count = unpack("<B", data[new_offset+58:new_offset+59])[0]
            coupled_count = unpack("<B", data[new_offset+59:new_offset+60])[0]
            
            # might need more depending on channel count
            channel_mapping_family1 = unpack("<B", data[new_offset+60:new_offset+61])[0]
            channel_mapping_family2 = unpack("<B", data[new_offset+61:new_offset+62])[0]
            #padding_3 = 18
            # I don't really get the final packet listing section from the BT file

            ktss_sections2.append({
                "offset": offset,
                "section_size": section_size,
                "padding_1": padding_1,
                "codec_id": codec_id,
                "unk1": unk1,
                "unk2": unk2,
                "unk3": unk3,
                "codec_start_offset": codec_start_offset,
                "layer_count": layer_count,
                "channel_count": channel_count,
                "unk4": unk4,
                "sample_rate": sample_rate,
                "sample_count": sample_count,
                "loop_start_sample": loop_start_sample,
                "loop_length": loop_length,
                "padding_2": padding_2,
                "audio_offset": audio_offset,
                "audio_size": audio_size,
                "unk5": unk5,
                "packet_count": packet_count,
                "packet_size": packet_size,
                "unk6": unk6,
                "input_sample_rate": input_sample_rate,
                "skip": skip,
                "stream_count": stream_count,
                "coupled_count": coupled_count,
                "channel_mapping_family1": channel_mapping_family1,
                "channel_mapping_family2": channel_mapping_family2
            })

            offset += section_size
        else:
            offset += 4

    print(ktss_sections2)
    return ktss_sections2


# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Display verbose information about ktsl2stbin files")
        print("(This is used as basis for editing/understanding its structure)")
        print("Usage: python ktsl2stbin-info.py XXXX.ktsl2stbin")
        sys.exit(1)

    filename = sys.argv[1]
    parsed = parse_ktsl2stbin(filename)

    print("Is valid ktsl2stbin:", parsed["is_valid_ktsl2stbin"])
    if parsed["is_valid_ktsl2stbin"]:
        print("KTSS Sections at offsets:", parsed["ktss_sections"])

        print("")
        print("KTSS section")
        parsed2 = parse_ktss_sections(filename)

        print("")
        print("KTSS section 2.")
        parsed3 = parse_ktss_sections2(filename)
