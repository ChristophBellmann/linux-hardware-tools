#!/usr/bin/env bash

CARD="/sys/class/drm/card1/device"

echo "Setze RX 6700 XT auf MAX-Performance..."
echo

# --- GPU Clock: Erzwinge höchsten DPM-State ---
echo "2725MHz (DPM-State 2) setzen..."
echo "2" | sudo tee $CARD/pp_dpm_sclk > /dev/null
echo "2725MHz -> aktiv."

# --- SOC Clock: Maximalen SOC setzen ---
echo "SOC Clock auf 1200MHz setzen..."
echo "1" | sudo tee $CARD/pp_dpm_socclk > /dev/null
echo "1200MHz SOC aktiv."

# --- GPU Busy / Frequency Check ---
echo
echo "Aktuelle Werte:"
cat $CARD/pp_dpm_sclk | sed 's/^/  /'
cat $CARD/pp_dpm_socclk | sed 's/^/  /'

# --- Hinweis ---
echo
echo "Hinweis:"
echo "Die Karte läuft jetzt mit maximalem Boost-Profil."
echo "Beobachte 'gpu_watch.sh' für Power, Hotspot und Takt."
