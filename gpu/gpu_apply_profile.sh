#!/bin/bash
echo "s 1 2620" > /sys/class/drm/card1/device/pp_od_clk_voltage
echo "vo -70"  > /sys/class/drm/card1/device/pp_od_clk_voltage
echo "m 1 1075" > /sys/class/drm/card1/device/pp_od_clk_voltage
echo "c" > /sys/class/drm/card1/device/pp_od_clk_voltage
