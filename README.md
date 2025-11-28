# Lüfter- & Pumpensteuerung (nct6798 / hwmon2)

Dieses Verzeichnis enthält kleine Hilfsskripte, um unter Linux die
Mainboard-Lüfter und die Wasserpumpe (über den `nct6798`-Sensor,
`/sys/class/hwmon/hwmon2`) zu **anzeigen** und **manuell zu steuern**.

> ACHTUNG  
> Falsche Einstellungen können zu zu hohen Temperaturen führen.  
> Pumpe im Zweifel immer eher zu schnell als zu langsam laufen lassen.

## Übersicht der Skripte

- `status_pumpen_drehzahl.sh`  
  Zeigt aktuelle Drehzahlen und PWM-Werte für `nct6798`:
  - alle `fan*_input` (RPM)
  - alle `pwm*` + `pwm*_enable`
  - Nur Lesezugriff – **kein sudo nötig**.

- `test_pumpen_drehzahl.sh`  
  Testet einen PWM-Kanal in Stufen und zeigt dazu die Drehzahlen.
  - **Benötigt sudo**, da auf `/sys/class/hwmon/.../pwm*` geschrieben wird.
  - Standard-Kanal: `pwm2` (beim Aufruf änderbar).
  - Fährt mehrere PWM-Werte (z.B. 80 → 128 → 180 → 230 → 255 → …) und zeigt
    jeweils die aktuellen RPM.
  - Am Ende Hinweis, wie man den Kanal wieder auf Auto (`pwmX_enable = 2`) setzt.

- `fan_pump_control_tui.py`  
  Einfaches curses-TUI zur “Live”-Steuerung per Tastatur:
  - Zeigt für Kanäle `pwm1`, `pwm2`, `pwm5` jeweils:
    - PWM-Wert (0–255)
    - Modus (`AUTO` / `MANUAL`)
    - Drehzahl (`fan*_input` in RPM)
  - Anzeige wird etwa einmal pro Sekunde aktualisiert.
  - Tasten:
    - `TAB` / `Shift+Tab`: Kanal wechseln
    - `←` / `-`: PWM leicht herunter
    - `→` / `+` / `=`: PWM leicht erhöhen
    - `↑`: PWM grob erhöhen
    - `↓`: PWM grob senken
    - `a`: Auto/Manuell für aktuellen Kanal umschalten
    - `q`: Beenden
  - Oben wird angezeigt, ob das Programm als **root** läuft:
    - nur als root werden PWM-/Mode-Änderungen tatsächlich nach `/sys` geschrieben.

## Typische Aufrufe

Im Verzeichnis arbeiten:

```bash
cd ~/Nextcloud/Documents/Produktion/luefter_pumpe
```

### Status anzeigen (ohne Eingriff)

```bash
./status_pumpen_drehzahl.sh
```

### Einzelnen Kanal in Stufen testen

Beispiel für `pwm2`:

```bash
sudo ./test_pumpen_drehzahl.sh 2
```

Beispiel für `pwm5` (falls das die Pumpe ist):

```bash
sudo ./test_pumpen_drehzahl.sh 5
```

### Interaktive Steuerung (TUI)

```bash
sudo ./fan_pump_control_tui.py
```

Dann mit `TAB` den gewünschten Kanal auswählen und mit den Pfeiltasten
oder `-` / `+` den PWM-Wert ändern.  
Mit `a` zwischen Auto/Manuell umschalten, mit `q` beenden.

## Hinweise zur Zuordnung (pwmX ↔ Lüfter/Pumpe)

Welche Nummer zu welchem physikalischen Anschluss gehört, hängt vom
Mainboard ab. Vorgehen:

1. `./status_pumpen_drehzahl.sh` aufrufen und RPM-Werte notieren.
2. `sudo ./test_pumpen_drehzahl.sh <kanal>` für einen Kanal starten.
3. Beobachten, welcher Lüfter sich hörbar / in den RPM-Werten verändert.
4. Kanal, der zur Pumpe gehört, gut merken und später im TUI vorsichtig verwenden.

Im Zweifel lieber im BIOS/Handbuch nachsehen, wie die Fan-Header
bezeichnet und verschaltet sind.

