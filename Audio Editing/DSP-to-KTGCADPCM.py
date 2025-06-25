import sys
from pathlib import Path
from struct import unpack, pack, pack_into

# --- Constants ---
# Magic numbers to identify file and section types.
FILE_MAGIC = 0x70CBCCC5
AUDIO_MAGIC = 0xE96FD86A
# The fixed size of the top-level KTGCADPCM header.
KTGC_HEADER_LENGTH = 32
# The fixed size of a single DSP header block.
DSP_HEADER_LENGTH = 96

# ==============================================================================
# SECTION 1: DSP FILE PARSING
# Functions for reading the source `.dsp` audio files.
# ==============================================================================

def read_dsp_header(data, offset):
    """
    Reads a single 96-byte DSP header from a data block at a given offset.
    The format string ">IIIHHIII16H9H" unpacks 78 bytes of structured data.
    > endianness: Big-endian
    I: unsigned int (4 bytes)
    H: unsigned short (2 bytes)
    """
    if offset + 78 > len(data):
        raise ValueError("Not enough data to read a full DSP header.")
    
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
        "Coefficients": list(fields[8:24]), # Store coefficients as a list
        "Gain": fields[24],
        "InitialPredictorScale": fields[25],
        "History1": fields[26],
        "History2": fields[27],
        "LoopPredictorScale": fields[28],
        "LoopHistory1": fields[29],
        "LoopHistory2": fields[30],
        "ChannelCount": fields[31],
        "InterleaveSizeFrames": fields[32],
    }
    return header

def parse_dsp_file(dsp_file_path):
    """
    Parses a .dsp file, returning all channel headers and the raw audio data blob.
    It assumes headers are sequential at the start of the file.
    """
    with open(dsp_file_path, "rb") as f:
        data = f.read()

    headers = []
    if not data:
        raise ValueError(f"DSP file '{dsp_file_path}' is empty.")

    # Read the first header to determine the total number of channels.
    first_header = read_dsp_header(data, 0)
    headers.append(first_header)
    
    # The ChannelCount field in the first header dictates how many headers to read.
    # We trust this value to be accurate for the file's structure.
    channel_count = first_header.get("ChannelCount", 1)
    if channel_count <= 0:
        channel_count = 1

    # Read the remaining headers for a multi-channel file.
    for i in range(1, channel_count):
        offset = i * DSP_HEADER_LENGTH
        if len(data) < offset + DSP_HEADER_LENGTH:
            print(f"Warning: DSP file expects {channel_count} channels, but is truncated.", file=sys.stderr)
            break
        header_n = read_dsp_header(data, offset)
        headers.append(header_n)

    # The audio data begins immediately after the last header.
    audio_data_start_offset = len(headers) * DSP_HEADER_LENGTH
    audio_data_blob = data[audio_data_start_offset:]

    return headers, audio_data_blob

# ==============================================================================
# SECTION 2: KTGCADPCM FILE PARSING
# Functions for reading the target `.vgmstream`/`.ktgc` file format.
# These operate on a bytearray for safe, in-memory processing.
# ==============================================================================

def parse_ktgcadpcm_header_from_data(data):
    """
    Reads the main 32-byte header from a KTGCADPCM file's bytearray.
    """
    if len(data) < KTGC_HEADER_LENGTH:
        raise ValueError("Invalid KTGCADPCM file: too small for header.")
    
    magic = unpack("<I", data[0:4])[0]
    if magic != FILE_MAGIC:
        raise ValueError(f"Invalid KTGCADPCM magic. Got {hex(magic)}, expected {hex(FILE_MAGIC)}")

    (
        total_filesize, section_headerlink, unk_12, stream_count, pointer_table_offset
    ) = unpack("<IIIII", data[4:24])

    return {
        "total_filesize": total_filesize,
        "section_headerlink": section_headerlink,
        "unk_12": unk_12,
        "stream_count": stream_count,
        "pointer_table_offset": pointer_table_offset,
    }

