from pathlib import Path
from struct import unpack
import sys

FILE_MAGIC = 0x70CBCCC5
AUDIO_MAGIC = 0xE96FD86A
AUDIO_MAGIC2 = 0x27052510
HEADER_LENGTH = 32

# Returns (string, new_offset). Tries to decode until null-byte, else fallback.
def parse_null_terminated_string(data, offset):
    end = data.find(b'\x00', offset)
    if end == -1:
        end = len(data)
    raw_bytes = data[offset:end]
    try:
        result = raw_bytes.decode('utf-8')
    except UnicodeDecodeError:
        result = ''
    return result, end + 1

# Read header entries
def parse_ktgcadpcm_header(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    offset = 0
    magic = unpack("<I", data[offset:offset+4])[0]

    if magic != FILE_MAGIC:
        raise ValueError("Invalid KTGADPCM magic header!")

    offset = 4
    total_filesize = unpack("<I", data[offset:offset+4])[0]
    section_headerlink = unpack("<I", data[offset+4:offset+8])[0]
    unk_12 = unpack("<I", data[offset+8:offset+12])[0]
    stream_count = unpack("<I", data[offset+12:offset+16])[0]
    pointer_table = unpack("<I", data[offset+16:offset+20])[0]

    names = []
    names_offset = offset + 20
    for i in range(stream_count):
        name, names_offset = parse_null_terminated_string(data, names_offset)
        if not name: # fallback to numeric string
            name = str(i)
        names.append(name)

    # Move to pointer table to read all stream pointers
    pointers = []
    for i in range(stream_count):
        ptr_offset = pointer_table + (i * 4)
        pointer = unpack("<I", data[ptr_offset:ptr_offset + 4])[0]
        pointers.append(pointer)

    header_info = {
        "total_filesize": total_filesize,
        "section_headerlink": section_headerlink,
        "unk_12": unk_12,
        "stream_count": stream_count,
        "pointer_table": pointer_table,
        "names": names,
        "pointers": pointers
    }

    print(header_info)
    return header_info

# Read audio data with multi-channel support
def parse_audio_data(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    offset = HEADER_LENGTH
    magic = unpack("<I", data[offset:offset+4])[0]
    if magic != AUDIO_MAGIC and magic != AUDIO_MAGIC2:
        raise ValueError("Invalid audio header!")

    base_offset = HEADER_LENGTH
    offset += 4

    audio_datasize = unpack("<I", data[offset:offset+4])[0]
    file_linkID = unpack("<I", data[offset+4:offset+8])[0]
    num_channels = unpack("<I", data[offset+8:offset+12])[0]
    unk_48 = unpack("<I", data[offset+12:offset+16])[0]
    sample_rate = unpack("<I", data[offset+16:offset+20])[0]
    duration = unpack("<I", data[offset+20:offset+24])[0]
    unk_60 = unpack("<I", data[offset+24:offset+28])[0]
    alwaysFF = hex(unpack("<I", data[offset+28:offset+32])[0])
    unk_68 = unpack("<I", data[offset+32:offset+36])[0]
    dsp_info_pointer = unpack("<I", data[offset+36:offset+40])[0]
    dsp_info_size = unpack("<I", data[offset+40:offset+44])[0]
    stream_pointer_table_pointer = unpack("<I", data[offset+44:offset+48])[0]
    stream_size_table_pointer = unpack("<I", data[offset+48:offset+52])[0]

    # Read DSP info for all channels
    dsp_infos = []
    for ch in range(num_channels):
        base = base_offset + dsp_info_pointer + (ch * 96)
        info = {
            "duration": unpack("<I", data[base:base+4])[0],
            "sampleCount": unpack("<I", data[base+4:base+8])[0],
            "sampleRate": unpack("<I", data[base+8:base+12])[0],
            "unk_16": unpack("<I", data[base+12:base+16])[0],
            "unk_20": unpack("<I", data[base+16:base+20])[0],
            "clippedSampleCount": unpack("<I", data[base+20:base+24])[0],
            "unk_28": unpack("<I", data[base+24:base+28])[0],
            "coefficients": [unpack("<H", data[base+28+i*2:base+30+i*2])[0] for i in range(16)],
        }
        dsp_infos.append(info)

    # Read stream pointers and sizes
    stream_pointers = []
    stream_sizes = []
    for ch in range(num_channels):
        ptr_offset = base_offset + stream_pointer_table_pointer + (ch * 4)
        size_offset = base_offset + stream_size_table_pointer + (ch * 4)
        stream_pointers.append(unpack("<I", data[ptr_offset:ptr_offset+4])[0])
        stream_sizes.append(unpack("<I", data[size_offset:size_offset+4])[0])

    # Compute stream data locations
    stream_data = []
    for ch in range(num_channels):
        begin = base_offset + stream_pointers[ch]
        end = begin + stream_sizes[ch] - 1
        stream_data.append({
            "channel": ch,
            "start": begin,
            "end": end,
            "size": stream_sizes[ch],
            "pointer": stream_pointers[ch]
        })

    audio_section = {
        "audio_datasize": audio_datasize,
        "file_linkID": file_linkID,
        "num_channels": num_channels,
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
        "dsp_infos": dsp_infos,
        "stream_data": stream_data,
    }

    print(audio_section)
    return audio_section


# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Display verbose information about KTGCADPCM audio files")
        print("(This is used as basis for editing/understanding its structure)")
        print("Usage: python KTGCADPCM-info.py XXX.vgmstream")
        sys.exit(1)

    filename = sys.argv[1]

    print("KTGCADPCM header")
    parsed = parse_ktgcadpcm_header(filename)

    print("")
    print("Audio data")
    parsed = parse_audio_data(filename)
