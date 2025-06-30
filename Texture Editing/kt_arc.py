import os
import struct

KT_ARC_ENTRY_STRUCT = struct.Struct("<II")  # offset, size


def read_files_sorted(in_dir):
    files = []
    for entry in os.listdir(in_dir):
        path = os.path.join(in_dir, entry)
        if os.path.isfile(path) and entry.endswith(".gz"):
            try:
                index = int(os.path.splitext(entry)[0].split('.')[0])
                files.append((index, path))
            except ValueError:
                continue
    return [path for _, path in sorted(files)]


def pack_bin_file(file_paths, out_path):
    file_count = len(file_paths)
    header_size = 4 + file_count * 8
    entries = []
    file_data = []
    current_offset = header_size

    for path in file_paths:
        with open(path, "rb") as f:
            data = f.read()

        entries.append((current_offset, len(data)))
        file_data.append(data)
        current_offset += len(data)

    with open(out_path, "wb") as f:
        f.write(struct.pack("<I", file_count))  # number of entries
        for offset, size in entries:
            f.write(struct.pack("<II", offset, size))
        for data in file_data:
            f.write(data)

    print(f"[INFO] Packed {file_count} files to: {out_path}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python kt_arc.py <input_folder> <output_file> [compression_level]")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_file = sys.argv[2]

    file_list = read_files_sorted(input_folder)
    if not file_list:
        print("No valid numbered files found.")
        sys.exit(1)

    pack_bin_file(file_list, output_file)
