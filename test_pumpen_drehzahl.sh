#!/usr/bin/env bash
set -euo pipefail

# Einfaches Testskript, um für einen ausgewählten
# PWM-Kanal am Nuvoton nct6798-Chip die Drehzahländerung
# zu beobachten.
#
# WICHTIG:
# - NUR auf dem Kanal benutzen, von dem du sicher bist,
#   dass dort die Pumpe hängt.
# - Im Zweifel vorher im BIOS schauen / Handbuch checken.
# - Skript mit sudo ausführen, damit Schreibzugriff auf /sys möglich ist.
#
# Aufrufbeispiele:
#   sudo ./test_pumpen_drehzahl.sh 2   # testet pwm2
#   sudo ./test_pumpen_drehzahl.sh 5   # testet pwm5

PWM_CH="${1:-2}"          # Standard: pwm2, kannst du beim Aufruf ändern
HWMON_DIR="/sys/class/hwmon/hwmon2"   # nct6798 laut sensors/hwmon-Ausgabe

PWM_PATH="$HWMON_DIR/pwm${PWM_CH}"
PWM_ENABLE="$HWMON_DIR/pwm${PWM_CH}_enable"
FAN_INPUT="$HWMON_DIR/fan${PWM_CH}_input"  # häufig gleiche Nummer, ggf. abweichend

if [ ! -e "$PWM_PATH" ]; then
  echo "PWM-Kanal pwm${PWM_CH} existiert nicht unter $HWMON_DIR." >&2
  echo "Bitte anderen Kanal testen (z.B. 1, 2 oder 5)." >&2
  exit 1
fi

echo "Nutze $PWM_PATH (Kanal ${PWM_CH})" >&2

if [ ! -e "$FAN_INPUT" ]; then
  echo "WARNUNG: Kein passender fan${PWM_CH}_input gefunden." >&2
  echo "Ich zeige stattdessen alle fan*_input-Werte vor jedem Schritt." >&2
  SHOW_ALL_FANS=1
else
  SHOW_ALL_FANS=0
fi

show_rpm() {
  echo "--- aktuelle Drehzahlen ---" >&2
  if [ "$SHOW_ALL_FANS" -eq 1 ]; then
    grep . "$HWMON_DIR"/fan*_input 2>/dev/null || true
  else
    echo -n "fan${PWM_CH}_input: "
    cat "$FAN_INPUT" 2>/dev/null || echo "(nicht lesbar)"
  fi
  echo >&2
}

# Aktuelle Werte anzeigen
show_rpm

# Auf manuellen Modus stellen (1 = manuell, 2 = automatisch)
echo "Setze pwm${PWM_CH}_enable auf 1 (manuell)…" >&2
echo 1 > "$PWM_ENABLE"

# Teststufen: niedrig -> mittel -> hoch -> zurück
for val in 80 128 180 230 255 180 128; do
  echo "Setze pwm${PWM_CH} = $val" >&2
  echo "$val" > "$PWM_PATH"
  sleep 8
  show_rpm
done

echo "Test beendet. Du kannst pwm${PWM_CH}_enable wieder auf 2 (Auto) setzen:" >&2
echo "  echo 2 | sudo tee $PWM_ENABLE" >&2
