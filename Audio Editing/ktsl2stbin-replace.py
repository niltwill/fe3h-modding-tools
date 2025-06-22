import mmap
import os
import time
import sys
from pathlib import Path
from struct import pack, unpack

# Define hex markers and other constants
MAGIC = b"KTSR"
MAGIC2 = b"KTSC"
KTSL2ASBIN_ID = 0x1A487B77
INFO2_SECTION_ID = 0x70CBCCC5
KTSL2STBIN_ID = 0xFCDD9402
KTSS_SECTION_ID = 0x15F4D409
KTSS_ID = 0x5353544B
HEADER_LENGTH = 64
KTSS_HEADER_LENGTH = 112

# For a conditional part, the project rate is checked later
ProjectRate = {
    8000, 11025, 16000, 22050, 32000, 44100, 48000,
    88200, 96000, 176400, 192000, 352800, 384000
}

# Read for ktsl2asbin file (recognition)
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

# Read for KTSC file (recognition)
def parse_ktscbin(data):
    results = {
        "is_valid_ktsc": False
    }

    # Check magic and type ID
    if data[:4] != MAGIC2:
        return results

    results["is_valid_ktsc"] = True

    return results

def parse_ktsc_sections(data):
    #if data[:4] != MAGIC2:
    #    raise ValueError("Invalid KTSC magic header")

    offset = 4  # skip magic word
    data_len = len(data)
    ktsc_sections = []

    while offset + 4 <= data_len:
        flags = unpack("<H", data[offset:offset+2])[0]
        console_type = unpack("<H", data[offset+2:offset+4])[0]
        ktsr_count = unpack("<I", data[offset+4:offset+8])[0]
        ktsr_link_id_table_offset = unpack("<I", data[offset+8:offset+12])[0]
        ktsr_offset_table_offset = unpack("<I", data[offset+12:offset+16])[0]
        file_size = unpack("<I", data[offset+16:offset+20])[0]
        ktsc_end_offset = unpack("<I", data[offset+20:offset+24])[0]
        padding_1 = unpack("<I", data[offset+24:offset+28])[0]
        
        # Dynamically read ktsr_link_ids
        ktsr_link_ids = [
            unpack("<I", data[ktsr_link_id_table_offset + i * 4 : ktsr_link_id_table_offset + (i + 1) * 4])[0]
            for i in range(ktsr_count)
        ]

        # Dynamically read ktsr_offsets
        ktsr_offsets = [
            unpack("<I", data[ktsr_offset_table_offset + i * 4 : ktsr_offset_table_offset + (i + 1) * 4])[0]
            for i in range(ktsr_count)
        ]
        
        # Read trailing 4-byte value after ktsr_offsets
        trailing_offset = ktsr_offset_table_offset + ktsr_count * 4
        if trailing_offset + 4 <= len(data):
            file_end_offset = unpack("<I", data[trailing_offset:trailing_offset + 4])[0]
        else:
            file_end_offset = None
        
        ktsc_sections.append({
            "flags": flags,
            "console_type": console_type,
            "ktsr_count": ktsr_count,
            "ktsr_link_id_table_offset": ktsr_link_id_table_offset,
            "ktsr_offset_table_offset": ktsr_offset_table_offset,
            "file_size": file_size,
            "ktsc_end_offset": ktsc_end_offset,
            "padding_1": padding_1,
            "ktsr_link_ids": ktsr_link_ids,
            "ktsr_offsets": ktsr_offsets,
            "file_end_offset": file_end_offset
        })
        
        break

    return ktsc_sections

# Read info2_sections
def parse_info2_sections(data):
    #if data[:4] != MAGIC:
    #    raise ValueError("Invalid KTSR magic header")

    type_id = unpack("<I", data[4:8])[0]
    if type_id != KTSL2ASBIN_ID:
        raise ValueError("Not a ktsl2asbin file")

    offset = HEADER_LENGTH # Skip header
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
                #if loop_start == 4294967295:
                #    loop_start = -1
                    
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
                #if loop_start == 4294967295:
                #    loop_start = -1
                    
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

# Read the binary file
def parse_ktsl2stbin(data):
    results = {
        "is_valid_ktsl2stbin": False,
        "ktss_sections": [],
    }

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

