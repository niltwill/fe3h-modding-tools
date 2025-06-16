import sys
import struct
import os
import zlib
from struct import unpack as up, pack as pk

def iterate(s, ofs, num_entries, entry_size):
    return [s[ofs + entry_size * i:ofs + entry_size * (i + 1)] for i in range(num_entries)]

def uncompress(data):
    def align(ofs):
        return (ofs + 0x7F) & ~0x7F
    split_size, num_entries, total_size = up('<III', data[:0xC])
    splits = [up('<I', entry)[0] for entry in iterate(data, 0xC, num_entries, 4)]
    ofs = align(0xC + 0x4 * num_entries)
    out_data = b''
    for split in splits:
        cur_comp = up('<I', data[ofs:ofs+4])[0]
        assert cur_comp == split - 4
        out_data += zlib.decompress(data[ofs+4:ofs+4+cur_comp])
        ofs = align(ofs + split)
    assert len(out_data) == total_size
    return out_data

def uncompress_to_file(f, data):
    def align(ofs):
        return (ofs + 0x7F) & ~0x7F
    split_size, num_entries, total_size = up('<III', data[:0xC])
    splits = [up('<I', entry)[0] for entry in iterate(data, 0xC, num_entries, 4)]
    ofs = align(0xC + 0x4 * num_entries)
    for i, split in enumerate(splits):
        cur_comp = up('<I', data[ofs:ofs+4])[0]
        if i == num_entries - 1:
            if cur_comp != split - 4:
                assert split + (split_size * (num_entries - 1)) == total_size
                f.write(data[ofs:ofs+split])
            else:
                f.write(zlib.decompress(data[ofs+4:ofs+4+cur_comp]))
        else:
            assert cur_comp == split - 4
            f.write(zlib.decompress(data[ofs+4:ofs+4+cur_comp]))
        ofs = align(ofs + split)

def extract(meta, data):
    fileIndex = -1
    meta_data = meta.read()
    entries = [up('<QQQ?', entry[:0x19]) for entry in iterate(meta_data, 0, len(meta_data) // 0x20, 0x20)]
    os.makedirs("out", exist_ok=True)
    for (offset, uncompressed_size, compressed_size, compressed) in entries:
        fileIndex += 1
        if compressed_size == 0:
            continue
        print(f'Saving data from {fileIndex}')
        data.seek(offset)
        cur_data = data.read(compressed_size)
        with open(f'out/{fileIndex}.bin', 'wb') as f:
            if compressed:
                uncompress_to_file(f, cur_data)
            else:
                f.write(cur_data)

def main(argc, argv):
    if argc != 1:
        print(f'Usage: {argv[0]}')
        return 1
    try:
        with open('DATA0.bin', 'rb') as meta:
            with open('DATA1.bin', 'rb') as data:
                extract(meta, data)
    except Exception as ex:
        print(f'An error occurred ({type(ex).__name__}): {ex}')
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main(len(sys.argv), sys.argv))
