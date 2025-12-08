#!/usr/bin/env python3
import argparse, glob, os, re, subprocess, textwrap

def find_amd_card():
    for c in glob.glob("/sys/class/drm/card*"):
        vendor = os.path.join(c, "device/vendor")
        try:
            with open(vendor) as f:
                v = f.read().strip()
        except OSError:
            continue
        if v == "0x1002":  # AMD
            return os.path.basename(c)
    return "card1"

def find_hwmon(card):
    for h in glob.glob(f"/sys/class/drm/{card}/device/hwmon/hwmon*"):
        if os.path.isdir(h):
            return h
    return None

def read_int(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except Exception:
        return None

def read_pm_info(card_index=1):
    path = f"/sys/kernel/debug/dri/{card_index}/amdgpu_pm_info"
    try:
        out = subprocess.check_output(["sudo", "cat", path], text=True)
        return out
    except Exception as e:
        return f"(Fehler beim Lesen von {path}: {e})"

def parse_pm_info_block(text):
    avg_power = None
    gfx_clk = None
    mclk = None
    temp = None
    for line in text.splitlines():
        m = re.search(r"(\d+\.\d+)\s*W\s*\(average SoC\)", line)
        if m:
            avg_power = float(m.group(1))
        m = re.search(r"(\d+)\s*MHz\s*\(SCLK\)", line)
        if m:
            gfx_clk = int(m.group(1))
        m = re.search(r"(\d+)\s*MHz\s*\(MCLK\)", line)
        if m:
            mclk = int(m.group(1))
        m = re.search(r"GPU Temperature:\s*(\d+)\s*C", line)
        if m:
            temp = int(m.group(1))
    return avg_power, gfx_clk, mclk, temp

def main():
    parser = argparse.ArgumentParser(
        description="SMU/Power-Info für AMD-GPU (READ-ONLY / DRY-RUN)."
    )
    parser.add_argument("--show", action="store_true",
                        help="Aktuelle PPT-/Power-Werte anzeigen")
    parser.add_argument("--set", metavar="PPT",
                        help="Dry-Run: Zeigt nur an, auf welchen PPT (W) gestellt würde, ohne zu schreiben. Beispiel: --set 220")

    args = parser.parse_args()

    card = find_amd_card()
    hwmon = find_hwmon(card)
    if not hwmon:
        print(f"Konnte hwmon für {card} nicht finden.")
        return

    p_cap     = os.path.join(hwmon, "power1_cap")
    p_cap_min = os.path.join(hwmon, "power1_cap_min")
    p_cap_max = os.path.join(hwmon, "power1_cap_max")

    cap     = read_int(p_cap)
    cap_min = read_int(p_cap_min)
    cap_max = read_int(p_cap_max)

    print(f"AMD-Karte: {card}")
    print(f"hwmon:     {hwmon}")
    print()

    if cap is not None:
        print(f"power1_cap:      {cap} µW  ({cap/1e6:.1f} W)")
    if cap_min is not None:
        print(f"power1_cap_min:  {cap_min} µW  ({cap_min/1e6:.1f} W)")
    if cap_max is not None:
        print(f"power1_cap_max:  {cap_max} µW  ({cap_max/1e6:.1f} W)")
    print()

    pm_info = read_pm_info(card_index=int(card.replace("card", "")))
    avg_power, gfx_clk, mclk, temp = parse_pm_info_block(pm_info) if "Fehler" not in pm_info else (None, None, None, None)

    if "Fehler" not in pm_info:
        print("Auszug aus amdgpu_pm_info (sudo):")
        if gfx_clk is not None:
            print(f"  SCLK:      {gfx_clk} MHz")
        if mclk is not None:
            print(f"  MCLK:      {mclk} MHz")
        if avg_power is not None:
            print(f"  avg SoC:   {avg_power:.1f} W")
        if temp is not None:
            print(f"  GPU Temp:  {temp} °C")
    else:
        print(pm_info)
    print()

    if args.set:
        try:
            new_ppt_w = int(args.set)
        except ValueError:
            print(f"Ungültiger PPT-Wert: {args.set}")
            return
        new_ppt_uw = new_ppt_w * 1_000_000
        print("DRY-RUN: Es wird NICHT geschrieben.")
        print("Geplanter Schritt wäre:")
        print()
        print(textwrap.dedent(f"""
            sudo tee {p_cap} <<EOF
            {new_ppt_uw}
            EOF
        """).strip())
        if cap is not None:
            print()
            print(f"Aktueller PPT: {cap/1e6:.1f} W  ->  Gewünschter PPT: {new_ppt_w:.1f} W")
        if cap_max is not None and new_ppt_uw > cap_max:
            print(f"Hinweis: {new_ppt_w:.1f} W liegt ÜBER power1_cap_max ({cap_max/1e6:.1f} W).")
        print()
        print("Es wurde NICHT ins System geschrieben (read-only Modus).")

if __name__ == "__main__":
    main()
