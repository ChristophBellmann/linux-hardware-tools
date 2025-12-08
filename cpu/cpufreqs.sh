#!/bin/bash

LOGFILE="max.log"
AVGFILE="avg.log"
COUNTFILE="samples.log"

[ -f "$LOGFILE" ]  || echo 0 > "$LOGFILE"
[ -f "$AVGFILE" ]  || echo 0 > "$AVGFILE"
[ -f "$COUNTFILE" ] || echo 0 > "$COUNTFILE"

while true; do
    current=$(grep "cpu MHz" /proc/cpuinfo | awk '{print $4}' | sort -nr | head -1)
    max=$(cat "$LOGFILE")
    avg=$(cat "$AVGFILE")
    count=$(cat "$COUNTFILE")

    if (( $(echo "$current > $max" | bc -l) )); then
        echo "$current" > "$LOGFILE"
        echo "Neues Maximum: $current MHz"
        max="$current"
    fi

    new_count=$((count + 1))
    new_avg=$(echo "scale=3; ($avg * $count + $current) / $new_count" | bc -l)
    echo "$new_avg"   > "$AVGFILE"
    echo "$new_count" > "$COUNTFILE"

    echo "Aktuell: $current MHz | Maximum: $max MHz | Durchschnitt: $new_avg MHz"
    sleep 1
done
