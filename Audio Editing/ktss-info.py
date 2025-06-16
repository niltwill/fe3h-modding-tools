from pathlib import Path
from struct import unpack
import sys

# Define hex markers and other constants
KTSS_ID = 0x5353544B
KTSS_HEADER_LENGTH = 112

# Read KTSS
def parse_ktss_sections(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    offset = 0
    data_len = len(data)
    ktss_sections = []

    while offset + 8 <= data_len:
        section_id = unpack("<I", data[offset:offset+4])[0]

        if section_id == KTSS_ID:
            section_size = unpack("<I", data[offset+4:offset+8])[0]
            padding1 = 24

            s_offset = offset+8+padding1
            codec_id = unpack("<B", data[s_offset:s_offset+1])[0]
            unk1 = unpack("<B", data[s_offset+1:s_offset+2])[0]
            unk2 = unpack("<B", data[s_offset+2:s_offset+3])[0]
            unk3 = unpack("<B", data[s_offset+3:s_offset+4])[0]
            codec_start_offset = unpack("<I", data[s_offset+4:s_offset+8])[0]
            layer_count = unpack("<B", data[s_offset+8:s_offset+9])[0]
            channel_count = unpack("<B", data[s_offset+9:s_offset+10])[0]
            unk4 = unpack("<H", data[s_offset+10:s_offset+12])[0]
            sample_rate = unpack("<I", data[s_offset+12:s_offset+16])[0] # the frequency at which the KTSS is read
            sample_count = unpack("<I", data[s_offset+16:s_offset+20])[0] # if looping, this should be: loop start + loop length
            loop_start = unpack("<I", data[s_offset+20:s_offset+24])[0] # in sample block
            loop_length = unpack("<I", data[s_offset+24:s_offset+28])[0] # in sample block
            padding2 = unpack("<I", data[s_offset+28:s_offset+32])[0]

            audio_section_address = unpack("<I", data[s_offset+32:s_offset+36])[0]
            audio_section_size = unpack("<I", data[s_offset+36:s_offset+40])[0]
            unk5 = unpack("<I", data[s_offset+40:s_offset+44])[0]
            frame_count = unpack("<I", data[s_offset+44:s_offset+48])[0]
            frame_size = unpack("<H", data[s_offset+48:s_offset+50])[0]
            some_constant = unpack("<H", data[s_offset+50:s_offset+52])[0] # always 960 so far
            sample_rate_original = unpack("<I", data[s_offset+52:s_offset+56])[0] # the frequency the original file was using
            skip = unpack("<H", data[s_offset+56:s_offset+58])[0] # initial delay in samples
            stream_count = unpack("<B", data[s_offset+58:s_offset+59])[0]
            coupled_count = unpack("<B", data[s_offset+59:s_offset+60])[0]
            channel_mapping_family = list(data[s_offset+60:s_offset+60+channel_count])

            # Current relative offset into KTSS section
            relative_offset = (s_offset + 60 + channel_count) - (s_offset - 8 - padding1)

            # Padding needed to align to next 0x70 (112-byte) boundary
            remainder = relative_offset % 0x70
            padding3 = (0x70 - remainder) if remainder != 0 else 0

            full_header_length = relative_offset + padding3
            assert full_header_length == KTSS_HEADER_LENGTH, f"Header length mismatch at offset {offset}: got {full_header_length}, expected {KTSS_HEADER_LENGTH}"

            ktss_sections.append({
                "offset": offset,
                "section_size": section_size,
                "padding1": padding1,
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
                "loop_start": loop_start,
                "loop_length": loop_length,
                "padding2": padding2,
                "audio_section_address": audio_section_address,
                "audio_section_size": audio_section_size,
                "unk5": unk5,
                "frame_count": frame_count,
                "frame_size": frame_size,
                "some_constant": some_constant,
                "sample_rate_original": sample_rate_original,
                "skip": skip,
                "stream_count": stream_count,
                "coupled_count": coupled_count,
                "channel_mapping_family": channel_mapping_family,
                "padding3": padding3
            })

            offset += section_size
        else:
            offset += 4

    print(ktss_sections)
    return ktss_sections


# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Display verbose information about KTSS audio files")
        print("(This is used as basis for editing/understanding its structure)")
        print("Usage: python ktss-info.py XXXX.ktss")
        sys.exit(1)

    filename = sys.argv[1]
    parsed = parse_ktss_sections(filename)

    """
    for i, section in enumerate(parsed):
        print(f"\n--- KTSS Section {i} ---")
        for key, value in section.items():
            print(f"{key}: {value}")
    """