from pathlib import Path
from struct import unpack, pack
import sys

FILE_MAGIC = 0x70CBCCC5
AUDIO_MAGIC = 0xE96FD86A
HEADER_LENGTH = 32

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


def DivideBy2RoundUp(value):
    return (value // 2) + (value & 1)

# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Convert KTGCADPCM audio files to Nintendo DSP")
        print("For simplicity reasons, this only handles the structure of original files")
        print("(So only 1 channel, 1 audio stream)")
        print("For user generated DSP files, also add this letter as the third argument: 'c'")
        print("")
        print("Usage: python KTGCADPCM-to-DSP.py XXX.vgmstream [c]")
        sys.exit(1)

    filename = sys.argv[1]

    # Set default custom flag
    custom = 0

    # Check if optional third argument is provided
    if len(sys.argv) >= 3 and sys.argv[2].lower() == "c":
        custom = 0x11 # only works for 1 channel (mono) files

    parsed = parse_audio_data(filename)
    section = parsed[0]

    # Get the needed sections to create a DSP header and audio data to a new file
    sampleCount = section["dsp_info1_duration"]
    NibbleCount = section["dsp_info1_sampleCount"]
    SampleRate = section["dsp_info1_sampleRate"]
    EndAddress = NibbleCount - 1
    Coefficient1 = section["dsp_info1_coefficient1"]
    Coefficient2 = section["dsp_info1_coefficient2"]
    Coefficient3 = section["dsp_info1_coefficient3"]
    Coefficient4 = section["dsp_info1_coefficient4"]
    Coefficient5 = section["dsp_info1_coefficient5"]
    Coefficient6 = section["dsp_info1_coefficient6"]
    Coefficient7 = section["dsp_info1_coefficient7"]
    Coefficient8 = section["dsp_info1_coefficient8"]
    Coefficient9 = section["dsp_info1_coefficient9"]
    Coefficient10 = section["dsp_info1_coefficient10"]
    Coefficient11 = section["dsp_info1_coefficient11"]
    Coefficient12 = section["dsp_info1_coefficient12"]
    Coefficient13 = section["dsp_info1_coefficient13"]
    Coefficient14 = section["dsp_info1_coefficient14"]
    Coefficient15 = section["dsp_info1_coefficient15"]
    Coefficient16 = section["dsp_info1_coefficient16"]
    AudioData_Start = section["stream_data1_begin"]
    AudioData_End = section["stream_data1_end"]
    AudioData_Length = AudioData_End - AudioData_Start
    
    # Construct DSP header
    dsp_header = bytearray()

    dsp_header += pack(">I", sampleCount)      # Sample count
    dsp_header += pack(">I", NibbleCount)      # Nibble count
    dsp_header += pack(">I", SampleRate)       # Sample rate
    dsp_header += pack(">H", 0)                # Loop flag
    dsp_header += pack(">H", 0)                # Format
    dsp_header += pack(">I", 2)                # Loop start address
    dsp_header += pack(">I", EndAddress)       # Loop end address
    dsp_header += pack(">I", 2)                # Current address

    # Coefficients (16 * 2 bytes = 32 bytes total)
    for coeff in [
        Coefficient1, Coefficient2, Coefficient3, Coefficient4,
        Coefficient5, Coefficient6, Coefficient7, Coefficient8,
        Coefficient9, Coefficient10, Coefficient11, Coefficient12,
        Coefficient13, Coefficient14, Coefficient15, Coefficient16
    ]:
        dsp_header += pack(">H", coeff)

    dsp_header += pack(">H", 0)     # Gain
    #dsp_header += pack(">H", 0x11)  # Initial PS (0x11 needed for files generated with VGAudioCli, the game's files have 0x00 though)
    dsp_header += pack(">H", custom)  # Initial PS
    dsp_header += pack(">H", 0)     # Hist 1
    dsp_header += pack(">H", 0)     # Hist 2
    dsp_header += pack(">H", 0)     # Loop PS
    dsp_header += pack(">H", 0)     # Loop Hist 1
    dsp_header += pack(">H", 0)     # Loop Hist 2
    dsp_header += pack(">H", 0)     # Channel Count
    dsp_header += pack(">H", 0)     # Interleave size

    dsp_header += bytes(18)         # Padding to 96 bytes total

    assert len(dsp_header) == 96, "DSP header must be exactly 96 bytes"

    # Read raw audio stream
    with open(filename, "rb") as f:
        f.seek(AudioData_Start)
        #stream_data = f.read(DivideBy2RoundUp(NibbleCount))
        stream_data = f.read(AudioData_Length)

    # Create output filename
    out_path = Path(filename).with_suffix(".dsp")
    with open(out_path, "wb") as out:
        out.write(dsp_header)
        out.write(stream_data)

    print(f"Wrote to DSP file: '{out_path}'")
