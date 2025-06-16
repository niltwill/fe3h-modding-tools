from struct import unpack
import sys

HEADER_SIZE = 96  # Each DSP header is 78 + 18 padding = 96 bytes

def read_dsp_header(data, offset):
    fields = unpack(">IIIHHIII16H9H", data[offset:offset + 78])
    header = {
        "SampleCount": fields[0],
        "NibbleCount": fields[1],
        "SampleRate": fields[2],
        "LoopFlag": fields[3],
        "AudioFormat": fields[4],
        "StartAddress": fields[5],
        "EndAddress": fields[6],
        "CurrentAddress": fields[7],
    }

    # Coefficients
    for i in range(16):
        header[f"Coefficient{i + 1}"] = fields[8 + i]

    header["Gain"] = fields[24]
    header["InitialPredictorScale"] = hex(fields[25])
    header["History1"] = fields[26]
    header["History2"] = fields[27]
    header["LoopPredictorScale"] = hex(fields[28])
    header["LoopHistory1"] = fields[29]
    header["LoopHistory2"] = fields[30]
    header["ChannelCount"] = fields[31]
    header["InterleaveSizeFrames"] = fields[32]

    return header

def parse_dsp_header(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    offset = 0
    headers = []
    #total_data_len = len(data)

    # Read first header
    header1 = read_dsp_header(data, offset)
    headers.append(header1)
    offset += HEADER_SIZE

    # Read additional headers if ChannelCount > 1
    for i in range(1, header1["ChannelCount"]):
        header_n = read_dsp_header(data, offset)
        headers.append(header_n)
        offset += HEADER_SIZE

    # Optionally compute total audio data length
    # nibble_count is shared per channel, divide to get bytes per channel
    audio_data_length = (header1["NibbleCount"] + 1) // 2
    #print(f"\nTotal Audio Data Length: {audio_data_length} bytes")

    for idx, h in enumerate(headers):
        print(f"\nHeader {idx + 1}")
        for key, value in h.items():
            print(f"  {key}: {value}")
            
    # Calculate interleaved blocks if multichannel
    if header1["ChannelCount"] > 1:
        calculate_interleaved_blocks(header1)

    return headers

def divide_by_2_round_up(value):
    return (value // 2) + (value % 2)

def get_next_multiple(value, multiple):
    return ((value + multiple - 1) // multiple) * multiple

def calculate_interleaved_blocks(header):
    nibble_count = header["NibbleCount"]
    channel_count = header["ChannelCount"]
    interleave_size = header["InterleaveSizeFrames"] * 8  # bytes
    total_audio_bytes = divide_by_2_round_up(nibble_count)

    print(f"\nInterleave Size per Channel: {interleave_size} bytes")
    print(f"Total Audio Data Length: {total_audio_bytes} bytes\n")

    blocks = []
    audio_offset = 96 * channel_count  # skip all headers
    remaining_bytes = total_audio_bytes
    block_idx = 0

    while remaining_bytes > 0:
        block = {}
        block_size = min(interleave_size, remaining_bytes)
        block["BlockIndex"] = block_idx
        block["TotalSize"] = 0
        block["RangeStart"] = audio_offset
        block["Channels"] = []

        block_start_offset = audio_offset

        for ch in range(channel_count):
            ch_data_start = audio_offset
            ch_padding = get_next_multiple(block_size, 8) - block_size
            ch_total = block_size + ch_padding
            ch_data_end = ch_data_start + ch_total - 1

            block["Channels"].append({
                "Index": ch,
                "DataSize": block_size,
                "Padding": ch_padding,
                "TotalSize": ch_total,
                "Start": ch_data_start,
                "End": ch_data_end
            })

            audio_offset += ch_total
            block["TotalSize"] += ch_total

        block["RangeEnd"] = audio_offset - 1
        blocks.append(block)
        remaining_bytes -= block_size
        block_idx += 1

    # Print formatted output
    for blk in blocks:
        blk_size = blk["TotalSize"]
        blk_start = blk["RangeStart"]
        blk_end = blk["RangeEnd"]
        print(f"block[{blk['BlockIndex']}] - {blk_size} [0x{blk_size:04X}] bytes "
              f"(Range: {blk_start} [0x{blk_start:04X}] to {blk_end} [0x{blk_end:04X}])")

        for ch in blk["Channels"]:
            ch_idx = ch["Index"]
            ch_total = ch["TotalSize"]
            ch_start = ch["Start"]
            ch_end = ch["End"]
            print(f" * channel[{ch_idx}] - {ch_total} [0x{ch_total:04X}] bytes "
                  f"(Range: {ch_start} [0x{ch_start:04X}] to {ch_end} [0x{ch_end:04X}])")
        print()

    return blocks

# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Display verbose information about Nintendo DSP audio files")
        print("Usage: python dsp-info.py XXX.dsp")
        sys.exit(1)

    parse_dsp_header(sys.argv[1])
