#!/usr/bin/env python3
import curses
import os
import time
from typing import Optional

HWMON_DIR = "/sys/class/hwmon/hwmon2"  # nct6798
CHANNELS = [1, 2, 5]  # typische Zuordnung: CPU / Case / Pumpe


def read_int(path: str) -> Optional[int]:
    try:
        with open(path, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None


def write_int(path: str, value: int) -> bool:
    try:
        with open(path, "w") as f:
            f.write(str(value))
        return True
    except Exception:
        return False


def pwm_path(ch: int) -> str:
    return os.path.join(HWMON_DIR, f"pwm{ch}")


def pwm_enable_path(ch: int) -> str:
    return os.path.join(HWMON_DIR, f"pwm{ch}_enable")


def fan_input_path(ch: int) -> str:
    return os.path.join(HWMON_DIR, f"fan{ch}_input")


def clamp(val: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, val))


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)  # 100 ms für flüssigere Eingabe

    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    last_msg = ""

    if not os.path.isdir(HWMON_DIR):
        stdscr.addstr(0, 0, f"{HWMON_DIR} nicht gefunden (nct6798?).")
        stdscr.addstr(1, 0, "Beenden mit q.")
        while True:
            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q")):
                return
        
    selected_idx = 0
    last_update = 0.0

    while True:
        # Eingabe (nicht-blockierend / kurz blockierend)
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            break
        # Tab: nächster Kanal (nutze nur den Tab-Zeichencode, da KEY_TAB
        # auf manchen Systemen nicht definiert ist)
        elif key == 9:
            selected_idx = (selected_idx + 1) % len(CHANNELS)
        # Shift+Tab (wenn verfügbar) oder ESC-[Z Sequenz wäre komplexer,
        # daher hier nur KEY_BTAB, wenn curses ihn definiert.
        elif hasattr(curses, "KEY_BTAB") and key == curses.KEY_BTAB:
            selected_idx = (selected_idx - 1) % len(CHANNELS)
        elif key in (curses.KEY_LEFT, ord("-")):
            ch = CHANNELS[selected_idx]
            pv = read_int(pwm_path(ch)) or 0
            if is_root:
                ok_en = write_int(pwm_enable_path(ch), 1)
                ok_pwm = write_int(pwm_path(ch), clamp(pv - 8, 0, 255))
                if not (ok_en and ok_pwm):
                    last_msg = f"Fehler beim Schreiben auf pwm{ch} (Rechte?)"
            else:
                last_msg = "Keine root-Rechte: PWM-Änderungen werden ignoriert."
        elif key in (curses.KEY_RIGHT, ord("+"), ord("=")):
            ch = CHANNELS[selected_idx]
            pv = read_int(pwm_path(ch)) or 0
            if is_root:
                ok_en = write_int(pwm_enable_path(ch), 1)
                ok_pwm = write_int(pwm_path(ch), clamp(pv + 8, 0, 255))
                if not (ok_en and ok_pwm):
                    last_msg = f"Fehler beim Schreiben auf pwm{ch} (Rechte?)"
            else:
                last_msg = "Keine root-Rechte: PWM-Änderungen werden ignoriert."
        elif key == curses.KEY_UP:
            ch = CHANNELS[selected_idx]
            pv = read_int(pwm_path(ch)) or 0
            if is_root:
                ok_en = write_int(pwm_enable_path(ch), 1)
                ok_pwm = write_int(pwm_path(ch), clamp(pv + 32, 0, 255))
                if not (ok_en and ok_pwm):
                    last_msg = f"Fehler beim Schreiben auf pwm{ch} (Rechte?)"
            else:
                last_msg = "Keine root-Rechte: PWM-Änderungen werden ignoriert."
        elif key == curses.KEY_DOWN:
            ch = CHANNELS[selected_idx]
            pv = read_int(pwm_path(ch)) or 0
            if is_root:
                ok_en = write_int(pwm_enable_path(ch), 1)
                ok_pwm = write_int(pwm_path(ch), clamp(pv - 32, 0, 255))
                if not (ok_en and ok_pwm):
                    last_msg = f"Fehler beim Schreiben auf pwm{ch} (Rechte?)"
            else:
                last_msg = "Keine root-Rechte: PWM-Änderungen werden ignoriert."
        elif key in (ord("a"), ord("A")):
            # Auto/Manuell umschalten
            ch = CHANNELS[selected_idx]
            en_path = pwm_enable_path(ch)
            cur = read_int(en_path)
            if is_root:
                if cur == 1:
                    if not write_int(en_path, 2):  # Auto
                        last_msg = f"Fehler beim Setzen von pwm{ch}_enable auf 2"
                else:
                    if not write_int(en_path, 1):  # Manuell
                        last_msg = f"Fehler beim Setzen von pwm{ch}_enable auf 1"
            else:
                last_msg = "Keine root-Rechte: Mode-Änderungen werden ignoriert."

        now = time.time()
        if now - last_update < 1.0:
            continue
        last_update = now

        stdscr.erase()
        stdscr.addstr(0, 0, "Fan/Pumpen-Steuerung (nct6798 hwmon2)")
        mode_str = "root (Schreiben erlaubt)" if is_root else "nicht-root (nur Lesen, keine PWM-Änderung)"
        stdscr.addstr(1, 0, f"Modus: {mode_str}")
        stdscr.addstr(2, 0, "q: Quit  TAB: Kanal wechseln  ←/→/-/+: PWM  ↑/↓: grob  a: Auto/Manuell")
        stdscr.addstr(3, 0, "Anzeige aktualisiert sich etwa einmal pro Sekunde.")

        if last_msg:
            stdscr.addstr(4, 0, f"Status: {last_msg}")
        else:
            stdscr.addstr(4, 0, "Status: OK")

        row = 6
        for idx, ch in enumerate(CHANNELS):
            fan_rpm = read_int(fan_input_path(ch))
            pwm_val = read_int(pwm_path(ch))
            en_val = read_int(pwm_enable_path(ch))

            sel_marker = ">" if idx == selected_idx else " "
            mode = {
                0: "OFF/unk",  # selten genutzt
                1: "MANUAL",
                2: "AUTO",
                3: "AUTO_HWP",
            }.get(en_val, str(en_val) if en_val is not None else "?")

            line = (
                f"{sel_marker} Kanal pwm{ch}: "
                f"PWM={pwm_val if pwm_val is not None else '?':>3} "
                f"Mode={mode:<8} "
                f"RPM={fan_rpm if fan_rpm is not None else '?'}"
            )
            stdscr.addstr(row, 0, line)
            row += 1

        stdscr.refresh()


if __name__ == "__main__":
    curses.wrapper(main)
