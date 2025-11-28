#!/usr/bin/env python3
import curses
import os
import time
from collections import defaultdict
from typing import Optional, List, Tuple

HWMON_BASE = "/sys/class/hwmon"


def read_file(path: str) -> Optional[str]:
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return None


def list_temp_channels(hwmon_dir: str) -> List[int]:
    try:
        entries = os.listdir(hwmon_dir)
    except Exception:
        return []
    indices = set()
    for name in entries:
        if name.startswith("temp") and name.endswith("_input"):
            middle = name[len("temp") : -len("_input")]
            if middle.isdigit():
                indices.add(int(middle))
    return sorted(indices)


def read_temp(hwmon_dir: str, idx: int) -> Tuple[str, Optional[float]]:
    label_path = os.path.join(hwmon_dir, f"temp{idx}_label")
    input_path = os.path.join(hwmon_dir, f"temp{idx}_input")

    label = read_file(label_path) or f"temp{idx}"

    raw = read_file(input_path)
    if raw is None:
        return label, None

    try:
        # Werte sind in Milligrad Celsius
        value_c = int(raw) / 1000.0
    except ValueError:
        return label, None

    return label, value_c


def detect_category(hwmon_name: str) -> str:
    name = hwmon_name.lower()
    if "amdgpu" in name or name.startswith("nvidia") or "gpu" in name:
        return "GPU"
    if "k10temp" in name or "coretemp" in name or "zenpower" in name:
        return "CPU"
    if name.startswith("acpitz") or name.startswith("thermal"):
        return "CPU/SoC"
    if "nct" in name:
        return "Mainboard"
    return "Sonstiges"


def find_temp_sensors():
    sensors = []
    if not os.path.isdir(HWMON_BASE):
        return sensors

    for entry in sorted(os.listdir(HWMON_BASE)):
        hwmon_dir = os.path.join(HWMON_BASE, entry)
        name_path = os.path.join(hwmon_dir, "name")
        hwmon_name = read_file(name_path) or "unknown"
        temps = list_temp_channels(hwmon_dir)
        if not temps:
            continue
        category = detect_category(hwmon_name)
        sensors.append((category, hwmon_name, hwmon_dir, temps))
    return sensors


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(200)

    last_update = 0.0

    while True:
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            break

        now = time.time()
        if now - last_update < 1.0:
            continue
        last_update = now

        max_y, max_x = stdscr.getmaxyx()
        sensors = find_temp_sensors()

        stdscr.erase()
        stdscr.addstr(0, 0, "Temperatur-Übersicht CPU / GPU / Mainboard"[: max_x - 1])
        stdscr.addstr(1, 0, f"Quelle: {HWMON_BASE}/*"[: max_x - 1])
        stdscr.addstr(
            2, 0, "Aktualisierung ca. 1x pro Sekunde, q: Quit"[: max_x - 1]
        )

        if not sensors:
            if 4 < max_y:
                stdscr.addstr(4, 0, "Keine temp*-Sensoren gefunden."[: max_x - 1])
            stdscr.refresh()
            continue

        grouped = defaultdict(list)
        for category, hwmon_name, hwmon_dir, temps in sensors:
            grouped[category].append((hwmon_name, hwmon_dir, temps))

        row = 4
        order = ["CPU", "CPU/SoC", "GPU", "Mainboard", "Sonstiges"]
        for category in order:
            if category not in grouped:
                continue

            if row >= max_y - 1:
                break
            stdscr.addstr(row, 0, f"[{category}]"[: max_x - 1])
            row += 1

            for hwmon_name, hwmon_dir, temps in grouped[category]:
                if row >= max_y - 1:
                    break
                base = os.path.basename(hwmon_dir)
                stdscr.addstr(row, 0, f"  {hwmon_name} ({base})"[: max_x - 1])
                row += 1
                if row >= max_y - 1:
                    break
                header = f"    {'Kanal':<8} {'Label':<20} {'Temp [°C]':>10}"
                stdscr.addstr(row, 0, header[: max_x - 1])
                row += 1
                if row >= max_y - 1:
                    break
                stdscr.addstr(row, 0, ("    " + "-" * 38)[: max_x - 1])
                row += 1

                for idx in temps:
                    if row >= max_y - 1:
                        break
                    label, value_c = read_temp(hwmon_dir, idx)
                    if value_c is None:
                        temp_str = "?"
                    else:
                        temp_str = f"{value_c:5.1f}"

                    line = f"    temp{idx:<3} {label:<20.20} {temp_str:>10}"
                    stdscr.addstr(row, 0, line[: max_x - 1])
                    row += 1

                row += 1

        stdscr.refresh()


if __name__ == "__main__":
    curses.wrapper(main)
