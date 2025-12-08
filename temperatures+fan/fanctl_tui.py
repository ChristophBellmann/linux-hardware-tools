#!/usr/bin/env python3
import curses
import os
import time
from typing import Optional, Dict

HWMON_DIR = "/sys/class/hwmon/hwmon2"  # nct6798 auf deinem B550I
CHANNELS = [1, 2, 5]  # typische Zuordnung: CPU / Case / Pumpe

# Leerlauf-Update-Intervall (wenn keine Eingabe erfolgt)
UPDATE_INTERVAL = 0.3  # Sekunden (~3x pro Sekunde)


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


# --------- Snapshot/Restore der ursprünglichen Mainboard-Einstellungen ---------


def snapshot_initial_state() -> Dict[str, int]:
    """
    Merkt sich für alle in CHANNELS verwendeten PWM-Kanäle:
    - pwmX
    - pwmX_enable

    Genau der Zustand, der beim Programmstart gesetzt ist,
    wird später beim Beenden wiederhergestellt.
    """
    state: Dict[str, int] = {}

    if not os.path.isdir(HWMON_DIR):
        return state

    for ch in CHANNELS:
        for path_func in (pwm_path, pwm_enable_path):
            path = path_func(ch)
            val = read_int(path)
            if val is not None:
                state[path] = val

    return state


def restore_initial_state(state: Dict[str, int]) -> None:
    """
    Schreibt alle früher gespeicherten Werte wieder zurück.
    Wird im finally-Block aufgerufen, d.h. auch bei Exceptions.
    """
    for path, val in state.items():
        write_int(path, val)


# ------------------------------------------------------------------------


def main(stdscr, initial_state: Dict[str, int]):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)  # alle 50 ms auf Eingaben prüfen

    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    last_msg = ""

    if not os.path.isdir(HWMON_DIR):
        stdscr.addstr(0, 0, f"{HWMON_DIR} nicht gefunden (nct6798?).")
        stdscr.addstr(1, 0, "Beenden mit q oder ESC.")
        while True:
            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q"), 27):
                return

    selected_idx = 0
    last_update = 0.0
    force_refresh = True  # beim Start einmal zeichnen

    while True:
        key = stdscr.getch()
        now = time.time()

        if key != -1:
            # jede Eingabe → sofort neu zeichnen
            if key in (ord("q"), ord("Q")):
                break

            # ESC → sofort Restore + Exit
            elif key == 27:
                if is_root and initial_state:
                    restore_initial_state(initial_state)
                break

            # Tab oder Cursor hoch/runter: Kanal wechseln
            elif key == 9:
                selected_idx = (selected_idx + 1) % len(CHANNELS)
                force_refresh = True
            elif hasattr(curses, "KEY_BTAB") and key == curses.KEY_BTAB:
                selected_idx = (selected_idx - 1) % len(CHANNELS)
                force_refresh = True
            elif key == curses.KEY_UP:
                selected_idx = (selected_idx - 1) % len(CHANNELS)
                force_refresh = True
            elif key == curses.KEY_DOWN:
                selected_idx = (selected_idx + 1) % len(CHANNELS)
                force_refresh = True

            # Links/Rechts bzw. - / +: PWM-Wert ändern
            elif key in (curses.KEY_LEFT, ord("-")):
                ch = CHANNELS[selected_idx]
                pv = read_int(pwm_path(ch)) or 0
                if is_root:
                    ok_en = write_int(pwm_enable_path(ch), 1)
                    ok_pwm = write_int(pwm_path(ch), clamp(pv - 8, 0, 255))
                    if not (ok_en and ok_pwm):
                        last_msg = f"Fehler beim Schreiben auf pwm{ch} (Rechte?)"
                    else:
                        last_msg = ""
                else:
                    last_msg = "Keine root-Rechte: PWM-Änderungen werden ignoriert."
                force_refresh = True

            elif key in (curses.KEY_RIGHT, ord("+"), ord("=")):
                ch = CHANNELS[selected_idx]
                pv = read_int(pwm_path(ch)) or 0
                if is_root:
                    ok_en = write_int(pwm_enable_path(ch), 1)
                    ok_pwm = write_int(pwm_path(ch), clamp(pv + 8, 0, 255))
                    if not (ok_en and ok_pwm):
                        last_msg = f"Fehler beim Schreiben auf pwm{ch} (Rechte?)"
                    else:
                        last_msg = ""
                else:
                    last_msg = "Keine root-Rechte: PWM-Änderungen werden ignoriert."
                force_refresh = True

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
                            last_msg = ""
                    else:
                        if not write_int(en_path, 1):  # Manuell
                            last_msg = f"Fehler beim Setzen von pwm{ch}_enable auf 1"
                        else:
                            last_msg = ""
                else:
                    last_msg = "Keine root-Rechte: Mode-Änderungen werden ignoriert."
                force_refresh = True

            elif key in (ord("r"), ord("R")):
                # manueller Reset auf Startzustand
                if is_root and initial_state:
                    restore_initial_state(initial_state)
                    last_msg = "Ursprüngliche Mainboard-Einstellungen wiederhergestellt."
                elif not is_root:
                    last_msg = "Keine root-Rechte: Restore nicht möglich."
                force_refresh = True

        # Zeichnen nur, wenn
        #  - Eingabe war (force_refresh), oder
        #  - genug Zeit seit letztem Update vergangen (Idle-Refresh)
        if not force_refresh and (now - last_update) < UPDATE_INTERVAL:
            continue

        last_update = now
        force_refresh = False

        # --- Anzeige aktualisieren ---
        stdscr.erase()
        stdscr.addstr(0, 0, "Fan/Pumpen-Steuerung (nct6798 hwmon2)")
        mode_str = "root (Schreiben erlaubt)" if is_root else "nicht-root (nur Lesen, keine PWM-Änderung)"
        stdscr.addstr(1, 0, f"Modus: {mode_str}")
        stdscr.addstr(
            2,
            0,
            "q/ESC: Quit  ↑/↓/TAB: Kanal  ←/→/-/+: PWM  a: Auto/Manuell  r: Reset auf Startzustand",
        )
        stdscr.addstr(
            3,
            0,
            "Navigation & Änderungen: sofortige Anzeige, im Idle langsamer Refresh.",
        )
        stdscr.addstr(
            4,
            0,
            "Beim Beenden werden die ursprünglichen Mainboard-Werte automatisch wiederhergestellt.",
        )

        if last_msg:
            stdscr.addstr(5, 0, f"Status: {last_msg}")
        else:
            stdscr.addstr(5, 0, "Status: OK")

        row = 7
        for idx, ch in enumerate(CHANNELS):
            fan_rpm = read_int(fan_input_path(ch))
            pwm_val = read_int(pwm_path(ch))
            en_val = read_int(pwm_enable_path(ch))

            sel_marker = ">" if idx == selected_idx else " "
            mode = {
                0: "OFF/unk",
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
    # Zustand beim Start merken
    initial_state = snapshot_initial_state()
    try:
        curses.wrapper(main, initial_state)
    finally:
        # Egal wie das Programm endet: ursprüngliche Werte wiederherstellen
        if initial_state:
            restore_initial_state(initial_state)

