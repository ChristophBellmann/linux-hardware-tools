#!/usr/bin/env bash

RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
BOLD="\033[1m"
RESET="\033[0m"

find_amd_card() {
  for c in /sys/class/drm/card*; do
    if [ -f "$c/device/vendor" ]; then
      v=$(cat "$c/device/vendor")
      if [ "$v" = "0x1002" ]; then
        basename "$c"
        return
      fi
    fi
  done
  echo "card1"
}

CARD=$(find_amd_card)

find_hwmon() {
  for h in /sys/class/drm/$CARD/device/hwmon/hwmon*; do
    if [ -f "$h/temp2_input" ]; then
      echo "$h"
      return
    fi
  done
}

HWMON=$(find_hwmon)

if [ ! -d "/sys/class/drm/$CARD" ] || [ -z "$HWMON" ]; then
  echo "Konnte AMD-GPU oder hwmon nicht finden. CARD=$CARD HWMON=$HWMON"
  exit 1
fi

PP_SCLK="/sys/class/drm/$CARD/device/pp_dpm_sclk"
GPU_BUSY="/sys/class/drm/$CARD/device/gpu_busy_percent"
PWR_AVG="$HWMON/power1_average"
PWR_CAP="$HWMON/power1_cap"

read_temp() {
  local idx=$1
  local f="$HWMON/temp${idx}_input"
  [ -f "$f" ] || { echo ""; return; }
  local v
  v=$(cat "$f" 2>/dev/null)
  [ -n "$v" ] || { echo ""; return; }
  awk "BEGIN {printf \"%.1f\", $v/1000.0}"
}

read_power_w() {
  local f=$1
  [ -f "$f" ] || { echo ""; return; }
  local v
  v=$(cat "$f" 2>/dev/null)
  [ -n "$v" ] || { echo ""; return; }
  awk "BEGIN {printf \"%.1f\", $v/1000000.0}"
}

# Cursor ausblenden, bei Abbruch wieder einblenden
tput civis 2>/dev/null || true
trap 'tput cnorm 2>/dev/null || true; printf "\033[0m\n"; exit 0' INT TERM

# einmal komplett löschen und nach oben
printf '\033[2J\033[H'

while true; do
  # Cursor nach oben links, Rest später mit \033[J gelöscht → kein hartes Flackern
  printf '\033[H'

  echo -e "${BOLD}${CYAN}AMD GPU Monitor ($CARD)${RESET}  $(date +'%H:%M:%S')"
  echo

  cur_clk=""
  max_clk=""
  if [ -f "$PP_SCLK" ]; then
    dpm=$(cat "$PP_SCLK")
    cur_clk=$(printf "%s\n" "$dpm" | awk '/\*/ {gsub("Mhz","",$2); print $2}')
    max_clk=$(printf "%s\n" "$dpm" | awk '{gsub("Mhz","",$2); last=$2} END {print last}')
  fi

  edge=$(read_temp 1)
  hot=$(read_temp 2)
  vram=$(read_temp 3)

  pwr=$(read_power_w "$PWR_AVG")
  pwr_cap=$(read_power_w "$PWR_CAP")

  busy=""
  if [ -f "$GPU_BUSY" ]; then
    busy=$(cat "$GPU_BUSY" 2>/dev/null)
  fi

  temp_color="$GREEN"
  if [ -n "$hot" ]; then
    hot_int=${hot%.*}
    if [ "$hot_int" -ge 100 ]; then
      temp_color="$RED"
    elif [ "$hot_int" -ge 90 ]; then
      temp_color="$YELLOW"
    fi
  fi

  throttle="OK"
  throttle_color="$GREEN"

  if [ -n "$hot" ]; then
    hot_int=${hot%.*}
    if [ "$hot_int" -ge 100 ]; then
      throttle="THERMAL"
      throttle_color="$RED"
    fi
  fi

  if [ "$throttle" = "OK" ] && [ -n "$pwr" ] && [ -n "$pwr_cap" ]; then
    if [ -f "$PWR_AVG" ] && [ -f "$PWR_CAP" ]; then
      raw_avg=$(cat "$PWR_AVG")
      raw_cap=$(cat "$PWR_CAP")
      near=$(( raw_cap * 95 / 100 ))
      if [ "$raw_avg" -ge "$near" ]; then
        throttle="PWR-LIMIT"
        throttle_color="$YELLOW"
      fi
    fi
  fi

  if [ "$throttle" = "OK" ] && [ -n "$cur_clk" ] && [ -n "$max_clk" ]; then
    delta=$(( max_clk - cur_clk ))
    if [ "$delta" -gt 100 ]; then
      throttle="POSSIBLE"
      throttle_color="$YELLOW"
    fi
  fi

  if [ -n "$cur_clk" ] && [ -n "$max_clk" ]; then
    echo -e "Clock:       ${BOLD}$cur_clk MHz${RESET} (max $max_clk MHz)"
  elif [ -n "$cur_clk" ]; then
    echo -e "Clock:       ${BOLD}$cur_clk MHz${RESET}"
  fi

  if [ -n "$busy" ]; then
    echo -e "GPU-Load:    ${BOLD}$busy %${RESET}"
  fi

  if [ -n "$edge" ]; then
    echo -e "Edge Temp:   $edge °C"
  fi

  if [ -n "$hot" ]; then
    echo -e "Hotspot:     ${temp_color}$hot °C${RESET}"
  fi

  if [ -n "$vram" ]; then
    echo -e "VRAM Temp:   $vram °C"
  fi

  if [ -n "$pwr" ]; then
    line="Power:       $pwr W"
    if [ -n "$pwr_cap" ]; then
      line="$line (Cap: $pwr_cap W)"
    fi
    echo -e "$line"
  fi

  echo
  echo -e "Throttle:    ${throttle_color}${BOLD}$throttle${RESET}"
  echo
  echo "Strg+C zum Beenden."

  # Rest des Bildschirms löschen (alte Zeilen weg)
  printf '\033[J'

  sleep 1
done