def parse_audio_data_from_data(data):
    """

    Reads the audio section header and stream info from a KTGCADPCM file's bytearray.
    """
    audio_section_base_offset = KTGC_HEADER_LENGTH
    if len(data) < audio_section_base_offset + 4:
         raise ValueError("Invalid KTGCADPCM file: no audio section found.")
         
    magic = unpack("<I", data[audio_section_base_offset:audio_section_base_offset+4])[0]
    if magic != AUDIO_MAGIC:
        raise ValueError(f"Invalid audio header magic. Got {hex(magic)}, expected {hex(AUDIO_MAGIC)}")

    header_unpack_offset = audio_section_base_offset + 4
    (
        audio_datasize, file_linkID, num_channels, unk_48, sample_rate,
        duration, unk_60, alwaysFF, unk_68, dsp_info_ptr, dsp_info_size,
        stream_ptr_tbl_ptr, stream_size_tbl_ptr
    ) = unpack("<IIIIIIIIIIIII", data[header_unpack_offset : header_unpack_offset+52])
    
    # Calculate absolute offsets for easier processing later.
    dsp_info_abs = audio_section_base_offset + dsp_info_ptr
    stream_ptr_tbl_abs = audio_section_base_offset + stream_ptr_tbl_ptr
    stream_size_tbl_abs = audio_section_base_offset + stream_size_tbl_ptr
    
    # Get stream pointers and sizes from their tables
    stream_pointers, stream_sizes = [], []
    for ch in range(num_channels):
        ptr_offset = stream_ptr_tbl_abs + (ch * 4)
        size_offset = stream_size_tbl_abs + (ch * 4)
        if ptr_offset + 4 > len(data) or size_offset + 4 > len(data): break
        
        stream_pointers.append(unpack("<I", data[ptr_offset:ptr_offset+4])[0])
        stream_sizes.append(unpack("<I", data[size_offset:size_offset+4])[0])
        
    # Calculate absolute start/end of each audio stream's data
    stream_data_locs = []
    for ch in range(len(stream_pointers)):
        start_ptr = stream_pointers[ch]
        size = stream_sizes[ch]
        start_abs = audio_section_base_offset + start_ptr
        end_abs = start_abs + size
        stream_data_locs.append({ "start_abs": start_abs, "end_abs": end_abs, "size": size })

    return {
        "num_channels": num_channels, "sample_rate": sample_rate,
        "dsp_info_ptr": dsp_info_ptr, "dsp_info_size": dsp_info_size,
        "dsp_info_abs": dsp_info_abs,
        "stream_ptr_tbl_ptr": stream_ptr_tbl_ptr,
        "stream_ptr_tbl_abs": stream_ptr_tbl_abs,
        "stream_size_tbl_ptr": stream_size_tbl_ptr,
        "stream_size_tbl_abs": stream_size_tbl_abs,
        "stream_data_locs": stream_data_locs,
    }

# ==============================================================================
# SECTION 3: REBUILDING LOGIC
# This is the core of the script, performing all modifications in memory.
# ==============================================================================

