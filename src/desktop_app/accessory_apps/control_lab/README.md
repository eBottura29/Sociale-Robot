# Control Lab (Desktop)

Interactive hardware testing app for NIER that uses the same serial protocol as the main firmware.

## Run

From project root:

```bash
python src/desktop_app/accessory_apps/control_lab/control_lab_app.py
```

## Features

- WASD movement (only when motion switch is enabled)
- Emotion selector + intensity sender (`EMO:`)
- Eyebrow angle controls (`BROW:`)
- Top sonar servo auto/manual + manual angle (`PAN:`)
- RGB control (`RGB:`)
- Buzzer on/off + pitch (`BUZZER:`)
- LCD text sender (`LCD:`)
- Live telemetry view (`STAT`, `OUT`, `ACT`, `BROW`, `EMO`)

## Keybinds

Keybinds are loaded from:

- `src/desktop_app/accessory_apps/control_lab/keybinds.json`

Edit this file to customize shortcuts.
