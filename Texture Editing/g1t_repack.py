import os
import re
import struct
from pathlib import Path

# Load custom shared G1T info
import g1t

def read_g1t_metadata(g1t_path):
    """Reads G1T and returns metadata per texture and header info.
    Assumes little-endian based on previous discussion where 'GT1G' magic was observed
    and original values were read incorrectly as big-endian.
    """
    metadata = []

    with open(g1t_path, 'rb') as f:
        # Determine endianness
        magic = f.read(4)
        endian = '<' if magic != b'G1TG' else '>'
        f.seek(0)

        # Main G1T header format: magic (4s), version (4s), filesize (I), table_offset (I),
        # entry_count (I), platform (I), astc_size (I)
        header_fmt = f'{endian}4s4s5I'
        header_size_bytes = struct.calcsize(header_fmt)
        
        # Read and unpack the main header
        header = struct.unpack(header_fmt, f.read(header_size_bytes))
        magic, version, filesize, table_offset, entry_count, platform, astc_size = header

        # Read normal flags block.
        normal_flags_data_start = f.tell()
        f.seek(normal_flags_data_start) # Ensure we are right after the main header
        normal_flags = struct.unpack(f'{endian}{entry_count}I', f.read(entry_count * 4))
        
        # Seek to the texture offset table's start position as indicated by header
        f.seek(table_offset)
        offsets = struct.unpack(f'{endian}{entry_count}I', f.read(entry_count * 4))

        # Loop through each texture entry to gather its metadata
        for i, offset in enumerate(offsets):
            # Calculate the absolute offset of the texture header in the original file
            tex_offset = table_offset + offset
            f.seek(tex_offset) # Move file pointer to the texture header

            # Read fixed 8-byte texture header components
            byte1 = struct.unpack(f'{endian}B', f.read(1))[0]
            subsystem = byte1 & 0x0F
            mip_count_raw = (byte1 >> 4) & 0x0F
            mip_count = mip_count_raw if mip_count_raw > 0 else 1
            tex_type = struct.unpack(f'{endian}B', f.read(1))[0]
            dim_byte = struct.unpack(f'{endian}B', f.read(1))[0]
            packed_w = dim_byte & 0x0F
            packed_h = (dim_byte >> 4) & 0x0F
            f.read(4)    # skip 4 unknown bytes
            extra_version = struct.unpack(f'{endian}B', f.read(1))[0]
            
            # Initial header size is 8 bytes (fixed part)
            calculated_entry_header_size = 8 
            extra_size_value = 0 # Initialize extra_size

            # If extra_version indicates additional header data, read its size and add to total header size
            if extra_version > 0:
                # Read the actual extra_size value from the file
                extra_size_value = struct.unpack(f'{endian}I', f.read(4))[0]
                calculated_entry_header_size += 4 + extra_size_value 
                
                # Capture initial width/height from packed_w/h
                width = 1 << packed_w if packed_w else 1
                height = 1 << packed_h if packed_h else 1

                if extra_size_value >= 0x14: # Check if the extra block is big enough to contain them
                    current_pos_before_seek = f.tell() # Save current position
                    f.seek(tex_offset + 0x10) # Seek to where width/height are if extra_version applies
                    width = struct.unpack(f'{endian}i', f.read(4))[0]
                    height = struct.unpack(f'{endian}i', f.read(4))[0]
                    f.seek(current_pos_before_seek) # Restore position to continue reading rest of header data
                else:
                    # For textures without extra_version, width and height are from packed_w/h
                    width = 1 << packed_w if packed_w else 1
                    height = 1 << packed_h if packed_h else 1
            else: # If no extra_version, width and height are from packed_w/h only
                width = 1 << packed_w if packed_w else 1
                height = 1 << packed_h if packed_h else 1
            
            # Ensure file pointer is at the end of the current texture's header for the next iteration
            f.seek(tex_offset + calculated_entry_header_size)

            format_info = g1t.G1T_TYPE_MAP.get(tex_type)

            metadata.append({
                "index": i,
                "offset": tex_offset, # Original absolute offset in G1T
                "subsystem": subsystem,
                "mip_count": mip_count,
                "tex_type": tex_type,
                "width": width,
                "height": height,
                "extra_version": extra_version,
                "extra_size": extra_size_value, # The value of extra_size from the file
                "header_size": calculated_entry_header_size, # The full size of this texture's header block
                "normal_flag": normal_flags[i], # This stores the individual flag for this texture
                "format_info": format_info
            })

    return {
        "endianness": endian,
        "header_info": {
            "magic": magic,
            "version": version,
            "filesize": filesize,
            "table_offset": table_offset,
            "entry_count": entry_count,
            "platform": platform,
            "astc_size": astc_size # Global ASTC size/flag from main G1T header
        },
        "normal_flags": normal_flags, # This stores the entire tuple of normal flags
        "textures": metadata
    }

