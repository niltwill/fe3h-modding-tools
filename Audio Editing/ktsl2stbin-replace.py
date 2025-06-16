import mmap
import os
import time
import sys
from pathlib import Path
from struct import pack, unpack

# Define hex markers and other constants
MAGIC = b"KTSR"
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
        new_offset = old_offset + delta

        # In-place patch
        data.seek(ktss_offset_addr)
        data.write(pack("<I", new_offset))

        #print(f"  -> link_id {section[next(k for k in section if k.startswith('link_id ('))]}:")
        #print(f"     old_offset = {old_offset}, new_offset = {new_offset}")


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

    with open(filename, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        parsed = parse_ktsl2stbin(data)
        ktss_header = parse_ktss_sections(data)

    #parsed = parse_ktsl2stbin(filename)
    if parsed["is_valid_ktsl2stbin"]:

        ktss_offsets = parsed["ktss_sections"]
        max_index = len(ktss_offsets)

        if index > max_index:
            print(f"Error: Your index was larger than the max (last entry): {max_index}")
            exit(1)

        cur_index = ktss_offsets[index-1]
        next_index = 0
        
        #ktss_header = parse_ktss_sections(filename)
        cur_entry = ktss_header[index-1]
        
        section_size = cur_entry["section_size"]
        link_id = cur_entry["link_id"] # for use in ktsl2asbin later
        kns_size = cur_entry["kns_size"]
        section_headersize = cur_entry["section_headersize"] # for use in ktsl2asbin later

        # offset start and end where KTSS audio needs to be removed and the new one inserted...
        # for now, we can calculate offset_start only
        offset_start = cur_index + HEADER_LENGTH

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
        print(f"Error: Not a valid ktsl2stbin file: {filename}")
        exit(1)

    # update ktsl2asbin
    with open(filename2, "r+b") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE) as data:
        parsed = parse_ktsl2asbin(data)
        info2_sections = parse_info2_sections(data)

        if parsed["is_valid_ktsl2asbin"]:        
            # Find match for target_link_id from KTSS section
            #match = next((sec for sec in info2_sections if sec["link_id"] == link_id), None)
            match = next(
                (sec for sec in info2_sections
                 if any(k.startswith("link_id (") and sec[k] == link_id for k in sec)),
                None
            )

            if match:
                print(f"Found matching Link ID in INFO2 at offset: {match['offset']}")
                #info2_offset = match['offset']

                # Find exact field offsets dynamically
                channel_count_field = next(k for k in match if k.startswith("channel_count ("))
                sample_rate_field = next(k for k in match if k.startswith("sample_rate ("))
                sample_count_field = next(k for k in match if k.startswith("sample_count ("))
                loop_start_field = next(k for k in match if k.startswith("loop_start ("))            
                ktss_offset_field = next(k for k in match if k.startswith("ktss_offset ("))
                ktss_size_field = next(k for k in match if k.startswith("ktss_size ("))

                channel_count_addr = int(channel_count_field.split("(")[1].split(")")[0])
                sample_rate_addr = int(sample_rate_field.split("(")[1].split(")")[0])
                sample_count_addr = int(sample_count_field.split("(")[1].split(")")[0])
                loop_start_addr = int(loop_start_field.split("(")[1].split(")")[0])
                ktss_offset_addr = int(ktss_offset_field.split("(")[1].split(")")[0])
                ktss_size_addr = int(ktss_size_field.split("(")[1].split(")")[0])

                # Write the new values
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

                print(f"Patched INFO2 entry:")
                print(f"  -> channel_count = {new_ktss_channel_count} (from {match[channel_count_field]})")
                print(f"  -> sample_rate   = {new_ktss_sample_rate} (from {match[sample_rate_field]})")
                print(f"  -> sample_count  = {new_ktss_sample_count} (from {match[sample_count_field]})")
                print(f"  -> loop_start    = {new_ktss_loop_start} (from {match[loop_start_field]})")
                print(f"  -> ktss_offset   = {offset_start} (from {match[ktss_offset_field]})")
                print(f"  -> ktss_size     = {ktss_section_size_new} (from {match[ktss_size_field]})")

                # now update the ktss_offset values, unless it's the final index
                delta = ktss_section_size_new - (section_size - section_headersize - 48)
                if delta != 0 and index != max_index:
                    update_following_ktss_offsets(info2_sections, link_id, delta, data)

                data.flush()
                data.close()
                f.close()

                os.utime(filename2, None) # update timestamp manually
            else:
                print(f"No matching INFO2 found for link_id {link_id} in: {filename2}")
        else:
            print(f"Error: Not a valid ktsl2asbin file: {filename2}")
            exit(1)
