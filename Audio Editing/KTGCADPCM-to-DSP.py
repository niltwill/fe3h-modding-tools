from pathlib import Path
from struct import unpack, pack
import glob
import sys

FILE_MAGIC = 0x70CBCCC5
AUDIO_MAGIC = 0xE96FD86A
AUDIO_MAGIC2 = 0x27052510
HEADER_LENGTH = 32

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

    return audio_section

def construct_dsp_header(
    sample_count: int,
    nibble_count: int,
    sample_rate: int,
    end_address: int,
    coefficients: list,
    channel_index: int,
    custom: int
) -> bytes:
    # Initialize bytearray
    dsp_header = bytearray()

    # Pack standard fields
    dsp_header += pack(">I", sample_count)       # Sample count
    dsp_header += pack(">I", nibble_count)       # Nibble count
    dsp_header += pack(">I", sample_rate)        # Sample rate
    dsp_header += pack(">H", 0)                  # Loop flag
    dsp_header += pack(">H", 0)                  # Format
    dsp_header += pack(">I", 2)                  # Loop start address
    dsp_header += pack(">I", end_address)        # Loop end address
    dsp_header += pack(">I", 2)                  # Current address

    # Pack coefficients (16 values, 2 bytes each)
    for coeff in coefficients:
        dsp_header += pack(">H", coeff)

    # Gain (0 by default)
    dsp_header += pack(">H", 0)

    # Initial PS
    if custom == 0:
        # For non-custom files, use 0x00
        initial_ps = 0x00
    else:
        # each channel's Initial PS is spaced by 0x10 (16) to match interleaving offset
        initial_ps = 0x11 + ((channel_index - 1) * 0x10)

    dsp_header += pack(">H", initial_ps)

    # Remaining fields
    dsp_header += pack(">H", 0)  # Hist 1
    dsp_header += pack(">H", 0)  # Hist 2
    dsp_header += pack(">H", 0)  # Loop PS
    dsp_header += pack(">H", 0)  # Loop Hist 1
    dsp_header += pack(">H", 0)  # Loop Hist 2
    dsp_header += pack(">H", 0)  # Channel Count
    dsp_header += pack(">H", 0)  # Interleave size
    dsp_header += bytes(18)      # Padding to reach 96 bytes

    # Final validation
    assert len(dsp_header) == 96, "DSP header must be exactly 96 bytes!"

    return bytes(dsp_header)

def DivideBy2RoundUp(value):
    return (value // 2) + (value & 1)

# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Convert KTGCADPCM audio files to Nintendo DSP")
        print("Multi-channel is supported, but multiple streams aren't yet")
        print("For user generated DSP files, also add this letter as the third argument: 'c'")
        print("")
        print("Usage: python KTGCADPCM-to-DSP.py <file or pattern.vgmstream> [c]")
        sys.exit(1)

    # Wildcard pattern or single file
    pattern = sys.argv[1]
    custom = 1 if len(sys.argv) >= 3 and sys.argv[2].lower() == "c" else 0

    matched_files = sorted(glob.glob(pattern))
    if not matched_files:
        print(f"No files matched pattern: {pattern}")
        sys.exit(1)

    for filename in matched_files:
        print(f"Processing: {filename}")
        try:
            parsed = parse_audio_data(filename)

            for idx in range(parsed["num_channels"]):
                dsp_info = parsed["dsp_infos"][idx]
                stream = parsed["stream_data"][idx]

                nibble_count = dsp_info["duration"]
                sample_count = dsp_info["sampleCount"]
                sample_rate = dsp_info["sampleRate"]
                coefficients = dsp_info["coefficients"]
                end_address = nibble_count - 1

                dsp_header = construct_dsp_header(
                    sample_count,
                    nibble_count,
                    sample_rate,
                    end_address,
                    coefficients,
                    idx + 1,
                    custom
                )

                with open(filename, "rb") as f:
                    f.seek(stream["start"])
                    stream_data = f.read(stream["size"])

                if idx + 1 == 1:
                    out_path = Path(filename).parent / f"{Path(filename).stem}.dsp"
                else:
                    out_path = Path(filename).parent / f"{Path(filename).stem}{idx + 1}.dsp"

                with open(out_path, "wb") as out:
                    out.write(dsp_header)
                    out.write(stream_data)

                print(f"Wrote channel {idx + 1} to DSP file: '{out_path}'")
        except Exception as e:
            print(f"Error processing '{filename}': {e}")