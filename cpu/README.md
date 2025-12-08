# CPU-X Prime Benchmark Automation

![bash](https://img.shields.io/badge/shell-bash-brightgreen?logo=gnu-bash&logoColor=white)
![cpu](https://img.shields.io/badge/benchmark-CPU--X-orange)
![status](https://img.shields.io/badge/status-experimental-blue)

Dieses Verzeichnis enthält ein paar Shell-Skripte, um den Prime-Zahl-Benchmark von [CPU‑X](https://github.com/TheTumultuousUnicornOfDarkness/CPU-X) nachzubilden und automatisiert zu messen (Single‑Core und All‑Core).

---

## Voraussetzungen

- Linux-System mit:
  - `/proc/cpuinfo`
  - `bash`
  - `taskset` (aus `util-linux`)
  - `nproc` (aus `coreutils`)
  - `bc`

---

## Dateien

- `primebench.sh`  
  Einfacher Prime-Benchmark (fast/slow) in Bash. Zählt Primzahlen bis eine bestimmte Zeit abgelaufen ist.

- `cpufreqs.sh`  
  Liest die CPU-Frequenz aus `/proc/cpuinfo` und führt eine laufende Auswertung:
  - `max.log` – maximale gemessene Frequenz (MHz)
  - `avg.log` – laufende Durchschnittsfrequenz (MHz)
  - `samples.log` – Anzahl der Samples  
  Läuft in einer Schleife und wird von der Automation als Hintergrundprozess gestartet.

- `primeautomation.sh`  
  Steuert die Messungen:
  - Single-Core-Lauf (ein Kern, `taskset -c 0`)
  - All-Core-Lauf (alle Kerne, je ein Prozess pro Kern mit `taskset`)
  - Startet/stoppt `cpufreqs.sh` während der Läufe
  - Schreibt Ergebnisse in `primeresults.csv`
  - Löscht am Ende alle `*.log`-Dateien im Verzeichnis

- `primeresults.csv`  
  Ergebnisdatei, wird automatisch angelegt/erweitert.

---

## Installation / Setup

Im Projektordner:

```bash
cd cpu-x-automation
chmod +x primebench.sh primeautomation.sh cpufreqs.sh
```

---

## CLI-Flags & Parameter

### `primebench.sh`

```bash
./primebench.sh [DURATION] [MODE]
```

- `DURATION` (optional)  
  - Typ: Sekunden (Integer)  
  - Standard: `60`
- `MODE` (optional)  
  - Werte: `fast` oder `slow`  
  - Standard: `fast`

Beispiele:

```bash
./primebench.sh           # 60 Sekunden, fast
./primebench.sh 10 fast   # 10 Sekunden, fast
./primebench.sh 30 slow   # 30 Sekunden, slow
```

Ausgabe (Beispiel):

```text
Mode       : fast
Duration   : 10s
Max number : 12345
Primes     : 789
```

### `primeautomation.sh`

```bash
./primeautomation.sh [-m NOTES] [DURATION]
```

- `DURATION` (optional)  
  - Typ: Sekunden (Integer)  
  - Standard: `60`  
  - Wird für Single‑Core- und All‑Core-Lauf gleichermaßen verwendet.
 - `-m NOTES` (optional)  
   - Freitext-Notiz, z. B. `TPU`, `test`, `default`  
   - Wird in der CSV-Spalte `notes` gespeichert (Standard: `default`)

Beispiel:

```bash
./primeautomation.sh -m TPU 60
```

Konsolenausgabe (vereinfacht):

```text
=== Starte Single-Core-Lauf (1 Kern, fast) ===
Single-Core Ergebnis: primes=... max_number=... max_freq=...MHz avg_freq=...MHz
=== Starte All-Core-Lauf (24 Kerne, fast) ===
All-Core Ergebnis: primes_total=... max_number=... max_freq=...MHz avg_freq=...MHz
Fertig. Ergebnisse in primeresults.csv gespeichert.
```

---

## CSV-Format

`primeresults.csv` hat (in der aktuellen Version) die Spalten:

```text
label,cores,duration_s,primes_total,max_number,max_freq_mhz,avg_freq_mhz,timestamp,notes
```

- `label` – `single` (Single-Core) oder `all` (All-Core)
- `cores` – Anzahl verwendeter Kerne
- `duration_s` – Laufzeit des Benchmarks in Sekunden
- `primes_total` – Anzahl gefundener Primzahlen
- `max_number` – höchste untersuchte Zahl im Lauf
- `max_freq_mhz` – maximale gemessene CPU-Frequenz (MHz)
- `avg_freq_mhz` – gemittelte CPU-Frequenz über alle Samples des Laufs (MHz)
- `timestamp` – Zeitpunkt, zu dem die Zeile geschrieben wurde (`YYYY-MM-DD HH:MM:SS`)
- `notes` – frei wählbare Notiz, z. B. `default`, `test`, `TPU`

Ältere Einträge ohne `avg_freq_mhz`/`notes` stammen aus früheren Versionen der Skripte und bleiben unverändert erhalten.