def validate_dds(path, expected_fourcc):
    with open(path, 'rb') as f:
        dds = f.read()

    if dds[:4] != b'DDS ':
        raise ValueError("Invalid DDS magic header")

    # Read and decode FOURCC
    fourcc = dds[84:88].decode("ascii")
    if expected_fourcc:
        if isinstance(expected_fourcc, bytes):
            expected_fourcc = expected_fourcc.decode("ascii")
        if fourcc != expected_fourcc:
            #raise ValueError(f"Expected {expected_fourcc}, got {fourcc}")
            print(f"Warning! Original was {expected_fourcc}, got {fourcc}")

    height = struct.unpack_from('<I', dds, 12)[0]
    width = struct.unpack_from('<I', dds, 16)[0]

    if fourcc == 'DXT1':
        expected_size = width * height // 2
    elif fourcc == 'DXT5':
        expected_size = width * height
    else:
        expected_size = width * height * 4

    # Should be 128, but first byte seems to be doubled, so we skip that one
    pixel_data = dds[128:128 + expected_size]  # Ensure no extra padding is pulled in

    if len(pixel_data) < expected_size: # it's like the first byte is doubled, so we have to do this workaround
        raise ValueError(f"Pixel data too short: {len(pixel_data)} < {expected_size}")

    return pixel_data

def get_dds_metadata(dds_path):
    with open(dds_path, "rb") as f:
        if f.read(4) != b'DDS ':
            raise ValueError("Invalid DDS file")
        f.seek(12)
        height = struct.unpack('<I', f.read(4))[0]
        width = struct.unpack('<I', f.read(4))[0]
        f.seek(84)
        fourcc = f.read(4).decode("ascii")
        f.seek(28)
        mipmaps = struct.unpack('<I', f.read(4))[0] or 1
    return width, height, mipmaps, fourcc