# Read ktss_sections for the ktsl2stbin
def parse_ktss_sections(data):
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

    return ktss_sections

# Read KTSS
def parse_ktss_audio(file_path):
    with open(file_path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:

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

    return ktss_sections

def patch_info2_entry(data, match, link_id, offset_start, ktss_section_size_new,
                      new_ktss_channel_count, new_ktss_sample_rate, new_ktss_sample_count,
                      new_ktss_loop_start, verbose=True):
    """
    Patch the INFO2 entry of a ktsl2asbin file (to match new info for the linked ktsl2stbin)
    """
    try:
        # Find exact field offsets dynamically
        channel_count_field = next(k for k in match if k.startswith("channel_count ("))
        sample_rate_field   = next(k for k in match if k.startswith("sample_rate ("))
        sample_count_field  = next(k for k in match if k.startswith("sample_count ("))
        loop_start_field    = next(k for k in match if k.startswith("loop_start ("))
        ktss_offset_field   = next(k for k in match if k.startswith("ktss_offset ("))
        ktss_size_field     = next(k for k in match if k.startswith("ktss_size ("))

        # Convert field strings to integer file offsets
        channel_count_addr = int(channel_count_field.split("(")[1].split(")")[0])
        sample_rate_addr   = int(sample_rate_field.split("(")[1].split(")")[0])
        sample_count_addr  = int(sample_count_field.split("(")[1].split(")")[0])
        loop_start_addr    = int(loop_start_field.split("(")[1].split(")")[0])
        ktss_offset_addr   = int(ktss_offset_field.split("(")[1].split(")")[0])
        ktss_size_addr     = int(ktss_size_field.split("(")[1].split(")")[0])

        # Patch fields
        data.seek(channel_count_addr)
        data.write(pack("<I", new_ktss_channel_count))

        data.seek(sample_rate_addr)
        data.write(pack("<I", new_ktss_sample_rate))

        data.seek(sample_count_addr)
        data.write(pack("<I", new_ktss_sample_count))

        if new_ktss_loop_start == -1:
            new_ktss_loop_start = 0xFFFFFFFF

        data.seek(loop_start_addr)
        data.write(pack("<I", new_ktss_loop_start))

        data.seek(ktss_offset_addr)
        data.write(pack("<I", offset_start))

        data.seek(ktss_size_addr)
        data.write(pack("<I", ktss_section_size_new))

        if verbose:
            print(f"Patched INFO2 entry for link_id {link_id}:")
            print(f"  -> channel_count = {new_ktss_channel_count} (was {match[channel_count_field]})")
            print(f"  -> sample_rate   = {new_ktss_sample_rate} (was {match[sample_rate_field]})")
            print(f"  -> sample_count  = {new_ktss_sample_count} (was {match[sample_count_field]})")
            print(f"  -> loop_start    = {new_ktss_loop_start} (was {match[loop_start_field]})")
            print(f"  -> ktss_offset   = {offset_start} (was {match[ktss_offset_field]})")
            print(f"  -> ktss_size     = {ktss_section_size_new} (was {match[ktss_size_field]})")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to patch INFO2 entry for link_id {link_id}: {e}")
        return False

def update_following_ktss_offsets(info2_sections, replaced_link_id, delta, data):
    """
    Updates all ktss_offset fields in info2_sections after the replaced entry,
    based on the delta size shift caused by KTSS replacement.
    """
    # Sort by ktss_offset to ensure correct ordering
    sorted_sections = sorted(info2_sections, key=lambda s: s[next(k for k in s if k.startswith("ktss_offset ("))])

    # Find index of the replaced entry
    replaced_index = next((i for i, s in enumerate(sorted_sections)
                           if s[next(k for k in s if k.startswith("link_id ("))] == replaced_link_id), None)

    if replaced_index is None:
        print(f"[!] Link ID {replaced_link_id} not found in INFO2")
        return

    print(f"[+] Adjusting KTSS offsets starting from index {replaced_index + 1} (link_id = {replaced_link_id})...")

    for section in sorted_sections[replaced_index + 1:]:
        # Extract offset address of the ktss_offset field
        ktss_offset_field = next(k for k in section if k.startswith("ktss_offset ("))
        ktss_offset_addr = int(ktss_offset_field.split("(")[1].split(")")[0])
        old_offset = section[ktss_offset_field]
        new_offset = (old_offset + delta) - 16

        # In-place patch
        data.seek(ktss_offset_addr)
        data.write(pack("<I", new_offset))

        #print(f"[+] Updating link_id {section[next(k for k in section if k.startswith('link_id ('))]}: new_offset = {new_offset}, old_offset = {old_offset}")

def update_following_ktsr_offsets(data, ktsr_map, start_index, updated_ktss_entries):
    """
    Adjusts the ktss_offset field (at offset+372) in all KTSR blocks that follow the replaced one.
    """
    
    print(f"[+] Adjusting KTSS offsets starting from index {start_index+1}...")

    for entry in ktsr_map[start_index:]:
        link_id = entry["link_id"]
        offset_start = entry["offset"]

        # Match with KTSS entry by link_id
        ktss_entry = next((e for e in updated_ktss_entries if e["link_id"] == link_id), None)
        if not ktss_entry:
            continue

        new_offset = ktss_entry["offset"]
        #print(f"[+] Updating embedded KTSR for link_id {link_id} to new offset {new_offset}")

        data.seek(offset_start + 372)  # ktss_offset field | 288 -> info2 section start, +84 to reach ktss_offset
        data.write(pack("<I", new_offset))

def rebuild_ktsr_offsets(data):
    """
    This should make it possible to rearrange the KTSR blocks or add new ones later
    """
    # Parse KTSC section again to get the offset table base
    ktsc_sections = parse_ktsc_sections(data)
    if not ktsc_sections:
        raise RuntimeError("No KTSC section found; cannot rebuild KTSR offset table")

    section = ktsc_sections[0]
    offset_table_addr = section["ktsr_offset_table_offset"]
    offset_table_end = section["ktsc_end_offset"]
    old_offsets = section["ktsr_offsets"]
    ktsr_count = len(old_offsets)

    # Find all current KTSR offsets by scanning the binary
    new_ktsr_offsets = []
    pos = 0
    while True:
        pos = data.find(MAGIC, pos)
        if pos == -1:
            break
        new_ktsr_offsets.append(pos)
        pos += 4

    new_ktsr_entries = len(new_ktsr_offsets)

    if new_ktsr_entries != ktsr_count:
        print(f"Warning: expected {ktsr_count} KTSR entries, but found {new_ktsr_entries} in file")

    # Overwrite the offset table at the known table location
    data.seek(offset_table_addr)
    for offset in new_ktsr_offsets:
        data.write(pack("<I", offset))

    # Update KTSR count
    data.seek(8)
    data.write(pack("<I", new_ktsr_entries))

    # Determine current full file size
    data.seek(0, os.SEEK_END)
    file_l = data.tell()

    # Update file size
    fs1 = 20
    fs2 = offset_table_end - 4
    data.seek(fs1)
    data.write(pack("<I", file_l))
    data.seek(fs2)
    data.write(pack("<I", file_l))

    print(f"Rebuilt KTSR offset table with {new_ktsr_entries} entries at offset {offset_table_addr}-{offset_table_end - 8}")
    #print(f"Updated KTSR count table with {new_ktsr_entries} entries at offset 8")
    #print(f"Updated file size at offset {fs1} and {fs2} to: {file_l}")

def adjust_offsets(entry, offset_base):
    """
    Adds offset_base to all keys in entry that look like 'field_name (offset)'. (For KTSC)
    """
    adjusted = {}
    for k, v in entry.items():
        if "(" in k and k.endswith(")"):
            field, offset_str = k.rsplit("(", 1)
            try:
                rel_offset = int(offset_str.rstrip(")"))
                new_key = f"{field.strip()} ({rel_offset + offset_base})"
                adjusted[new_key] = v
            except ValueError:
                adjusted[k] = v
        else:
            adjusted[k] = v
    return adjusted

# Update file size info
def update_file_size(filename):
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

def get_updated_ktss_entries(filename):
    with open(filename, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        parsed = parse_ktsl2stbin(data)
        ktss_header = parse_ktss_sections(data)

    if not parsed["is_valid_ktsl2stbin"]:
        raise RuntimeError(f"Not a valid ktsl2stbin file: {filename}")

    return [
        {
            "index": i + 1,
            "offset": entry["offset"] + HEADER_LENGTH,
            "link_id": entry["link_id"],
            "section_size": entry["section_size"],
        }
        for i, entry in enumerate(ktss_header)
    ]


# Main
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("FE3H - Replace a KTSS audio in a ktsl2stbin file")
        print("First, give the filename of the ktsl2stbin, then the KTSS audio file to insert...")
        print("... then the index number, and finally the linked ktsl2asbin file")
        print("Usage: python ktsl2stbin-replace.py XXXX.ktsl2stbin XXXX.ktss <index> XXXX.ktsl2asbin")
        sys.exit(1)

    filename = sys.argv[1]
    new_audio = sys.argv[2]
    index = int(sys.argv[3])
    filename2 = sys.argv[4]

    # update ktsl2stbin
    with open(filename, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        parsed = parse_ktsl2stbin(data)
        ktss_header = parse_ktss_sections(data)

    if parsed["is_valid_ktsl2stbin"]:
        ktss_offsets = parsed["ktss_sections"]
        max_index = len(ktss_offsets)

        if index > max_index:
            print(f"Error: Your index was larger than the max (last entry): {max_index}")
            exit(1)

        cur_index = ktss_offsets[index-1]
        next_index = 0

        cur_entry = ktss_header[index-1]
        
        section_size = cur_entry["section_size"]
        link_id = cur_entry["link_id"] # for use in ktsl2asbin later
        kns_size = cur_entry["kns_size"]
        section_headersize = cur_entry["section_headersize"] # for use in ktsl2asbin later

        # offset start and end where KTSS audio needs to be removed and the new one inserted...
        # for now, we can calculate offset_start only
        offset_start = cur_index + HEADER_LENGTH
        ktss_orig_offset = offset_start # for KTSC files

        # read original file
        with open(filename, "rb") as f:
            original_data = bytearray(f.read())  # use bytearray so we can modify it in place

        # read the new audio binary data
        with open(new_audio, "rb") as f:
            new_audio_data = f.read()

        new_ktss = parse_ktss_audio(new_audio)
        new_ktss_length = len(new_audio_data)
        
        # KTSS should only have one sole entry in a file, this should be fine
        ktss_section_size_new = new_ktss[0]["section_size"]
        
        # These ones are for the ktsl2asbin file
        new_ktss_channel_count = new_ktss[0]["channel_count"]
        new_ktss_sample_rate = new_ktss[0]["sample_rate"]
        new_ktss_sample_count = new_ktss[0]["sample_count"]
        new_ktss_loop_start = new_ktss[0]["loop_start"]
        if new_ktss_loop_start == 0:
            new_ktss_loop_start = 0xFFFFFFFF

        # update the ktsl2stbin file in-place now
        section_size_offset = cur_entry["offset"] + 4
        kns_size_offset = cur_entry["offset"] + 16

        #if index == max_index: # the very final element also seems to account for the header itself
        original_data[section_size_offset:section_size_offset+4] = pack("<I", new_ktss_length + HEADER_LENGTH)
        #else:
        #    original_data[section_size_offset:section_size_offset+4] = pack("<I", new_ktss_length)
        original_data[kns_size_offset:kns_size_offset+4] = pack("<I", ktss_section_size_new)

        if index == max_index:
            offset_end = offset_start + section_size
        else:
            offset_end = offset_start + (section_size - HEADER_LENGTH)
        new_data = original_data[:offset_start] + new_audio_data + original_data[offset_end:]

        with open(filename, "wb") as f:
            f.write(new_data)

        print(f"Replaced index {index} successfully.")

        # update file size info too
        update_file_size(filename)
    else:
        print(f"Error: Not a valid ktsl2stbin file: {filename}")
        exit(1)

    # update ktsl2asbin
    with open(filename2, "r+b") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE) as data:
        parsed = parse_ktsl2asbin(data)
        parsed2 = parse_ktscbin(data)

        # Check and parse based on whether it's a KTSC or a regular ktsl2asbin (non-KTSC) file
        if data[:4] == MAGIC:
            info2_sections = parse_info2_sections(data)
        elif data[:4] == MAGIC2:
            ktsc_sections = parse_ktsc_sections(data)

        if parsed["is_valid_ktsl2asbin"]:
            # Find match for target_link_id from KTSS section
            match = next(
                (sec for sec in info2_sections
                 if any(k.startswith("link_id (") and sec[k] == link_id for k in sec)),
                None
            )

            if match:
                print(f"Found matching Link ID in INFO2 at offset: {match['offset']}")
                success = patch_info2_entry(
                    data=data,
                    match=match,
                    link_id=link_id,
                    offset_start=offset_start,
                    ktss_section_size_new=ktss_section_size_new,
                    new_ktss_channel_count=new_ktss_channel_count,
                    new_ktss_sample_rate=new_ktss_sample_rate,
                    new_ktss_sample_count=new_ktss_sample_count,
                    new_ktss_loop_start=new_ktss_loop_start,
                    verbose=True
                )
                
                if success:
                    # now update the ktss_offset values, unless it's the final index
                    delta = ktss_section_size_new - (section_size - section_headersize - 48)
                    if delta != 0 and index != max_index:
                        update_following_ktss_offsets(info2_sections, link_id, delta, data)

                    data.flush()
                    data.close()
                    f.close()
                    os.utime(filename2, None) # update timestamp manually
                    update_file_size(filename2) # update file size for ktsl2asbin, just in case it changes
            else:
                print(f"No matching INFO2 found for link_id {link_id} in: {filename2}")

        if parsed2["is_valid_ktsc"]:
            # Map KTSR Link ID to offset
            section = ktsc_sections[0]
            link_ids = section["ktsr_link_ids"]
            offsets = section["ktsr_offsets"]

            ktsr_map = [
                {"index": i+1, "link_id": link_id, "offset": offset}
                for i, (link_id, offset) in enumerate(zip(link_ids, offsets))
            ]

            ktsr_entry = next((entry for entry in ktsr_map if entry["link_id"] == link_id), None)
            
            if ktsr_entry:
                offset_start = ktsr_entry["offset"]
                print(f"Found embedded KTSR with link_id {link_id} at offset {offset_start}")

                # jump to KTSR block and treat it like another ktsl2asbin file
                data.seek(offset_start)
                
                # use the offset of the next KTSR to calculate block length
                current_offset = ktsr_entry["offset"]
                index = ktsr_entry["index"] - 1

                # determine block end
                if index + 1 < len(ktsr_map):
                    next_offset = ktsr_map[index + 1]["offset"]
                    block_end = next_offset
                else:
                    block_end = len(data)  # last block, go to EOF

                block_data = data[current_offset:block_end] # temporary use

                parsed_ktsr_entries = parse_info2_sections(block_data)
                if parsed_ktsr_entries:
                    adjusted_entry = adjust_offsets(parsed_ktsr_entries[0], offset_start)

                    success = patch_info2_entry(
                        data=data,
                        match=adjusted_entry,
                        link_id=link_id,
                        offset_start=ktss_orig_offset,
                        ktss_section_size_new=ktss_section_size_new,
                        new_ktss_channel_count=new_ktss_channel_count,
                        new_ktss_sample_rate=new_ktss_sample_rate,
                        new_ktss_sample_count=new_ktss_sample_count,
                        new_ktss_loop_start=new_ktss_loop_start,
                        verbose=True
                    )

                    if success:
                        if index != max_index:
                             # 1. Adjust all KTSR offsets (prob. not really needed, but may not hurt)
                            rebuild_ktsr_offsets(data)
                            # 2. Adjust KTSS offset
                            ktss_entries = get_updated_ktss_entries(filename)
                            update_following_ktsr_offsets(data, ktsr_map, index+1, ktss_entries)

                        data.flush()
                        data.close()
                        f.close()
                        os.utime(filename2, None)
            else:
                print(f"No INFO2 match inside KTSR block for link_id {link_id}")
