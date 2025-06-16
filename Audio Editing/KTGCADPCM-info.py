from pathlib import Path
from struct import unpack
import sys

FILE_MAGIC = 0x70CBCCC5
AUDIO_MAGIC = 0xE96FD86A
HEADER_LENGTH = 32

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

    print(header_sections)
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

    print(audio_sections)
    return audio_sections


# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Display verbose information about KTGCADPCM audio files")
        print("(This is used as basis for editing/understanding its structure)")
        print("For simplicity reasons, this only handles the structure of original files")
        print("Usage: python KTGCADPCM-info.py XXX.vgmstream")
        sys.exit(1)

    filename = sys.argv[1]
    
    print("Standard header")
    parsed = parse_ktgcadpcm_header(filename)
    
    print("")
    print("Audio data")
    parsed = parse_audio_data(filename)
