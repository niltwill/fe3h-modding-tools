import argparse
import os
import struct
import subprocess
import zlib
from typing import Tuple, Optional, Dict, Any
from PIL import Image # for PNG export (RGBA8, BGRA8 only)
from kt_gz import decompress_kt_gz # For unpacking GZ files

# Load custom shared G1T info
import g1t

def create_dds_header(width: int, height: int, mip_count: int, fourcc_str: Optional[bytes], linear_size: int, is_uncompressed: bool = False) -> bytes:
    """Creates a 128-byte DDS header."""
    dwMagic = b'DDS '
    dwSize = 124
    dwFlags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000
    dwHeight = height
    dwWidth = width
    dwPitchOrLinearSize = linear_size
    dwDepth = 0
    dwMipMapCount = mip_count
    dwReserved1 = [0] * 11

    ddspf_dwSize = 32
    if is_uncompressed:
        ddspf_dwFlags = 0x41  # DDPF_RGB | DDPF_ALPHAPIXELS
        ddspf_dwFourCC = b'\x00\x00\x00\x00'
        ddspf_dwRGBBitCount = 32
        ddspf_dwRBitMask = 0x00FF0000
        ddspf_dwGBitMask = 0x0000FF00
        ddspf_dwBBitMask = 0x000000FF
        ddspf_dwABitMask = 0xFF000000
    else:
        ddspf_dwFlags = 0x4  # DDPF_FOURCC
        ddspf_dwFourCC = fourcc_str
        ddspf_dwRGBBitCount = 0
        ddspf_dwRBitMask = 0
        ddspf_dwGBitMask = 0
        ddspf_dwBBitMask = 0
        ddspf_dwABitMask = 0

    dwCaps = 0x1000 | 0x8 | 0x400000
    dwCaps2 = 0
    dwCaps3 = 0
    dwCaps4 = 0
    dwReserved2 = 0

    header = struct.pack(
        '<4s I 6I 11I I I 4s 5I 5I',
        dwMagic, dwSize, dwFlags, dwHeight, dwWidth, dwPitchOrLinearSize, dwDepth, dwMipMapCount,
        *dwReserved1,
        ddspf_dwSize, ddspf_dwFlags, ddspf_dwFourCC,
        ddspf_dwRGBBitCount, ddspf_dwRBitMask, ddspf_dwGBitMask, ddspf_dwBBitMask, ddspf_dwABitMask,
        dwCaps, dwCaps2, dwCaps3, dwCaps4, dwReserved2
    )

    return header

def parse_astc_meta(f, astc_size: int, endian: str) -> Dict[str, Any]:
    """Parse ASTC metadata section."""
    astc_meta = {}
    astc_entries = []
    
    if astc_size > 0:
        num_entries = astc_size // 8
        for i in range(num_entries):
            unk1, unk2, astc_format = struct.unpack(f'{endian}HHI', f.read(8))
            
            # Map ASTC format to block dimensions
            astc_formats = {
                0: (4, 4), 1: (5, 4), 2: (5, 5), 3: (6, 5), 4: (6, 6),
                5: (8, 5), 6: (8, 6), 7: (8, 8), 8: (10, 5), 9: (10, 6),
                10: (10, 8), 11: (10, 10), 12: (12, 10), 13: (12, 12)
            }
            
            block_dims = astc_formats.get(astc_format, (4, 4))
            astc_entries.append({
                'format': astc_format,
                'block_width': block_dims[0],
                'block_height': block_dims[1]
            })
    
    astc_meta['entries'] = astc_entries
    return astc_meta

