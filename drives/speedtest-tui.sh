#!/usr/bin/env bash
set -euo pipefail

need() { command -v "$1" >/dev/null 2>&1; }

for cmd in whiptail fio lsblk findmnt sudo; do
  need "$cmd" || { echo "Fehlt: $cmd"; exit 1; }
done

# Sudo vorher "warm machen", damit fio später nicht unsichtbar nach Passwort fragt
sudo -v

timestamp() { date +"%Y-%m-%d_%H-%M-%S"; }

MENU_ITEMS=()

# Raw block devices
while read -r name size model type; do
  [[ "$type" == "disk" ]] || continue
  MENU_ITEMS+=("/dev/$name" "RAW  $size  ${model:-unknown}")
done < <(lsblk -d -n -o NAME,SIZE,MODEL,TYPE)

# Mounted filesystems (root + /media)
while read -r target source fstype; do
  [[ "$target" == / ]] || [[ "$target" == /media/* ]] || continue
  MENU_ITEMS+=("$target" "FS   $fstype  ($source)")
done < <(findmnt -rno TARGET,SOURCE,FSTYPE)

CHOICE=$(whiptail --title "Speedtest" --menu "Ziel auswählen" 22 90 12 \
  "${MENU_ITEMS[@]}" 3>&1 1>&2 2>&3) || exit 0

SEQ_BS="1M"
RAND_BS="4k"
IODEPTH="32"
SIZE_GB="8"
RUNTIME="15"

SIZE_GB=$(whiptail --inputbox "Testgröße in GiB" 10 60 "$SIZE_GB" 3>&1 1>&2 2>&3) || exit 0
RUNTIME=$(whiptail --inputbox "Laufzeit je Test (Sekunden)" 10 60 "$RUNTIME" 3>&1 1>&2 2>&3) || exit 0

SAFE_NAME=$(echo "$CHOICE" | sed 's#^/##; s#[/ ]#_#g; s#^$#root#g')
LOG="speedtest_${SAFE_NAME}_$(timestamp).log"

exec > >(tee -a "$LOG") 2>&1

echo "=== Speedtest $(timestamp) ==="
echo "Target: $CHOICE"
echo "Kernel: $(uname -r)"
echo

IOENG="libaio"
fio --enghelp 2>/dev/null | grep -q io_uring && IOENG="io_uring"

run_fio() {
  local name="$1"
  local file="$2"
  local rw="$3"
  local bs="$4"

  sudo fio \
    --name="$name" \
    --filename="$file" \
    --rw="$rw" \
    --bs="$bs" \
    --iodepth="$IODEPTH" \
    --numjobs=1 \
    --direct=1 \
    --ioengine="$IOENG" \
    --size="${SIZE_GB}G" \
    --time_based \
    --runtime="$RUNTIME" \
    --group_reporting
}

prep_file() {
  local file="$1"
  echo "--- PREP (create file) ---"
  # Datei einmalig mit Daten füllen, damit READ/RANDREAD realistisch sind
  sudo fio \
    --name=prep \
    --filename="$file" \
    --rw=write \
    --bs=1M \
    --iodepth="$IODEPTH" \
    --numjobs=1 \
    --direct=1 \
    --ioengine="$IOENG" \
    --size="${SIZE_GB}G" \
    --group_reporting \
    --end_fsync=1
}

whiptail --infobox "Läuft… Ausgabe steht im Terminal + Log:\n$LOG" 8 70

if [[ "$CHOICE" == /dev/* ]]; then
  echo "--- RAW DEVICE TEST ---"
  lsblk "$CHOICE" || true
  echo

  echo "--- SEQ READ ---"
  run_fio seq_read "$CHOICE" read "$SEQ_BS"
  echo

  echo "--- RAND READ ---"
  run_fio rand_read "$CHOICE" randread "$RAND_BS"
  echo
else
  TESTFILE="$CHOICE/fio_test.bin"

  echo "--- FILESYSTEM TEST ---"
  df -h "$CHOICE" || true
  echo

  prep_file "$TESTFILE"
  echo

  echo "--- SEQ READ ---"
  run_fio seq_read "$TESTFILE" read "$SEQ_BS"
  echo

  echo "--- RAND READ ---"
  run_fio rand_read "$TESTFILE" randread "$RAND_BS"
  echo

  sudo rm -f "$TESTFILE" || true
fi

echo "=== Fertig ==="
echo "Logfile: $LOG"
whiptail --msgbox "Speedtest abgeschlossen.\n\nLogfile:\n$LOG" 12 70
