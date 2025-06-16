import sys
from struct import pack

# Main
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("FE3H - Replace or add loop in a KTSS audio file")
        print("Note: this is very rudimentary, only use on a singular KTSS audio file (no multiple KTSS sections)")
        print("Usage: python ktss-loop.py XXXX.ktss <loop_start> <loop_length>")
        sys.exit(1)

    filename = sys.argv[1]
    loop_start = int(sys.argv[2])
    loop_length = int(sys.argv[3])

    ## update file size info too
    with open(filename, "rb") as f:
        data = bytearray(f.read())

    # Update total file size at offsets 52 and 56
    data[52:56] = pack("<I", loop_start)
    data[56:60] = pack("<I", loop_length)

    # write to the file again (in-place)
    with open(filename, "wb") as f:
        f.write(data)
