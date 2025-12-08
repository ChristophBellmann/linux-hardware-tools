#!/usr/bin/env python3
import os
import time
import curses


def read_core_freqs():
    freqs = {}
    base_path = "/sys/devices/system/cpu"

    for entry in sorted(os.listdir(base_path)):
        if not entry.startswith("cpu"):
            continue
        suffix = entry[3:]
        if not suffix.isdigit():
            continue

        cpu_id = int(suffix)
        freq_path = os.path.join(
            base_path,
            entry,
            "cpufreq",
            "scaling_cur_freq",
        )

        try:
            with open(freq_path, "r", encoding="utf-8") as f:
                kHz = int(f.read().strip() or "0")
                freqs[cpu_id] = kHz / 1000.0  # MHz
        except (FileNotFoundError, ValueError, OSError):
            continue

    return freqs


def draw_freqs(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    rows_per_block = 6
    blocks_per_row = 4
    block_width = 16  # chars

    while True:
        ch = stdscr.getch()
        if ch in (ord("q"), 27):  # q oder ESC
            break

        freqs = read_core_freqs()
        stdscr.erase()

        if not freqs:
            stdscr.addstr(0, 0, "Keine CPU-Frequenzdaten gefunden (cpufreq).")
            stdscr.refresh()
            time.sleep(0.5)
            continue

        stdscr.addstr(0, 0, "Aktuelle Kernfrequenzen (MHz) – q/ESC beendet")

        cores = sorted(freqs.keys())
        max_cores = rows_per_block * blocks_per_row
        cores = cores[:max_cores]

        for idx, cpu_id in enumerate(cores):
            block_idx = idx // rows_per_block
            row_in_block = idx % rows_per_block

            col_block = block_idx  # eine Blockreihe, 4 nebeneinander

            col = col_block * block_width
            row = 2 + row_in_block

            label = f"CPU{cpu_id:02d}"
            val = f"{freqs[cpu_id]:6.1f}"
            stdscr.addstr(row, col, f"{label}: {val}")

        stdscr.refresh()
        time.sleep(0.1)


def main():
    curses.wrapper(draw_freqs)


if __name__ == "__main__":
    main()
