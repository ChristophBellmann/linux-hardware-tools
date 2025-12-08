# AMD GPU Power Limit – Kurzanleitung (Linux)

Diese Anleitung beschreibt, wie das Power-Limit einer AMD-GPU unter Linux erhöht wurde – basierend auf dem Tool **upp** (https://github.com/sibradzic/upp).

---

## 1. Installation von upp

`upp` wurde mit **pipx** installiert:

```bash
pipx install upp
```

`upp` wird dadurch unter `~/.local/bin/` abgelegt.

---

## 2. PowerPlay-Tabelle sichern und auslesen

Die GPU befindet sich unter:

```
/sys/class/drm/card1/device/pp_table
```

Backup der Original-Tabelle:

```bash
cat /sys/class/drm/card1/device/pp_table > pp_table_original.bin
```

Dekodierte Textversion erzeugen:

```bash
upp --pp-file=/sys/class/drm/card1/device/pp_table dump > pp_decoded.txt
```

---

## 3. Werte bearbeiten

Die Datei `pp_decoded.txt` wurde manuell geändert, u. a.:

- `smc_pptable/SocketPowerLimitAc/0` zb von 186 auf 210
- `smc_pptable/SocketPowerLimitDc/0`zb von 186 auf 210


Diese Werte steuern WattLimits.

---

## 4. Änderungen anwenden

Da `upp` über pipx installiert wurde, muss das User-PATH an sudo weitergegeben werden:

```bash
sudo -E env "PATH=$PATH" upp --pp-file=/sys/class/drm/card1/device/pp_table   undump -d pp_decoded.txt --write
```

- `undump -d pp_decoded.txt` → lädt die editierten Werte  
- `--write` → schreibt sie auf die GPU

Die neuen Limits sind sofort aktiv.

---

## 5. Überprüfen

```bash
sudo -E env "PATH=$PATH" upp --pp-file=/sys/class/drm/card1/device/pp_table   get smc_pptable/SocketPowerLimitAc/0 smc_pptable/SocketPowerLimitDc/0 smc_pptable/TdcLimit/0
```

---

## 6. Wiederherstellen (Restore)

```bash
sudo sh -c 'cat pp_table_original.bin > /sys/class/drm/card1/device/pp_table'
```

---

## 7. Optional: Automatisches Laden beim Booten

Das Repo enthält eine systemd-Unit (`upliftpowerplay@.service`), wurde hier aber **nicht** verwendet.

---

## Status

✓ PowerPlay-Tabelle erfolgreich erhöht  
✓ Änderungen aktiv ohne Neustart  
