# NIER Hardware Test Guide

This guide documents `src/robot/testing/hardware_test.cpp`.

Testing:
- 2x continuous servos for left/right tracks
- 1x 180 degree servo for sonar pan
- 2x sonars mounted on the pan servo
- LCD
- buzzer
- LEDs / matrix output path
- RGB LED (if mapped in your board profile)
- buttons
- serial (TX + optional RX)

## 1. Safety Before Running

1. Lift the robot so tracks are free (or place on a stand).
2. Keep fingers and cables away from wheels and servo horns.
3. Power the robot from a stable source.
4. Open serial monitor at `9600` baud if you want live logs.

## 2. File Location

- Sketch: `src/robot/testing/hardware_test.cpp`

## 3. What the Test Does (In Order)

1. LCD test
2. Left track servo: 1 second forward, 1 second backward
3. Right track servo: 1 second forward, 1 second backward
4. Top sonar pan servo: left -> center -> right -> center
5. Sonar test: reads both sonars while scanning angles 20/90/160
6. LED "matrix screen" phase test (3 sequential phases)
7. RGB LED color cycle (if RGB pins exist in the board profile)
8. Buzzer: rising then falling pitch sweep
9. Buttons test (`SW_N`, `SW_E`, `SW_S`, `SW_W`, `SW_C`)
10. Optional serial RX test: send `PING` within 8 seconds to get `PONG`
11. Summary on serial + LCD

After completion, pressing `SW_C` reruns the full suite.

## 4. Expected Successful Behavior

You should observe:

- LCD clearly changing messages during each stage.
- Left and right track servos moving separately (never both under the same test step).
- Top sonar servo rotating smoothly through left/center/right.
- Sonar values printed in serial logs.
- LED output flashing in 3 phases.
- RGB cycling red/green/blue/white/off (if RGB is available on your hardware profile).
- Buzzer audible rising and falling tones.
- Button presses registered before timeout.
- End summary like:
  - `PASS: <number>`
  - `FAIL: 0` (ideal)
  - `SKIP: <number>` (possible for optional/unmapped items)

## 5. Understanding PASS / FAIL / SKIP

- `PASS`: test stage executed and met criteria.
- `FAIL`: stage did not meet criteria (for example no sonar echo detected while scanning).
- `SKIP`: stage intentionally skipped because:
  - hardware profile has no RGB pin macros, or
  - a button pin is shared with a configured servo pin, or
  - optional serial RX `PING` was not sent.

## 6. Important Pin-Sharing Note

In this sketch, the top sonar servo is configured on pin `19`:
- `#define SONAR_PAN_SERVO_PIN 19`

On some Dwenguino mappings, `SW_W` is also pin `19`.
If that conflict exists in your hardware mapping, the `SW_W` button test is auto-skipped.

## 7. If You Want Stricter Sonar Verification

During the sonar stage, place a hand/object around `20-60 cm` in front of the robot.
That gives reliable non-zero readings and avoids false failures in empty space.

## 8. If You Have Custom External Matrix Wiring

`hardware_test.cpp` includes a 3-phase LED output sequence as matrix-screen validation flow.
If your 3 matrix displays use a custom driver, adapt `testLedMatrixScreens()` to your driver API and pin map.