def rebuild_g1t(original_path, dds_folder, output_path):
    """Recreates G1T from modified DDS files by repacking them.
    This function carefully handles offsets, alignments, and header patching.
    """
    meta = read_g1t_metadata(original_path)
    endian = meta["endianness"]
    header_info = meta["header_info"]
    textures = meta["textures"]
    normal_flags_tuple = meta["normal_flags"] # Correctly get the tuple of normal flags

    # Re-open original file to read specific chunks precisely, avoiding full memory load
    with open(original_path, 'rb') as f_orig:
        # Read the exact main G1T header bytes (first 28 bytes for 4s4s5I)
        main_header_size = struct.calcsize(f'{endian}4s4s5I')
        original_main_header_bytes = f_orig.read(main_header_size)

    with open(output_path, 'wb') as out:
        # 1. Write initial G1T header. We will patch filesize and table_offset later.
        out.write(original_main_header_bytes)

        # 2. Write the normal flags block by packing the tuple of flags.
        # This ensures only the actual flags are written and no padding.
        for flag in normal_flags_tuple: # Iterate directly over the tuple
            out.write(struct.pack(f'{endian}I', flag))

        # 3. Determine the absolute start of the new offset table and write placeholders.
        final_abs_offset_table_start = out.tell()

        # Write placeholder offsets. We'll fill these in later.
        placeholder_table_size = header_info["entry_count"] * 4
        out.write(b'\x00' * placeholder_table_size)

        # 4. Prepare to write texture headers and pixel data.
        new_relative_offsets_for_table = []  

        # Iterate through each texture entry to copy its header and add new pixel data
        for entry in textures:
            idx = entry["index"]
            dds_path = os.path.join(dds_folder, f"{idx:04d}.dds")

            if not os.path.exists(dds_path):
                raise FileNotFoundError(f"Missing DDS file for texture {idx:04d}: {dds_path}")

            expected_fourcc = None
            if entry["format_info"]:
                expected_fourcc = entry["format_info"].get("fourcc")

            try:
                pixel_data = validate_dds(dds_path, expected_fourcc)
            except ValueError as e:
                raise RuntimeError(f"[Texture {idx:04d}] DDS validation failed for '{dds_path}': {e}")

            new_width, new_height, new_mipmaps, new_fourcc = get_dds_metadata(dds_path)
            new_tex_type = next(
                (k for k, v in g1t.G1T_TYPE_MAP.items()
                 if v.get("fourcc") is not None and v["fourcc"].decode("ascii") == new_fourcc),
                None
            )
            if new_tex_type is None:
                raise ValueError(f"Unknown G1T type for DDS FOURCC: {new_fourcc}")

            # Store the current position for this texture's relative offset.
            relative_offset_for_table = out.tell() - final_abs_offset_table_start
            new_relative_offsets_for_table.append(relative_offset_for_table)

            # Read and modify original header
            with open(original_path, 'rb') as f_orig_tex:
                f_orig_tex.seek(entry["offset"])
                #tex_header = bytearray(f_orig_tex.read(entry["header_size"] - 4))
                tex_header = bytearray(f_orig_tex.read(entry["header_size"] - 4))

            # Set mipmap count in upper nibble of byte 0
            tex_header[0] = ((new_mipmaps & 0xF) << 4) | (tex_header[0] & 0x0F)

            # Set new tex_type
            tex_header[1] = new_tex_type

            # Set packed dimensions
            tex_header[2] = ((new_height.bit_length() - 1) << 4) | (new_width.bit_length() - 1)

            # Patch full width/height in extra block if applicable
            if entry["extra_size"] >= 0x14:
                struct.pack_into(f'{endian}II', tex_header, 0x10, new_width, new_height)

            # Write updated header
            out.write(tex_header)

            # Handle ASTC metadata (this is untested)
            if entry["format_info"] and entry["format_info"].get("astc") and header_info["astc_size"] > 0:
                # Extract ASTC block size from filename (e.g., "0003_8x6.dds")
                match = re.search(r"_(\d+)x(\d+)", os.path.basename(dds_path))
                if not match:
                    raise ValueError(f"Missing ASTC block size (e.g., '_6x6') in filename: {dds_path}")

                block_w = int(match.group(1))
                block_h = int(match.group(2))

                sub_format = g1t.ASTC_BLOCK_SIZE_TO_SUBFORMAT.get((block_w, block_h))
                if sub_format is None:
                    raise ValueError(f"Unsupported ASTC block size {block_w}x{block_h} in {dds_path}")

                # Construct ASTC metadata block: UNK1=0x15, UNK2=0x01, SubFormat (int32)
                astc_meta = struct.pack(f'{endian}HHI', 0x15, 0x01, sub_format)
                out.write(astc_meta)

            # Write the DDS pixel data (which has had its 128-byte header stripped)
            out.write(pixel_data)

        # 5. Patch the texture offset table.
        current_end_pos = out.tell()

        # Go back to where the offset table should be written
        out.seek(final_abs_offset_table_start)

        # Write the new texture offset table.
        for offset_val in new_relative_offsets_for_table:
            out.write(struct.pack(f'{endian}I', offset_val))

        # Restore file pointer to the end of the file.
        out.seek(current_end_pos)

        # 6. Patch the G1T header with the correct filesize and table_offset.
        final_filesize = out.tell()

        # Patch filesize (located at offset 0x08 from the beginning of the file)
        out.seek(0x08)
        out.write(struct.pack(f'{endian}I', final_filesize))

        # Patch table_offset (located at offset 0x0C from the beginning of the file)
        out.seek(0x0C)
        out.write(struct.pack(f'{endian}I', final_abs_offset_table_start))

        # Patch entry_count (number of textures) at offset 0x10
        out.seek(0x10)
        out.write(struct.pack(f'{endian}I', len(new_relative_offsets_for_table)))

        # Seek back to the end of the file for a clean close (optional, but good practice)
        out.seek(final_filesize)

    print(f"Rebuilt G1T saved to: {output_path}")

# Example usage:
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rebuilds a G1T file with new DDS textures from a directory.")
    parser.add_argument("original", help="Path to the original .g1t file to read structure from.")
    parser.add_argument("dds_dir", help="Path to the directory containing replacement DDS files (e.g., '0000.dds', '0001.dds').")
    parser.add_argument("output", help="Path to save the newly created .g1t file.")
    args = parser.parse_args()

    try:
        rebuild_g1t(args.original, args.dds_dir, args.output)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error during DDS validation: {e}")
    except RuntimeError as e:
        print(f"Error during G1T rebuilding: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
