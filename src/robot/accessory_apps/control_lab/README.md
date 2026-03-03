# Control Lab (Robot Side)

This folder documents the Control Lab tester protocol used by:

- `src/desktop_app/accessory_apps/control_lab/control_lab_app.py`
- `src/robot/accessory_apps/control_lab/control_lab.cpp`

The Control Lab desktop tester communicates with:

- `src/robot/firmware/main.cpp`
- `src/robot/accessory_apps/control_lab/control_lab.cpp` (includes firmware `main.cpp`)

It uses existing commands plus these additions:

- `BROW:<left>,<right>`
- `PAN:AUTO`
- `PAN:MANUAL`
- `PAN:<angle>`
- `RGB:<r>,<g>,<b>`
- `BUZZER:ON,<pitch>`
- `BUZZER:OFF`

Additional telemetry emitted by firmware:

- `BROW:<left>,<right>`
- `ACT:<panMode>,<panAngle>,<buzzerOn>,<buzzerPitch>`
