from pathlib import Path
from struct import unpack, pack
import sys

FILE_MAGIC = 0x70CBCCC5
AUDIO_MAGIC = 0xE96FD86A
HEADER_LENGTH = 32
DSP_HEADER_LENGTH = 96

# Read header entries
def parse_dsp_header(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    offset = 0
    data_len = len(data)
    audiodata_len = (data_len - DSP_HEADER_LENGTH) + 1
    dsp_sections = []

    while offset + 4 <= data_len:
        SampleCount = unpack(">I", data[offset:offset+4])[0]
        NibbleCount = unpack(">I", data[offset+4:offset+8])[0]
        SampleRate = unpack(">I", data[offset+8:offset+12])[0]
        LoopFlag = unpack(">H", data[offset+12:offset+14])[0]
        AudioFormat = unpack(">H", data[offset+14:offset+16])[0]
        StartAddress = unpack(">I", data[offset+16:offset+20])[0]
        EndAddress = unpack(">I", data[offset+20:offset+24])[0]
        CurrentAddress = unpack(">I", data[offset+24:offset+28])[0]
        
        Coefficient1 = unpack(">H", data[offset+28:offset+30])[0]
        Coefficient2 = unpack(">H", data[offset+30:offset+32])[0]
        Coefficient3 = unpack(">H", data[offset+32:offset+34])[0]
        Coefficient4 = unpack(">H", data[offset+34:offset+36])[0]
        Coefficient5 = unpack(">H", data[offset+36:offset+38])[0]
        Coefficient6 = unpack(">H", data[offset+38:offset+40])[0]
        Coefficient7 = unpack(">H", data[offset+40:offset+42])[0]
        Coefficient8 = unpack(">H", data[offset+42:offset+44])[0]
        Coefficient9 = unpack(">H", data[offset+44:offset+46])[0]
        Coefficient10 = unpack(">H", data[offset+46:offset+48])[0]
        Coefficient11 = unpack(">H", data[offset+48:offset+50])[0]
        Coefficient12 = unpack(">H", data[offset+50:offset+52])[0]
        Coefficient13 = unpack(">H", data[offset+52:offset+54])[0]
        Coefficient14 = unpack(">H", data[offset+54:offset+56])[0]
        Coefficient15 = unpack(">H", data[offset+56:offset+58])[0]
        Coefficient16 = unpack(">H", data[offset+58:offset+60])[0]

        Gain = unpack(">H", data[offset+60:offset+62])[0]
        InitialPredictorScale = hex(unpack(">H", data[offset+62:offset+64])[0])
        History1 = unpack(">H", data[offset+64:offset+66])[0]
        History2 = unpack(">H", data[offset+66:offset+68])[0]
        LoopPredictorScale = hex(unpack(">H", data[offset+68:offset+70])[0])
        LoopHistory1 = unpack(">H", data[offset+70:offset+72])[0]
        LoopHistory2 = unpack(">H", data[offset+72:offset+74])[0]
        ChannelCount = unpack(">H", data[offset+74:offset+76])[0]
        InterleaveSizeFrames = unpack(">H", data[offset+76:offset+78])[0]
        # Here's some padding for 18 bytes, which marks the end of header, but this is not needed to know

        dsp_sections.append({
            "AudioData_Length": audiodata_len, # not in actual header data, but useful when changing KTGCADPCM
            "SampleCount": SampleCount,
            "NibbleCount": NibbleCount,
            "SampleRate": SampleRate,
            "LoopFlag": LoopFlag,
            "AudioFormat": AudioFormat,
            "StartAddress": StartAddress,
            "EndAddress": EndAddress,
            "CurrentAddress": CurrentAddress,
            "Coefficient1": Coefficient1,
            "Coefficient2": Coefficient2,
            "Coefficient3": Coefficient3,
            "Coefficient4": Coefficient4,
            "Coefficient5": Coefficient5,
            "Coefficient6": Coefficient6,
            "Coefficient7": Coefficient7,
            "Coefficient8": Coefficient8,
            "Coefficient9": Coefficient9,
            "Coefficient10": Coefficient10,
            "Coefficient11": Coefficient11,
            "Coefficient12": Coefficient12,
            "Coefficient13": Coefficient13,
            "Coefficient14": Coefficient14,
            "Coefficient15": Coefficient15,
            "Coefficient16": Coefficient16,
            "Gain": Gain,
            "InitialPredictorScale": InitialPredictorScale,
            "History1": History1,
            "History2": History2,
            "LoopPredictorScale": LoopPredictorScale,
            "LoopHistory1": LoopHistory1,
            "LoopHistory2": LoopHistory2,
            "ChannelCount": ChannelCount,
            "InterleaveSizeFrames": InterleaveSizeFrames
        })

        break

    return dsp_sections

# Read header entries
def parse_ktgcadpcm_header(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    offset = 0
    magic = unpack("<I", data[offset:offset+4])[0]

    # Check magic and type ID
    if magic != FILE_MAGIC:
        raise ValueError("Invalid KTGADPCM magic header!")

    offset = 4
    data_len = len(data)
    
    header_sections = []

    while offset + 4 <= data_len:
        total_filesize = unpack("<I", data[offset:offset+4])[0]
        section_headerlink = unpack("<I", data[offset+4:offset+8])[0]
        unk_12 = unpack("<I", data[offset+8:offset+12])[0]
        stream_count = unpack("<I", data[offset+12:offset+16])[0]
        pointer_table = unpack("<I", data[offset+16:offset+20])[0]

        names1 = unpack("<B", data[offset+20:offset+21])[0] # depending on stream_count, there could be more
        
        offset = pointer_table # go to pointer table
        pointers1 = unpack("<I", data[offset:offset+4])[0] # like before, this would need more entries based on stream_count

        header_sections.append({
            "total_filesize": total_filesize,
            "section_headerlink": section_headerlink,
            "unk_12": unk_12,
            "stream_count": stream_count,
            "pointer_table": pointer_table,
            "names1": names1,
            "pointers1": pointers1
        })

        break

    return header_sections

# Read audio data
def parse_audio_data(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    offset = HEADER_LENGTH
    magic = unpack("<I", data[offset:offset+4])[0]

    # Check magic and type ID
    if magic != AUDIO_MAGIC:
        raise ValueError("Invalid audio header!")

    offset = HEADER_LENGTH + 4
    data_len = len(data)

    audio_sections = []

    while offset + 4 <= data_len:
        audio_datasize = unpack("<I", data[offset:offset+4])[0] # Audio Data size (Total File Size - 32)
        file_linkID = unpack("<I", data[offset+4:offset+8])[0]
        num_Channels = unpack("<I", data[offset+8:offset+12])[0]
        unk_48 = unpack("<I", data[offset+12:offset+16])[0]
        sample_rate = unpack("<I", data[offset+16:offset+20])[0]
        duration = unpack("<I", data[offset+20:offset+24])[0] # Duration = numOfSamples - (numOfSamples/8)
        unk_60 = unpack("<I", data[offset+24:offset+28])[0]
        alwaysFF = hex(unpack("<I", data[offset+28:offset+32])[0])
        unk_68 = unpack("<I", data[offset+32:offset+36])[0]
        dsp_info_pointer = unpack("<I", data[offset+36:offset+40])[0]
        dsp_info_size = unpack("<I", data[offset+40:offset+44])[0]
        stream_pointer_table_pointer = unpack("<I", data[offset+44:offset+48])[0]
        stream_size_table_pointer = unpack("<I", data[offset+48:offset+52])[0]
        
        offset = HEADER_LENGTH + dsp_info_pointer # from the start, including the magic hex, this DSP section is 96 bytes (each)
        # for simplicity, only one channel is handled here as in the original
        dsp_info1_duration = unpack("<I", data[offset:offset+4])[0] # Duration = numOfSamples - (numOfSamples/8)
        dsp_info1_sampleCount = unpack("<I", data[offset+4:offset+8])[0]
        dsp_info1_sampleRate = unpack("<I", data[offset+8:offset+12])[0]
        dsp_info1_unk_16 = unpack("<I", data[offset+12:offset+16])[0]
        dsp_info1_unk_20 = unpack("<I", data[offset+16:offset+20])[0]
        dsp_info1_clippedSampleCount = unpack("<I", data[offset+20:offset+24])[0]
        dsp_info1_unk_28 = unpack("<I", data[offset+24:offset+28])[0]

        dsp_info1_coefficient1 = unpack("<H", data[offset+28:offset+30])[0]
        dsp_info1_coefficient2 = unpack("<H", data[offset+30:offset+32])[0]
        dsp_info1_coefficient3 = unpack("<H", data[offset+32:offset+34])[0]
        dsp_info1_coefficient4 = unpack("<H", data[offset+34:offset+36])[0]
        dsp_info1_coefficient5 = unpack("<H", data[offset+36:offset+38])[0]
        dsp_info1_coefficient6 = unpack("<H", data[offset+38:offset+40])[0]
        dsp_info1_coefficient7 = unpack("<H", data[offset+40:offset+42])[0]
        dsp_info1_coefficient8 = unpack("<H", data[offset+42:offset+44])[0]
        dsp_info1_coefficient9 = unpack("<H", data[offset+44:offset+46])[0]
        dsp_info1_coefficient10 = unpack("<H", data[offset+46:offset+48])[0]
        dsp_info1_coefficient11 = unpack("<H", data[offset+48:offset+50])[0]
        dsp_info1_coefficient12 = unpack("<H", data[offset+50:offset+52])[0]
        dsp_info1_coefficient13 = unpack("<H", data[offset+52:offset+54])[0]
        dsp_info1_coefficient14 = unpack("<H", data[offset+54:offset+56])[0]
        dsp_info1_coefficient15 = unpack("<H", data[offset+56:offset+58])[0]
        dsp_info1_coefficient16 = unpack("<H", data[offset+58:offset+60])[0]
        
        # now we have a padding here with 36 bytes, this is not included

        offset = HEADER_LENGTH + stream_pointer_table_pointer
        stream_pointers1 = unpack("<I", data[offset:offset+4])[0] # only for one channel here

        offset = HEADER_LENGTH + stream_size_table_pointer
        stream_sizes1 = unpack("<I", data[offset:offset+4])[0] # only for one channel here
        
        # this is going to be the Stream_Data (audio stream data, finally!)
        offset = HEADER_LENGTH + stream_pointers1
        stream_data1_begin = offset
        stream_data1_end = offset + (stream_sizes1 - 1)

        audio_sections.append({
            "audio_datasize": audio_datasize,
            "file_linkID": file_linkID,
            "num_Channels": num_Channels,
            "unk_48": unk_48,
            "sample_rate": sample_rate,
            "duration": duration,
            "unk_60": unk_60,
            "alwaysFF": alwaysFF,
            "unk_68": unk_68,
            "dsp_info_pointer": dsp_info_pointer,
            "dsp_info_size": dsp_info_size,
            "stream_pointer_table_pointer": stream_pointer_table_pointer,
            "stream_size_table_pointer": stream_size_table_pointer,
            "dsp_info1_duration": dsp_info1_duration,
            "dsp_info1_sampleCount": dsp_info1_sampleCount,
            "dsp_info1_sampleRate": dsp_info1_sampleRate,
            "dsp_info1_unk_16": dsp_info1_unk_16,
            "dsp_info1_unk_20": dsp_info1_unk_20,
            "dsp_info1_clippedSampleCount": dsp_info1_clippedSampleCount,
            "dsp_info1_unk_28": dsp_info1_unk_28,
            "dsp_info1_coefficient1": dsp_info1_coefficient1,
            "dsp_info1_coefficient2": dsp_info1_coefficient2,
            "dsp_info1_coefficient3": dsp_info1_coefficient3,
            "dsp_info1_coefficient4": dsp_info1_coefficient4,
            "dsp_info1_coefficient5": dsp_info1_coefficient5,
            "dsp_info1_coefficient6": dsp_info1_coefficient6,
            "dsp_info1_coefficient7": dsp_info1_coefficient7,
            "dsp_info1_coefficient8": dsp_info1_coefficient8,
            "dsp_info1_coefficient9": dsp_info1_coefficient9,
            "dsp_info1_coefficient10": dsp_info1_coefficient10,
            "dsp_info1_coefficient11": dsp_info1_coefficient11,
            "dsp_info1_coefficient12": dsp_info1_coefficient12,
            "dsp_info1_coefficient13": dsp_info1_coefficient13,
            "dsp_info1_coefficient14": dsp_info1_coefficient14,
            "dsp_info1_coefficient15": dsp_info1_coefficient15,
            "dsp_info1_coefficient16": dsp_info1_coefficient16,
            "stream_pointers1": stream_pointers1,
            "stream_sizes1": stream_sizes1,
            "stream_data1_begin": stream_data1_begin,
            "stream_data1_end": stream_data1_end
        })

        break

    return audio_sections


def remove_bytes(binary_file, start, end):
    with open(binary_file, "r+b") as f:
        f.seek(end)
        remaining_bytes = f.read()
        f.seek(start)
        f.write(remaining_bytes)
        f.truncate(start + len(remaining_bytes))
        return True


def insert_bytes(binary_file, start, insert_data):
    with open(binary_file, "r+b") as f:
        f.seek(start)
        tail = f.read()
        f.seek(start)
        f.write(insert_data)
        f.write(tail)


def read_data_from_offset(file_path, offset):
    with open(file_path, "rb") as f:
        f.seek(offset)
        return f.read()  # Reads from offset to end


def update_audio_metadata(file_path, section, updates):
    with open(file_path, "r+b") as f:
        # Update audio_datasize (offset +4 from section start)
        if "audio_datasize" in updates:
            f.seek(HEADER_LENGTH + 4)
            f.write(pack("<I", updates["audio_datasize"]))

        # Update sample_rate (offset +16 in section)
        if "sample_rate" in updates:
            f.seek(HEADER_LENGTH + 20)  # HEADER + 4 (magic) + 16
            f.write(pack("<I", updates["sample_rate"]))

        # Update duration1 (offset +20 in section)
        if "duration1" in updates:
            f.seek(HEADER_LENGTH + 24)
            f.write(pack("<I", updates["duration1"]))

        # Update stream_sizes1
        if "stream_sizes1" in updates:
            f.seek(HEADER_LENGTH + section["stream_size_table_pointer"])
            f.write(pack("<I", updates["stream_sizes1"]))

        # --- DSP Info Section ---
        dsp_base = HEADER_LENGTH + section["dsp_info_pointer"]

        if "dsp_info1_sampleRate" in updates:
            f.seek(dsp_base + 8)
            f.write(pack("<I", updates["dsp_info1_sampleRate"]))

        if "duration2" in updates:
            f.seek(dsp_base + 0)
            f.write(pack("<I", updates["duration2"]))

        if "sampleCount" in updates:
            f.seek(dsp_base + 4)
            f.write(pack("<I", updates["sampleCount"]))

        if "clippedSampleCount" in updates:
            f.seek(dsp_base + 20)
            f.write(pack("<I", updates["clippedSampleCount"]))

        # Coefficients: dsp_info1_coefficient1 to dsp_info1_coefficient16
        for i in range(16):
            key = f"coefficient{i+1}"
            if key in updates:
                f.seek(dsp_base + 28 + (i * 2))
                f.write(pack("<H", updates[key]))


def update_ktgcadpcm_header(file_path, updates):
    with open(file_path, "r+b") as f:
        # Skip magic (first 4 bytes)
        base_offset = 4

        if "total_filesize" in updates:
            f.seek(base_offset + 0)
            f.write(pack("<I", updates["total_filesize"]))

        if "section_headerlink" in updates:
            f.seek(base_offset + 4)
            f.write(pack("<I", updates["section_headerlink"]))

        if "unk_12" in updates:
            f.seek(base_offset + 8)
            f.write(pack("<I", updates["unk_12"]))

        if "stream_count" in updates:
            f.seek(base_offset + 12)
            f.write(pack("<I", updates["stream_count"]))

        if "pointer_table" in updates:
            f.seek(base_offset + 16)
            f.write(pack("<I", updates["pointer_table"]))

        if "names1" in updates:
            f.seek(base_offset + 20)
            f.write(pack("<B", updates["names1"]))  # 1 byte

        if "pointers1" in updates:
            # Must read pointer_table offset first
            f.seek(base_offset + 16)
            pointer_table = unpack("<I", f.read(4))[0]

            f.seek(pointer_table)
            f.write(pack("<I", updates["pointers1"]))


def get_file_size(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return len(data)
    
def fix_padding(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    total_size = len(data)
    remainder = total_size % 16

    if remainder == 0:
        padding_needed = 0
    else:
        padding_needed = 16 - remainder

    padded_data = data + (b"\x00" * padding_needed)

    with open(file_path, "wb") as f:
        f.write(padded_data)

# Main
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("FE3H - replace DSP audio in KTGCADPCM game files")
        print("For simplicity reasons, this only handles the structure of original files")
        print("So only 1 channel, 1 audio stream is supported with this")
        print("Usage: python DSP-to-KTGCADPCM.py <XXX.dsp> <XXX.vgmstream>")
        sys.exit(1)

    dsp_file = sys.argv[1]
    out_file = sys.argv[2]

    # 1. Parse DSP header
    parsed1 = parse_dsp_header(dsp_file)
    section_dsp = parsed1[0]

    new_StreamSize = section_dsp["AudioData_Length"]
    new_SampleRate = section_dsp["SampleRate"]
    new_SampleCount = section_dsp["NibbleCount"]
    new_Duration = round(new_SampleCount - (new_SampleCount / 8)) # this must be rounded to the nearest integer
    new_clippedSampleCount = new_SampleCount - 1

    new_coef1 = section_dsp["Coefficient1"]
    new_coef2 = section_dsp["Coefficient2"]
    new_coef3 = section_dsp["Coefficient3"]
    new_coef4 = section_dsp["Coefficient4"]
    new_coef5 = section_dsp["Coefficient5"]
    new_coef6 = section_dsp["Coefficient6"]
    new_coef7 = section_dsp["Coefficient7"]
    new_coef8 = section_dsp["Coefficient8"]
    new_coef9 = section_dsp["Coefficient9"]
    new_coef10 = section_dsp["Coefficient10"]
    new_coef11 = section_dsp["Coefficient11"]
    new_coef12 = section_dsp["Coefficient12"]
    new_coef13 = section_dsp["Coefficient13"]
    new_coef14 = section_dsp["Coefficient14"]
    new_coef15 = section_dsp["Coefficient15"]
    new_coef16 = section_dsp["Coefficient16"]

    # Parse header sections
    parsed2 = parse_ktgcadpcm_header(out_file)
    section_out1 = parsed2[0]

    total_filesize = section_out1["total_filesize"]

    # Parse audio sections
    parsed3 = parse_audio_data(out_file)
    section_out2 = parsed3[0]

    audio_datasize = section_out2["audio_datasize"]
    sample_rate = section_out2["sample_rate"]
    dsp_info1_sampleRate = section_out2["dsp_info1_sampleRate"]
    duration1 = section_out2["duration"]
    duration2 = section_out2["dsp_info1_duration"]
    sampleCount = section_out2["dsp_info1_sampleCount"]
    clippedSampleCount = section_out2["dsp_info1_clippedSampleCount"]
    coefficient1 = section_out2["dsp_info1_coefficient1"]
    coefficient2 = section_out2["dsp_info1_coefficient2"]
    coefficient3 = section_out2["dsp_info1_coefficient3"]
    coefficient4 = section_out2["dsp_info1_coefficient4"]
    coefficient5 = section_out2["dsp_info1_coefficient5"]
    coefficient6 = section_out2["dsp_info1_coefficient6"]
    coefficient7 = section_out2["dsp_info1_coefficient7"]
    coefficient8 = section_out2["dsp_info1_coefficient8"]
    coefficient9 = section_out2["dsp_info1_coefficient9"]
    coefficient10 = section_out2["dsp_info1_coefficient10"]
    coefficient11 = section_out2["dsp_info1_coefficient11"]
    coefficient12 = section_out2["dsp_info1_coefficient12"]
    coefficient13 = section_out2["dsp_info1_coefficient13"]
    coefficient14 = section_out2["dsp_info1_coefficient14"]
    coefficient15 = section_out2["dsp_info1_coefficient15"]
    coefficient16 = section_out2["dsp_info1_coefficient16"]
    stream_sizes1 = section_out2["stream_sizes1"]
    stream_data1_begin = section_out2["stream_data1_begin"]
    stream_data1_end = section_out2["stream_data1_end"]

    # 1. Remove old audio stream
    remove_bytes(out_file, stream_data1_begin, stream_data1_end)

    # 2. Insert new audio stream
    new_audio = read_data_from_offset(dsp_file, DSP_HEADER_LENGTH)
    insert_bytes(out_file, stream_data1_begin, new_audio)

    # 3. Change most values as needed
    updates = {
        "sample_rate": new_SampleRate,
        "dsp_info1_sampleRate": new_SampleRate,
        "duration1": new_Duration,
        "duration2": new_Duration,
        "sampleCount": new_SampleCount,
        "clippedSampleCount": new_clippedSampleCount,
        "coefficient1": new_coef1,
        "coefficient2": new_coef2,
        "coefficient3": new_coef3,
        "coefficient4": new_coef4,
        "coefficient5": new_coef5,
        "coefficient6": new_coef6,
        "coefficient7": new_coef7,
        "coefficient8": new_coef8,
        "coefficient9": new_coef9,
        "coefficient10": new_coef10,
        "coefficient11": new_coef11,
        "coefficient12": new_coef12,
        "coefficient13": new_coef13,
        "coefficient14": new_coef14,
        "coefficient15": new_coef15,
        "coefficient16": new_coef16,
        "stream_sizes1": new_StreamSize,
    }
    update_audio_metadata(out_file, section_out2, updates)

    # 4. Calculate the new filesize and update two entries
    new_totalFileSize = get_file_size(out_file)
    new_audioDataSize = new_totalFileSize - 32

    header_updates = { "total_filesize": new_totalFileSize }
    update_ktgcadpcm_header(out_file, header_updates)

    updates = {"audio_datasize": new_audioDataSize}
    update_audio_metadata(out_file, section_out2, updates)

    # Add some padding as needed
    fix_padding(out_file)

    print(f"Modified the KTGCADPCM file: '{out_file}' with the DSP file: '{dsp_file}'")
