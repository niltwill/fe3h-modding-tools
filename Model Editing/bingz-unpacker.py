import os
import struct
import sys

def unpack_sections(input_file_path, output_dir):
    """
    Unpacks sections from a binary file based on the provided structure.

    Args:
        input_file_path (str): The path to the binary file to unpack.
        output_dir (str): The directory where the unpacked sections will be saved.
    """
    # Define the magic byte sequences for file type identification
    G1M_MAGIC = b'\x5F\x4D\x31\x47' # _M1G
    G1T_MAGIC = b'\x47\x54\x31\x47' # GT1G
    G2A_MAGIC = b'\x5F\x41\x32\x47' # _A2G
    G1A_MAGIC = b'\x5F\x41\x31\x47' # _A1G
    RIGB_MAGIC = b'\x42\x47\x49\x52' # BGIR
    QGWS_MAGIC = b'\x53\x57\x47\x51' # SWGQ

    try:
        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")

        with open(input_file_path, 'rb') as f:
            # Read the number of entries (4 bytes, little-endian)
            entry_count_data = f.read(4)
            if len(entry_count_data) < 4:
                print("Error: Could not read the entry count. The file may be too small.")
                return

            # '<I' specifies little-endian unsigned int
            entry_count = struct.unpack('<I', entry_count_data)[0]
            print(f"Found {entry_count} entries in the header.")

            # Read the section headers
            headers = []
            for i in range(entry_count):
                header_data = f.read(8)
                if len(header_data) < 8:
                    print(f"Error: Could not read header for entry {i}. File is incomplete.")
                    continue
                
                # Each header is a 4-byte pointer and a 4-byte size
                section_pointer, section_size = struct.unpack('<II', header_data)
                headers.append({'pointer': section_pointer, 'size': section_size, 'id': i})

            # Process and extract each section
            for i, header in enumerate(headers):
                section_size = header['size']
                section_pointer = header['pointer']
                
                if section_size > 0:
                    print(f"Processing section {i}: Pointer=0x{section_pointer:08X}, Size={section_size} bytes")
                    
                    # Seek to the start of the section data
                    f.seek(section_pointer)
                    
                    # Read the section data
                    section_data = f.read(section_size)
                    
                    if len(section_data) != section_size:
                        print(f"Warning: For section {i}, expected {section_size} bytes but only found {len(section_data)}.")

                    # Determine file extension based on magic bytes
                    extension = '.bin' # Default extension
                    
                    header = section_data[:128]  # get only the first 128 bytes to check the header (sort of)
                    
                    if section_data.startswith(G1M_MAGIC):
                        extension = '.g1m'
                        print("  -> Found G1M magic number.")
                    elif section_data.startswith(G1T_MAGIC):
                        extension = '.g1t'
                        print("  -> Found G1T magic number.")
                    elif section_data.startswith(RIGB_MAGIC):
                        extension = '.rigb'
                        print("  -> Found RIGB magic number.")
                    elif section_data.startswith(QGWS_MAGIC):
                        extension = '.qgws'
                        print("  -> Found QGWS magic number.")
                    elif G2A_MAGIC in header:
                        extension = '.g2a'
                        print("  -> Found G2A magic number.")
                    elif G1A_MAGIC in header:
                        extension = '.g1a'
                        print("  -> Found G1A magic number.")
                    else:
                        print("  -> No recognized magic number found, using default '.bin' extension.")

                    # Write the section data to a new file with the correct extension
                    output_file_name = f"section_{i}{extension}"
                    output_file_path = os.path.join(output_dir, output_file_name)
                    
                    with open(output_file_path, 'wb') as out_f:
                        out_f.write(section_data)
                    print(f"  -> Saved to {output_file_path}")
                else:
                    print(f"Skipping section {i}: Size is 0.")
                    
        print("\nUnpacking complete.")

    except FileNotFoundError:
        print(f"Error: The file '{input_file_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
        if len(sys.argv) >= 3:
            output_folder = sys.argv[2]
        else:
            # Use input filename without extension as output folder
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_folder = base_name
            print(f"No output directory provided. Using: {output_folder}")
        
        unpack_sections(input_file, output_folder)
    else:
        print("Usage: python bingz-unpacker.py <input_file> [output_directory]")
        print("For model files: 3120-4012 (nx\\action\\model)")
