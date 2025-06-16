from pathlib import Path
from struct import unpack
import sys

# Define hex markers and other constants
MAGIC = b"KTSC"
KTSR_SECTION_ID = 0x5253544B
HEADER_LENGTH = 32


# Read the binary file
def parse_ktscbin(file_path):
    results = {
        "is_valid_ktsl2asbin": False
        #"ktsr_sections": [],
    }

    with open(file_path, "rb") as f:
        data = f.read()

    # Check magic and type ID
    if data[:4] != MAGIC:
        return results

    results["is_valid_ktsl2asbin"] = True

    # This is redundant here, the header also has it

    """
    offset = HEADER_LENGTH # Skip header (sort of, not really correct, but skips a lil bit anyway)
    data_len = len(data)

    while offset + 4 <= data_len:
        section_id = unpack("<I", data[offset:offset+4])[0]

        if section_id == KTSR_SECTION_ID:
            results["ktsr_sections"].append(offset)

        offset += 4
    """

    return results

# Read header_sections (first)
def parse_header_sections(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    if data[:4] != MAGIC:
        raise ValueError("Invalid KTSC magic header")

    offset = 4  # skip magic word
    data_len = len(data)
    header_sections = []

    while offset + 4 <= data_len:
        flags = unpack("<H", data[offset:offset+2])[0]
        console_type = unpack("<H", data[offset+2:offset+4])[0]
        ktsr_count = unpack("<I", data[offset+4:offset+8])[0]
        ktsr_link_id_table_offset = unpack("<I", data[offset+8:offset+12])[0]
        ktsr_offset_table_offset = unpack("<I", data[offset+12:offset+16])[0]
        file_size = unpack("<I", data[offset+16:offset+20])[0]
        ktsc_end_offset = unpack("<I", data[offset+20:offset+24])[0]
        padding_1 = unpack("<I", data[offset+24:offset+28])[0]
        
        # Dynamically read ktsr_link_ids
        ktsr_link_ids = [
            unpack("<I", data[ktsr_link_id_table_offset + i * 4 : ktsr_link_id_table_offset + (i + 1) * 4])[0]
            for i in range(ktsr_count)
        ]

        # Dynamically read ktsr_offsets
        ktsr_offsets = [
            unpack("<I", data[ktsr_offset_table_offset + i * 4 : ktsr_offset_table_offset + (i + 1) * 4])[0]
            for i in range(ktsr_count)
        ]
        
        # Read trailing 4-byte value after ktsr_offsets
        trailing_offset = ktsr_offset_table_offset + ktsr_count * 4
        if trailing_offset + 4 <= len(data):
            file_end_offset = unpack("<I", data[trailing_offset:trailing_offset + 4])[0]
        else:
            file_end_offset = None
        
        header_sections.append({
            "flags": flags,
            "console_type": console_type,
            "ktsr_count": ktsr_count,
            "ktsr_link_id_table_offset": ktsr_link_id_table_offset,
            "ktsr_offset_table_offset": ktsr_offset_table_offset,
            "file_size": file_size,
            "ktsc_end_offset": ktsc_end_offset,
            "padding_1": padding_1,
            "ktsr_link_ids": ktsr_link_ids,
            "ktsr_offsets": ktsr_offsets,
            "file_end_offset": file_end_offset
        })
        
        break

    print(header_sections)
    return header_sections

# Main
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("FE3H - Display verbose information about ktsl2asbin collection files (30831-30837, 31001-31007)")
        print("(This is used as basis for editing/understanding its structure)")
        print("Usage: python ktsc-info.py XXXX.ktsl2asbin")
        sys.exit(1)

    filename = sys.argv[1]
    parsed = parse_ktscbin(filename)

    print("Is valid ktsl2asbin (collection):", parsed["is_valid_ktsl2asbin"])
    if parsed["is_valid_ktsl2asbin"]:
        #print("KTSR Sections at offsets:", parsed["ktsr_sections"])

        print("")
        print("Header section")
        parsed2 = parse_header_sections(filename)
        
        # Map KTSR Link ID to offset
        section = parsed2[0]
        link_ids = section["ktsr_link_ids"]
        offsets = section["ktsr_offsets"]

        print("\nKTSR Link ID -> Offset Mapping:")
        print("-" * 32)
        for i, (link_id, offset) in enumerate(zip(link_ids, offsets)):
            print(f"{i:4}: Link ID = {link_id:<10} | Offset = {offset}")

        #ktsr_map = [
        #    {"index": i, "link_id": link_id, "offset": offset}
        #    for i, (link_id, offset) in enumerate(zip(link_ids, offsets))
        #]
