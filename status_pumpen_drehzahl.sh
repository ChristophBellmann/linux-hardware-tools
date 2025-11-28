#!/usr/bin/env bash
set -euo pipefail

# Zeigt aktuelle Drehzahl(en) und PWM-Werte für nct6798 (hwmon2).
# Kein sudo nötig, da nur gelesen wird.

HWMON_DIR="/sys/class/hwmon/hwmon2"   # nct6798 laut vorheriger Ausgabe

if [ ! -d "$HWMON_DIR" ]; then
  echo "$HWMON_DIR nicht gefunden (nct6798 nicht geladen?)." >&2
  exit 1
fi

echo "=== Aktuelle Lüfter-/Pumpen-Werte (nct6798) ==="

# Zeige alle fan*_input
for f in "$HWMON_DIR"/fan*_input; do
  [ -e "$f" ] || continue
  bn="$(basename "$f")"
  printf "%-15s : " "$bn"
  cat "$f" 2>/dev/null || echo "(nicht lesbar)"
done

# Zeige alle pwm*
for p in "$HWMON_DIR"/pwm[0-9]; do
  [ -e "$p" ] || continue
  bn="$(basename "$p")"
  printf "%-15s : " "$bn"
  cat "$p" 2>/dev/null || echo "(nicht lesbar)"
  en="$HWMON_DIR/${bn}_enable"
  if [ -e "$en" ]; then
    printf "%-15s   " "${bn}_enable"
    cat "$en" 2>/dev/null || echo "(nicht lesbar)"
  fi
  echo
done
