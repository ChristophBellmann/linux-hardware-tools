#!/usr/bin/env python3
import sys, struct, glob

CARD = "card1"  # bei dir fest

def find_power_cap_uw():
    for path in glob.glob(f"/sys/class/drm/{CARD}/device/hwmon/hwmon*/power1_cap"):
        try:
            with open(path) as f:
                v = int(f.read().strip())
            return v, path
        except:
            continue
    raise SystemExit("power1_cap nicht gefunden")

if len(sys.argv) != 3:
    print("Usage: ./patch_ppt_auto.py <input_pp_table.bin> <new_PPT_in_Watt>")
    sys.exit(1)

inp = sys.argv[1]
ppt_w = int(sys.argv[2])
ppt_uw_new = ppt_w * 1_000_000

ppt_uw_old, cap_path = find_power_cap_uw()
print(f"Aktueller PPT laut {cap_path}: {ppt_uw_old/1e6:.1f} W")

# Original lesen
data = bytearray(open(inp, "rb").read())

needle = struct.pack("<I", ppt_uw_old)
repl = struct.pack("<I", ppt_uw_new)

count = 0
for i in range(len(data) - 3):
    if data[i:i+4] == needle:
        data[i:i+4] = repl
        count += 1

open("pp_table_mod.bin", "wb").write(data)

print(f"Gefundene Stellen: {count}")
print(f"PPT {ppt_uw_old/1e6:.1f} W -> {ppt_w} W in pp_table_mod.bin")
print("\nFERTIG — *NICHT* ins Kernel-pp_table geschrieben.")
