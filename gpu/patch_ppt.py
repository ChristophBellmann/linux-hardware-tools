#!/usr/bin/env python3
import sys, struct

if len(sys.argv) != 3:
    print("Usage: ./patch_ppt.py <input_pp_table.bin> <new_PPT_in_watts>")
    sys.exit(1)

inp = sys.argv[1]
ppt_watts = int(sys.argv[2])
ppt_uW = ppt_watts * 1000000

data = bytearray(open(inp, "rb").read())

# PPT befindet sich in RDNA2 PowerPlay Tables immer bei offset 0x1e4 (PPT)
# Format: 4 Bytes, little-endian, in µW.
offset = 0x1e4

old = struct.unpack_from("<I", data, offset)[0]
struct.pack_into("<I", data, offset, ppt_uW)

open("pp_table_mod.bin", "wb").write(data)

print(f"Done. PPT {old/1e6:.1f} W -> {ppt_watts} W")
