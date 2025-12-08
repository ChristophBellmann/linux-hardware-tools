#!/usr/bin/env bash

set -euo pipefail

# Simple reimplementation of CPU-X prime benchmark in shell.
# It counts how many prime numbers are found within a given duration.
# Usage: ./cpu_x_prime_bench.sh [duration_seconds] [fast|slow]

duration="${1:-60}"   # default: 60 seconds
mode="${2:-fast}"     # default: fast mode

case "$mode" in
  fast|FAST) mode="fast" ;;
  slow|SLOW) mode="slow" ;;
  *)
    echo "Unknown mode: $mode" >&2
    echo "Usage: $0 [duration_seconds] [fast|slow]" >&2
    exit 1
    ;;
esac

start_ts=$(date +%s)
primes=0
number=1

is_prime_slow() {
  local n="$1"
  (( n < 2 )) && return 1
  local i
  for ((i = 2; i <= n; i++)); do
    if (( n % i == 0 )); then
      break
    fi
  done
  (( i == n ))
}

is_prime_fast() {
  local n="$1"
  (( n < 2 )) && return 1
  local i
  for ((i = 2; i * i <= n; i++)); do
    if (( n % i == 0 )); then
      return 1
    fi
  done
  return 0
}

while :; do
  now_ts=$(date +%s)
  elapsed=$((now_ts - start_ts))
  (( elapsed >= duration )) && break

  (( number++ ))

  if [[ "$mode" == "fast" ]]; then
    if is_prime_fast "$number"; then
      (( ++primes ))
    fi
  else
    if is_prime_slow "$number"; then
      (( ++primes ))
    fi
  fi
done

echo "Mode       : $mode"
echo "Duration   : ${duration}s"
echo "Max number : $number"
echo "Primes     : $primes"
