#!/usr/bin/env bash

set -euo pipefail

# Automatisiert die CPU-X-Prime-Benchmarks (fast)
# - Ein Lauf mit 1 Kern
# - Ein Lauf mit allen Kernen
# Für jeden Lauf wird die maximale und durchschnittliche CPU-Frequenz (wie in ./cpufreqs.sh)
# und das Benchmark-Ergebnis protokolliert.
#
# Nutzung:
#   ./primeautomation.sh [dauer_in_sekunden]
#   ./primeautomation.sh -m TPU [dauer_in_sekunden]
#
# Ergebnis-Datei:
#   primeresults.csv

DURATION=60
NOTES="default"
RESULTS_FILE="primeresults.csv"
MAXLOG="max.log"
AVGLOG="avg.log"
COUNTLOG="samples.log"

while getopts ":m:h" opt; do
  case "$opt" in
    m)
      NOTES="$OPTARG"
      ;;
    h)
      echo "Nutzung: $0 [-m notes] [dauer_in_sekunden]" >&2
      exit 0
      ;;
    \?)
      echo "Unbekannte Option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG benötigt ein Argument." >&2
      exit 1
      ;;
  esac
done
shift $((OPTIND - 1))

if [[ $# -ge 1 ]]; then
  DURATION="$1"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -x ./primebench.sh ]]; then
  echo "Fehler: ./primebench.sh nicht gefunden oder nicht ausführbar." >&2
  exit 1
fi

if [[ ! -x ./cpufreqs.sh ]]; then
  echo "Fehler: ./cpufreqs.sh nicht gefunden oder nicht ausführbar." >&2
  exit 1
fi

if ! command -v nproc >/dev/null 2>&1; then
  echo "Warnung: 'nproc' nicht gefunden, nehme 1 Kern an." >&2
  CPU_COUNT=1
else
  CPU_COUNT=$(nproc)
fi

if ! command -v taskset >/dev/null 2>&1; then
  echo "Fehler: 'taskset' wird benötigt, um auf Kerne zu pinnen." >&2
  exit 1
fi

if [[ ! -f "$RESULTS_FILE" ]]; then
  echo "label,cores,duration_s,primes_total,max_number,max_freq_mhz,avg_freq_mhz,timestamp,notes" > "$RESULTS_FILE"
fi

start_freq_monitor() {
  echo 0 > "$MAXLOG"
  echo 0 > "$AVGLOG"
  echo 0 > "$COUNTLOG"
  ./cpufreqs.sh > "$1" 2>&1 &
  echo $!
}

stop_freq_monitor() {
  local pid="$1"
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

single_core_run() {
  echo "=== Starte Single-Core-Lauf (1 Kern, fast) ==="
  local freq_log="cpufreq_1core.log"
  local bench_log="bench_1core.log"

  local freq_pid
  freq_pid=$(start_freq_monitor "$freq_log")

  taskset -c 0 ./primebench.sh "$DURATION" fast > "$bench_log" 2>&1

  stop_freq_monitor "$freq_pid"

  local max_freq avg_freq
  max_freq=$(cat "$MAXLOG" 2>/dev/null || echo 0)
  avg_freq=$(cat "$AVGLOG" 2>/dev/null || echo 0)

  local primes max_number
  primes=$(grep '^Primes' "$bench_log" | awk '{print $3}')
  max_number=$(grep '^Max number' "$bench_log" | awk '{print $4}')

  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')

  echo "Single-Core Ergebnis: primes=$primes max_number=$max_number max_freq=${max_freq}MHz avg_freq=${avg_freq}MHz"
  echo "single,1,$DURATION,$primes,$max_number,$max_freq,$avg_freq,$ts,$NOTES" >> "$RESULTS_FILE"
}

all_cores_run() {
  echo "=== Starte All-Core-Lauf ($CPU_COUNT Kerne, fast) ==="
  local freq_log="cpufreq_allcore.log"

  local freq_pid
  freq_pid=$(start_freq_monitor "$freq_log")

  local pids=()
  for ((cpu = 0; cpu < CPU_COUNT; cpu++)); do
    local bench_log="bench_allcore_core${cpu}.log"
    taskset -c "$cpu" ./primebench.sh "$DURATION" fast > "$bench_log" 2>&1 &
    pids+=("$!")
  done

  for pid in "${pids[@]}"; do
    wait "$pid"
  done

  stop_freq_monitor "$freq_pid"

  local max_freq avg_freq
  max_freq=$(cat "$MAXLOG" 2>/dev/null || echo 0)
  avg_freq=$(cat "$AVGLOG" 2>/dev/null || echo 0)

  local primes_total max_number
  primes_total=$(grep '^Primes' bench_allcore_core*.log | awk '{sum+=$3} END {print sum+0}')
  max_number=$(grep '^Max number' bench_allcore_core*.log | awk '{if($4>m)m=$4} END {print m+0}')

  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')

  echo "All-Core Ergebnis: primes_total=$primes_total max_number=$max_number max_freq=${max_freq}MHz avg_freq=${avg_freq}MHz"
  echo "all,$CPU_COUNT,$DURATION,$primes_total,$max_number,$max_freq,$avg_freq,$ts,$NOTES" >> "$RESULTS_FILE"
}

single_core_run
all_cores_run

rm -f *.log

echo "Fertig. Ergebnisse in $RESULTS_FILE gespeichert."