def rebuild_ktgcadpcm_layout(dsp_file_path, out_file_path):
    """
    Rebuilds the audio in a KTGCADPCM file using a new DSP file. This function
    operates on an in-memory bytearray to prevent file corruption from direct
    on-disk insertion/deletion operations.
    """
    print(f"--- Starting Audio Rebuild ---")
    print(f"Source DSP: {Path(dsp_file_path).name}")
    print(f"Target File: {Path(out_file_path).name}")

    # --- 1. Load files into memory ---
    dsp_headers, dsp_audio_blob = parse_dsp_file(dsp_file_path)
    new_channel_count = len(dsp_headers)
    
    with open(out_file_path, "rb") as f:
        ktgc_content = bytearray(f.read())
        
    # --- 2. Parse target file structure ---
    audio_info = parse_audio_data_from_data(ktgc_content)
    orig_channel_count = audio_info["num_channels"]
    print(f"Source has {new_channel_count} channel(s). Target has {orig_channel_count} channel(s).")
    
    # --- 3. Verify Channel Count ---
    # The script now exits if the channel counts do not match. This is a safety
    # measure to prevent corruption when channel expansion logic is not needed.
    if new_channel_count != orig_channel_count:
        print("\n--- ERROR: Channel Count Mismatch ---", file=sys.stderr)
        print(f"Source DSP file has {new_channel_count} channel(s).", file=sys.stderr)
        print(f"Target file is configured for {orig_channel_count} channel(s).", file=sys.stderr)
        print("\nAborting to prevent file corruption.", file=sys.stderr)
        print("Please use a source DSP with a matching number of channels.", file=sys.stderr)
        sys.exit(1)

    # --- 4. Prepare and Splice New Audio Data ---
    # The new audio data replaces the old audio block completely.
    new_streams_data, new_stream_sizes = [], []
    cursor = 0
    for ch_header in dsp_headers:
        nibble_count = int((ch_header["SampleCount"] * 16 + 13) // 14)
        #byte_length = (ch_header["NibbleCount"] + 1) // 2 # strangely this doesn't work in every case, so better to calculate it
        byte_length = (nibble_count + 1) // 2 # Each nibble is 4 bits.
        ch_data = dsp_audio_blob[cursor : cursor + byte_length]
        new_streams_data.append(ch_data)
        new_stream_sizes.append(len(ch_data))
        cursor += byte_length
        
    new_audio_block = b"".join(new_streams_data)

    # Determine the boundaries of the old audio block to replace it.
    if not audio_info["stream_data_locs"]:
         raise ValueError("Target file has no audio streams defined to replace.")
    audio_block_start = audio_info["stream_data_locs"][0]["start_abs"]
    audio_block_end = audio_info["stream_data_locs"][-1]["end_abs"]
    
    ktgc_content = ktgc_content[:audio_block_start] + new_audio_block + ktgc_content[audio_block_end:]
    
    # --- 5. Update All Pointers and Metadata ---
    audio_section_base = KTGC_HEADER_LENGTH
    
    # Update stream pointer and size tables with new values.
    stream_ptr_tbl_abs = audio_info["stream_ptr_tbl_abs"]
    stream_size_tbl_abs = audio_info["stream_size_tbl_abs"]
    
    current_stream_ptr_relative = audio_block_start - audio_section_base
    for i in range(new_channel_count):
        pack_into("<I", ktgc_content, stream_ptr_tbl_abs + i * 4, current_stream_ptr_relative)
        pack_into("<I", ktgc_content, stream_size_tbl_abs + i * 4, new_stream_sizes[i])
        current_stream_ptr_relative += new_stream_sizes[i]

    # Update DSP info blocks for each channel using data from the source DSP.
    dsp_info_abs = audio_info["dsp_info_abs"]
    for i in range(new_channel_count):
        ch_header = dsp_headers[i]
        dsp_block_offset = dsp_info_abs + i * DSP_HEADER_LENGTH
        
        # Pack various metadata fields. This structure must match the game's expectations.
        pack_into("<I", ktgc_content, dsp_block_offset + 0, ch_header["NibbleCount"]) # Duration
        pack_into("<I", ktgc_content, dsp_block_offset + 4, ch_header["SampleCount"]) # Sample Count
        pack_into("<I", ktgc_content, dsp_block_offset + 8, ch_header["SampleRate"]) # Sample Rate
        pack_into("<I", ktgc_content, dsp_block_offset + 20, ch_header["SampleCount"] - 1) # clippedSampleCount
        
        # Pack the 16 DSP coefficients (2 bytes each)
        coeffs_base = dsp_block_offset + 28
        for j, unsigned_coeff in enumerate(ch_header["Coefficients"]):
            # *** FIX: Convert unsigned short to signed short ***
            # The DSP uses unsigned shorts (H) for coefficients, but the
            # target format expects signed shorts (h). We must convert
            # values > 32767 to their negative equivalent (two's complement).
            signed_coeff = unsigned_coeff
            if unsigned_coeff > 32767:
                signed_coeff = unsigned_coeff - 65536
            pack_into("<h", ktgc_content, coeffs_base + j * 2, signed_coeff)
            
    # Update shared metadata in the main audio header.
    pack_into("<I", ktgc_content, audio_section_base + 20, dsp_headers[0]["SampleRate"])
    pack_into("<I", ktgc_content, audio_section_base + 24, dsp_headers[0]["NibbleCount"])

    # --- 6. Finalize Header and Apply Padding ---
    # Update datasize and filesize fields.
    new_audio_datasize = len(ktgc_content) - KTGC_HEADER_LENGTH
    pack_into("<I", ktgc_content, audio_section_base + 4, new_audio_datasize)
    pack_into("<I", ktgc_content, 4, len(ktgc_content)) # Total filesize

    # The file size must be a multiple of 16. Pad with null bytes if needed.
    padding_needed = (16 - (len(ktgc_content) % 16)) % 16
    if padding_needed > 0:
        ktgc_content.extend(b'\x00' * padding_needed)
        # Update final filesize again to include padding.
        pack_into("<I", ktgc_content, 4, len(ktgc_content))
    
    # --- 7. Write Result to File ---
    with open(out_file_path, "wb") as f:
        f.write(ktgc_content)

    print(f"\nSuccessfully rebuilt '{Path(out_file_path).name}' with {new_channel_count} channel(s).")
    print(f"Final file size: {len(ktgc_content)} bytes.")
    print(f"--- Rebuild Complete ---")

# ==============================================================================
# SECTION 4: MAIN EXECUTION
# ==============================================================================

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("FE3H - replace DSP audio in KTGCADPCM game files")
        print("Replaces the audio in a KTGCADPCM file with audio from a DSP file.")
        print(f"Usage: python {Path(__file__).name} <source_file.dsp> <target_file.vgmstream>")
        sys.exit(1)

    source_dsp = sys.argv[1]
    target_ktgc = sys.argv[2]
    
    if not Path(source_dsp).exists():
        print(f"Error: Source file not found at '{source_dsp}'", file=sys.stderr)
        sys.exit(1)
        
    if not Path(target_ktgc).exists():
        print(f"Error: Target file not found at '{target_ktgc}'", file=sys.stderr)
        sys.exit(1)

    try:
        rebuild_ktgcadpcm_layout(source_dsp, target_ktgc)
    except (ValueError, FileNotFoundError, IndexError, TypeError, NameError) as e:
        print(f"\nFATAL ERROR: An unexpected problem occurred during the process.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print("Please ensure the files are valid and not corrupt.", file=sys.stderr)
        sys.exit(1)