def calculate_texture_size(width: int, height: int, tex_type: int, mip_count: int, astc_meta: Dict = None, tex_index: int = 0) -> int:
    """Calculate texture data size based on format and dimensions."""
    format_info = g1t.G1T_TYPE_MAP.get(tex_type)
    if not format_info:
        return 0
    
    # Handle special cases
    if tex_type == 0x6F:  # ETC1_RGB_Special
        # Special case with different mipmap calculation
        size = width * height // 2
        original_size = size
        for i in range(1, mip_count):
            original_size = original_size // 4
            size += original_size
        return size
    elif tex_type == 0x7D and astc_meta:  # ASTC
        if tex_index < len(astc_meta['entries']):
            entry = astc_meta['entries'][tex_index]
            block_w, block_h = entry['block_width'], entry['block_height']
            blocks_x = (width + block_w - 1) // block_w
            blocks_y = (height + block_h - 1) // block_h
            size = blocks_x * blocks_y * 16  # 16 bytes per ASTC block
            return max(size, 16)  # Minimum 16 bytes
    else:
        # Standard calculation
        if format_info.get('fourcc'):
            # Block compressed format
            blocks_x = max(1, (width + 3) // 4)
            blocks_y = max(1, (height + 3) // 4)
            return blocks_x * blocks_y * format_info['block_size']
        else:
            # Uncompressed format
            return width * height * (format_info['bpp'] // 8)

def extract_g1t(g1t_path: str, output_dir: str):
    """Parse a G1T texture container and extract textures."""
    print(f"Opening '{g1t_path}'...")
    
    with open(g1t_path, 'rb') as f:
        # Check endianness
        magic_check = f.read(4)
        endian = '<'  # Default to Little Endian
        if magic_check == b'G1TG':
            endian = '>'
            print("Big Endian file format detected.")
        else:
            print("Little Endian file format detected.")
        f.seek(0)

        # Read main header
        header_fmt = f'{endian}4s4sIIIII'
        header_data = struct.unpack(header_fmt, f.read(struct.calcsize(header_fmt)))
        magic, version, filesize, table_offset, entry_count, platform, astc_size = header_data
        
        platform_name = g1t.G1T_PLATFORMS.get(platform, f"Unknown({platform})")
        print(f"Magic: {magic.decode('ascii')}, Version: {version.hex()}, Platform: {platform_name}")
        print(f"Filesize: {filesize}, Table offset: 0x{table_offset:X}")
        print(f"Found {entry_count} texture entries, ASTC size: {astc_size}")

        # Read normal map flags
        normal_flags = []
        if entry_count > 0:
            normal_flags = struct.unpack(f'{endian}{entry_count}I', f.read(entry_count * 4))

        # Read offset table
        f.seek(table_offset)
        offsets = struct.unpack(f'{endian}{entry_count}I', f.read(entry_count * 4))

        # Parse ASTC metadata if present
        astc_meta = None
        if astc_size > 0:
            astc_meta = parse_astc_meta(f, astc_size, endian)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        print(f"Extracting textures to '{output_dir}/'")

        # Process each texture
        for i in range(entry_count):
            tex_offset = table_offset + offsets[i]
            f.seek(tex_offset)

            # Read texture header (first 8 bytes are always present)
            header_byte1 = struct.unpack(f'{endian}B', f.read(1))[0]
            subsystem_id = header_byte1 & 0x0F
            mip_count = (header_byte1 >> 4) & 0x0F
            if mip_count == 0:
                mip_count = 1

            tex_type = struct.unpack(f'{endian}B', f.read(1))[0]
            
            dim_byte = struct.unpack(f'{endian}B', f.read(1))[0]
            packed_width = dim_byte & 0x0F
            packed_height = (dim_byte >> 4) & 0x0F

            # Skip unknown bytes
            f.read(4)
            
            extra_version = struct.unpack(f'{endian}B', f.read(1))[0]

            width = height = 0
            tex_header_size = 8  # Base header size

            # Handle extra header data
            if extra_version > 0:
                extra_size = struct.unpack(f'{endian}I', f.read(4))[0]
                tex_header_size += extra_size
                
                if extra_size >= 0x10:
                    f.seek(tex_offset + 0x10)  # Skip to extra width
                    if extra_size >= 0x14:
                        extra_width = struct.unpack(f'{endian}i', f.read(4))[0]
                        extra_height = struct.unpack(f'{endian}i', f.read(4))[0]
                        
                        # Use extra dimensions if packed dimensions are 0
                        if packed_width == 0 or packed_height == 0:
                            width, height = extra_width, extra_height

            # Calculate final dimensions
            if width == 0 and height == 0:
                width = 1 << packed_width if packed_width > 0 else 1
                height = 1 << packed_height if packed_height > 0 else 1

            # Get format information
            format_info = g1t.G1T_TYPE_MAP.get(tex_type)
            if not format_info:
                print(f"Skipping texture {i:03d}: Unsupported G1T type 0x{tex_type:02X}")
                continue

            # Calculate texture data size
            texture_size = calculate_texture_size(width, height, tex_type, mip_count, astc_meta, i)
            if texture_size == 0:
                print(f"Skipping texture {i:03d}: Could not calculate size for type 0x{tex_type:02X}")
                continue

            # Determine output format
            is_normal_map = len(normal_flags) > i and normal_flags[i] == 3
            subsystem_name = g1t.G1T_SUBSYSTEMS.get(subsystem_id, f"Unknown({subsystem_id})")
            morton_info = " (Morton)" if format_info.get('morton') else ""
            
            print(f"  -> Texture {i:03d}: {width}x{height}, Mips: {mip_count}")
            print(f"     Format: {format_info['format']}{morton_info}, Subsystem: {subsystem_name}")
            print(f"     Normal map: {is_normal_map}, Size: {texture_size} bytes")

            # Read texture data
            pixel_data_offset = tex_offset + tex_header_size
            f.seek(pixel_data_offset)
            pixel_data = f.read(texture_size)

            # Save based on format
            if format_info.get('fourcc'):
                # Compressed formats like DXT1/DXT5
                linear_size = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * format_info['block_size']
                dds_header = create_dds_header(width, height, mip_count, format_info['fourcc'], linear_size)
                output_filename = os.path.join(output_dir, f"{i:04d}.dds")
                with open(output_filename, 'wb') as out_f:
                    out_f.write(dds_header)
                    out_f.write(pixel_data)
                convert_dds_to_png(output_filename, output_dir)
                output_png = os.path.join(output_dir, f"{i:03d}.png")
            elif format_info['format'] in ("BGRA8", "RGBA8"):
                # Write DDS first
                # Uncompressed BGRA8/RGBA8 to DDS with alpha masks
                linear_size = width * height * 4
                dds_header = create_dds_header(width, height, mip_count, None, linear_size, is_uncompressed=True)
                output_filename = os.path.join(output_dir, f"{i:04d}.dds")
                print(f"     -> Saving as DDS: {output_filename}")
                with open(output_filename, 'wb') as out_f:
                    out_f.write(dds_header)
                    out_f.write(pixel_data)
            
                # Convert raw pixel data to PNG                
                # Reorder BGRA to RGBA if needed
                if format_info['format'] == "BGRA8":
                    # Convert BGRA to RGBA
                    pixels = bytearray()
                    for j in range(0, len(pixel_data), 4):
                        b, g, r, a = pixel_data[j:j+4]
                        pixels.extend([r, g, b, a])
                    pixel_data_rgba = bytes(pixels)
                else:
                    pixel_data_rgba = pixel_data  # Already RGBA8
                
                image_mode = 'RGBA'
                output_filename = os.path.join(output_dir, f"{i:04d}.png")
                print(f"     -> Saving as PNG: {output_filename}")
                
                # Create the image
                image = Image.frombytes(image_mode, (width, height), pixel_data_rgba)
                image.save(output_filename)
            else:
                # Fallback: raw binary
                format_name = format_info['format'].replace(' ', '_')
                output_filename = os.path.join(output_dir, f"{i:04d}_{format_name}_{width}x{height}.bin")
                with open(output_filename, 'wb') as out_f:
                    out_f.write(pixel_data)

    print("\nExtraction complete!")

def which(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK) and os.path.isfile(fpath)

    def ext_candidates(fpath):
        yield fpath
        for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
            yield fpath + ext

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            for candidate in ext_candidates(exe_file):
                if is_exe(candidate):
                    return candidate

    return None

def convert_dds_to_png(dds_path, output_folder):
    # ImageMagick for the win!
    if which("magick"):
        try:
            subprocess.run([
                "magick",
                "mogrify",
                "-format", "png",
                "-quality", "100",
                "-path", f"{output_folder}",
                dds_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"ImageMagick failed: {e}")
    elif which("texconv"):
        # texconv can work too, but the PNG will display brighter in image viewers, due to it not embedding any sRGB ICC profile
        try:
            subprocess.run([
                "texconv",
                "-nologo",
                "-ft", "PNG",
                "-f", "B8G8R8A8_UNORM",
                "-srgb",
                "-y",
                "-o", output_folder,
                dds_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"texconv failed: {e}")
    else:
        print("Please install ImageMagick or Texconv and put it in your PATH (environment variable) to be able to convert the images from DDS to PNG and vice versa.")

def decompress_kt_gz_data(data: bytes) -> bytes:
    import io
    input_stream = io.BytesIO(data)
    output_stream = io.BytesIO()
    decompress_kt_gz(input_stream, output_stream)
    return output_stream.getvalue()

def try_unpack_bin(bin_path: str) -> Optional[list]:
    """Try to unpack a BIN file that contains embedded G1T/BIN files."""
    with open(bin_path, "rb") as f:
        num_files_bytes = f.read(4)
        if len(num_files_bytes) < 4:
            return None

        num_files = struct.unpack("<I", num_files_bytes)[0]

        if num_files <= 0 or num_files > 10000:
            return None  # Sanity check

        offsets_sizes = []
        for i in range(num_files):
            f.seek(4 + i * 8)
            entry = f.read(8)
            if len(entry) < 8:
                return None
            offset, size = struct.unpack("<II", entry)
            offsets_sizes.append((offset, size))

        file_list = []
        for offset, size in offsets_sizes:
            f.seek(offset)
            data = f.read(size)
            file_list.append(data)

        return file_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="FE3H: Extract textures from Koei Tecmo G1T containers or BIN bundles.")
    parser.add_argument("g1t_file", help="Path to the input G1T or BIN file")
    parser.add_argument("-o", "--output", help="Output directory (defaults to filename)", default=None)
    
    args = parser.parse_args()

    if not os.path.exists(args.g1t_file):
        print(f"Error: File not found at '{args.g1t_file}'")
    else:
        output_directory = args.output
        if not output_directory:
            base_name = os.path.basename(args.g1t_file)
            output_directory = os.path.splitext(base_name)[0]

        # Try to unpack BIN
        bin_entries = try_unpack_bin(args.g1t_file)
        if bin_entries:
            print(f"Extracted BIN container with {len(bin_entries)} files.")
            os.makedirs(output_directory, exist_ok=True)
            for i, blob in enumerate(bin_entries):
                out_subdir = os.path.join(output_directory, f"{i:04d}")

                # Check if the blob is compressed (try header)
                try:
                    if blob[:4] != b'GT1G' and len(blob) > 16:
                        # Heuristics: not GT1G magic, maybe compressed
                        decompressed = decompress_kt_gz_data(blob)
                        print(f"  -> Entry {i:04d} was compressed. Decompressed successfully.")
                    else:
                        decompressed = blob
                except Exception as e:
                    print(f"  -> Entry {i:04d} not compressed or failed to decompress: {e}")
                    decompressed = blob

                # Save to temp file for G1T parser
                temp_path = os.path.join(output_directory, f"{i:04d}.g1t")
                with open(temp_path, "wb") as f:
                    f.write(decompressed)

                extract_g1t(temp_path, out_subdir)
        else:
            # Not a BIN container, proceed normally
            extract_g1t(args.g1t_file, output_directory)