# NIER Robot - Complete Build and Run Guide

This document is the single source of truth for building the robot, flashing firmware, running the desktop app, and understanding the protocol.
It is written to be enough to reproduce the full project without other files.

---

## 1. Repository Layout

Use these paths as your reference when reading or modifying the project.

- `src/desktop_app/` Python desktop app (GUI, LLM, emotions, serial, navigation).
- `src/robot/firmware/main.cpp` Robot firmware for Dwenguino.
- `src/robot/testing/hardware_test.cpp` Full staged hardware test sketch.
- `src/robot/testing/HARDWARE_TEST.md` Expected outcomes and troubleshooting for the hardware test.
- `src/robot/prototyping/` Older one-off experiments and prototype sketches.
- `src/robot/docs/documentation.md` This document.
- `requirements.txt` Python dependencies.
- `.hf_token` Hugging Face token (not committed).
- `logs/` Per-session logs (created at runtime).

---

## 2. Hardware Requirements

Minimum hardware used by this project.

- Dwenguino board (PIC18F4550 platform).
- 2x ultrasonic sonar sensors (HC-SR04 compatible).
- 2x 360 degree continuous rotation servos (drive).
- 1x 180 degree servo (sonar pan mount).
- LCD 16x2 display (on-board).
- LED matrix display(s), if installed.
- RGB LED, if installed.
- Buzzer (on-board).
- USB cable for serial and power.
- Power for motors if required (external if USB not enough).

---

## 3. Wiring and Pin Map

The firmware defines the pins used by the robot. Wire your hardware to match the firmware.

### 3.1 Sonar sensors (HC-SR04)

- Sonar 1 trigger: `A1`
- Sonar 1 echo: `A0`
- Sonar 2 trigger: `A3`
- Sonar 2 echo: `A2`

### 3.2 Servos

- Servo 1: pin `40`
- Servo 2: pin `41`
- Servo 3: pin `19`

### 3.3 Built-in peripherals

These are on-board and do not need wiring.

- LCD 16x2
- Buzzer
- Buttons (SW_N, SW_E, SW_S, SW_W, SW_C)

If you added external RGB or matrix hardware, use your project-specific wiring map.

---

## 4. Firmware Setup (Robot)

The firmware is in `src/robot/firmware/main.cpp`.

### 4.1 Flashing with Blockly (Dwengo)

1. Open `https://blockly.dwengo.org/`.
2. Import `src/robot/firmware/main.cpp`.
3. Press the RESET button and then the S button on the Dwenguino.
4. Release both buttons.
5. Click the "play" button in the website to flash.

### 4.2 Firmware behavior summary

- Listens to serial commands (see protocol below).
- Sends telemetry at a fixed interval.
- Updates LCD, LED matrix, RGB, and buzzer based on commands.
- Performs a soft reset when `RESET` is received.

### 4.3 Full hardware validation sketch

Use this before demo day or after rewiring:

- Flash `src/robot/testing/hardware_test.cpp`
- Follow `src/robot/testing/HARDWARE_TEST.md` for expected pass/fail behavior
- Press `SW_C` to rerun the full test suite

---

## 5. Desktop App Setup (Python)

The desktop app runs the UI, LLM, emotions, logging, and navigation.

### 5.1 Install dependencies

From the repo root:

```bash
python -m pip install -r requirements.txt
```

### 5.2 Run the app

```bash
python src/desktop_app/main.py
```

### 5.3 Connect to the robot

- Select the correct COM port.
- Click "Verbinden".

### 5.4 Debug features

Enable "Debug info tonen" to show these panels and fields.

- Antwoord (PC)
- LCD preview
- RX/TX debug
- Extra telemetry

### 5.5 Reset behavior

The Reset button always works:

- If offline: resets local state (UI, history, emotions).
- If online: resets local state and sends `RESET` to the robot.

---

## 6. LLM Setup (Hugging Face)

The desktop app uses a local Hugging Face model. The default is:

- `meta-llama/Llama-3.2-3B-Instruct`

### 6.1 Gated model access

The Llama models are gated. You must request access and authenticate.

1. Go to the model page and request access.
2. Put your HF token in `.hf_token` in the repo root.
3. Make sure `LLM_ALLOW_DOWNLOAD = True` in `src/desktop_app/config.py`.

`.hf_token` format:

```
hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 6.2 Change model

Edit `src/desktop_app/config.py`:

```python
LLM_MODEL_NAME = "meta-llama/Llama-3.2-3B-Instruct"
```

You can change to any Hugging Face model ID you have access to.

### 6.3 Length control

These values control response length:

- `LLM_MAX_NEW_TOKENS`
- `LLM_MIN_NEW_TOKENS`

Shorter responses: lower max, keep min small.

---

## 7. Serial Protocol (PC <-> Robot)

All commands are ASCII lines ending with `\n`.

### 7.1 PC -> Robot

- `HELLO`
- `PING`
- `STOP`
- `RESET`
- `MOVE:<left>,<right>` where each is `-255..255`
- `LCD:<text>` max about 128 chars (truncated)
- `EMO:<h>,<fat>,<hun>,<sad>,<anx>,<aff>,<cur>,<fru>` each 0..100

### 7.2 Robot -> PC

- `READY`
- `PONG`
- `ACK:<command>`
- `ACK:RESET`
- `STAT:<sonarL>,<sonarR>,<closest>,<battery>,<mode>`
- `OUT:<r>,<g>,<b>,<buzzer>,<matrix>,<lcd>`
- `EMO:<h>,<fat>,<hun>,<sad>,<anx>,<aff>,<cur>,<fru>`

---

## 8. Navigation Logic (Desktop App)

The navigation is computed on the PC using sonar readings from the robot.

- If closest distance <= 20 cm: avoid by turning away.
- If closest distance <= 60 cm: approach with a small correction.
- Otherwise: search mode (random forward/turn).

The PC sends `MOVE` commands to the robot with low speed values.

---

## 9. Emotions System

The desktop app computes emotions based on:

- Recent conversation context
- Sentiment score

Outputs:

- 8 emotion percentages (0..100)
- Dominant emotion used for LED matrix and RGB

---

## 10. Logging

Each session creates a log file in `logs/`:

- `session_YYYYMMDD_HHMMSS.log`

Log categories:

- `APP_START`, `APP_STOP`
- `USER_MSG`, `ROBOT_MSG`
- `TX`, `RX`
- `CONNECT_OK`, `CONNECT_FAIL`, `DISCONNECT`
- `SERIAL_ERR`
- `RESET`
- `LLM` and error details

---

## 11. Troubleshooting

### 11.1 No serial connection

- Check COM port.
- Make sure no other app is using the port.
- Verify the USB cable supports data, not just power.

### 11.2 LLM says offline or gated

- Make sure you have access to the model on Hugging Face.
- Add a valid token to `.hf_token`.
- Set `LLM_ALLOW_DOWNLOAD = True`.

### 11.3 Very slow responses

- The model may be too large for CPU-only.
- Use a smaller model (1B) or reduce `LLM_MAX_NEW_TOKENS`.

### 11.4 LCD is blank

- Check firmware flashed correctly.
- Make sure the LCD is initialized by `initDwenguino()`.

---

## 12. Safety Notes

- Use low speed values for `MOVE` on a desk.
- Avoid running motors without enough power.
- Keep sonar sensors unobstructed.

---

## 13. Minimal Firmware Template

```cpp
#include <Dwenguino.h>

void setup() {
  initDwenguino();
}

void loop() {
}
```

---
