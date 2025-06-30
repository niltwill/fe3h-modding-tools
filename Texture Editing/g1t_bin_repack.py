import argparse
import os
import io
import shutil
import subprocess
from g1t_repack import rebuild_g1t
from kt_gz import compress_kt_gz

def batch_rebuild_and_pack(input_dir, output_bin, compress_lvl=0):
    temp_dir = os.path.join(input_dir, "_repacked_temp")
    os.makedirs(temp_dir, exist_ok=True)

    for filename in sorted(os.listdir(input_dir)):
        if not filename.endswith(".g1t"):
            continue

        base = os.path.splitext(filename)[0]
        g1t_path = os.path.join(input_dir, filename)
        dds_folder = os.path.join(input_dir, base)
        rebuilt_path = os.path.join(temp_dir, filename)

        print(f"[INFO] Rebuilding: {filename} using DDS folder: {base}/")
        if not os.path.isdir(dds_folder):
            raise FileNotFoundError(f"Missing folder: {dds_folder}")

        rebuild_g1t(g1t_path, dds_folder, rebuilt_path)
        # gzip compress it into another temp folder
        gz_path = os.path.join(temp_dir, f"{base}.bin.gz")
        with open(rebuilt_path, "rb") as in_f, open(gz_path, "wb") as out_f:
            in_buf = io.BytesIO(in_f.read())
            compress_kt_gz(in_buf, out_f, in_buf.getbuffer().nbytes, level=compress_lvl)

        # remove the uncompressed .g1t file to avoid including non-gzipped files
        os.remove(rebuilt_path)

    print(f"[INFO] All G1Ts rebuilt. Repacking into: {output_bin}")

    # Use external kt_arc.py to compress and package
    subprocess.run([
        "python", "kt_arc.py",
        temp_dir,
        output_bin
    ], check=True)

    print("[INFO] Cleaning up temporary files...")
    shutil.rmtree(temp_dir)

    print(f"[DONE] Packed archive written to: {output_bin}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch-rebuild G1T files and pack into BIN.")
    parser.add_argument("directory", help="Path to directory with .g1t files and subfolders of DDS.")
    parser.add_argument("output", help="Output BIN file path.")
    parser.add_argument("--level", type=int, default=9, help="Compression level (0-9, default: 9) - recommendation: use 9 to get same or similar size")

    args = parser.parse_args()

    try:
        batch_rebuild_and_pack(args.directory, args.output, compress_lvl=args.level)
    except Exception as e:
        print(f"[ERROR] {e}")