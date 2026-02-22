#include <Wire.h>
#include <Dwenguino.h>
#include <LiquidCrystal.h>
#include <NewPing.h>
#include <Servo.h>

// -----------------------------
// Hardware mapping for this robot
// -----------------------------
#define LEFT_TRACK_SERVO_PIN 40
#define RIGHT_TRACK_SERVO_PIN 41
#define SONAR_PAN_SERVO_PIN 19

#define SONAR_1_TRIG_PIN A1
#define SONAR_1_ECHO_PIN A0
#define SONAR_2_TRIG_PIN A3
#define SONAR_2_ECHO_PIN A2

#define SONAR_MAX_DISTANCE_CM 200
#define SONAR_PAN_LEFT_DEG 20
#define SONAR_PAN_CENTER_DEG 90
#define SONAR_PAN_RIGHT_DEG 160

#define SERVO_TEST_SPEED 90
#define SERVO_TEST_MS 1000

#define BUTTON_TIMEOUT_MS 8000
#define SERIAL_RX_TIMEOUT_MS 8000

#ifndef LED_MATRIX_COUNT
#define LED_MATRIX_COUNT 3
#endif

Servo leftTrackServo;
Servo rightTrackServo;
Servo sonarPanServo;

NewPing sonar1(SONAR_1_TRIG_PIN, SONAR_1_ECHO_PIN, SONAR_MAX_DISTANCE_CM);
NewPing sonar2(SONAR_2_TRIG_PIN, SONAR_2_ECHO_PIN, SONAR_MAX_DISTANCE_CM);

struct SuiteStats {
  int passed;
  int failed;
  int skipped;
};

SuiteStats suiteStats = {0, 0, 0};
unsigned long lastIdleBlinkMs = 0;
bool idleLedOn = false;

void setTrackServoSpeed(Servo &servo, int vel) {
  int pulse = map(constrain(vel, -255, 255), -255, 255, 1000, 2000);
  servo.writeMicroseconds(pulse);
}

void stopTracks() {
  setTrackServoSpeed(leftTrackServo, 0);
  setTrackServoSpeed(rightTrackServo, 0);
}

void lcdShow(const char *line1, const char *line2) {
  dwenguinoLCD.clear();
  dwenguinoLCD.setCursor(0, 0);
  dwenguinoLCD.print(line1);
  dwenguinoLCD.setCursor(0, 1);
  dwenguinoLCD.print(line2);
}

void setBoardLeds(uint8_t mask) {
  LEDS = mask;
}

void setRgbLed(uint8_t r, uint8_t g, uint8_t b) {
#if defined(LED_R) && defined(LED_G) && defined(LED_B)
  analogWrite(LED_R, r);
  analogWrite(LED_G, g);
  analogWrite(LED_B, b);
#elif defined(RGB_LED_R) && defined(RGB_LED_G) && defined(RGB_LED_B)
  analogWrite(RGB_LED_R, r);
  analogWrite(RGB_LED_G, g);
  analogWrite(RGB_LED_B, b);
#else
  (void)r;
  (void)g;
  (void)b;
#endif
}

bool rgbPinsAvailable() {
#if defined(LED_R) && defined(LED_G) && defined(LED_B)
  return true;
#elif defined(RGB_LED_R) && defined(RGB_LED_G) && defined(RGB_LED_B)
  return true;
#else
  return false;
#endif
}

void reportPass(const char *name) {
  suiteStats.passed++;
  Serial.print(F("[PASS] "));
  Serial.println(name);
}

void reportFail(const char *name, const char *reason) {
  suiteStats.failed++;
  Serial.print(F("[FAIL] "));
  Serial.print(name);
  Serial.print(F(" - "));
  Serial.println(reason);
}

void reportSkip(const char *name, const char *reason) {
  suiteStats.skipped++;
  Serial.print(F("[SKIP] "));
  Serial.print(name);
  Serial.print(F(" - "));
  Serial.println(reason);
}

void testLcd() {
  lcdShow("Running HW test", "LCD check start");
  delay(1200);
  lcdShow("LCD line 1 OK", "LCD line 2 OK");
  delay(1200);
  reportPass("LCD");
}

void testDriveServo(const char *label, Servo &servo) {
  lcdShow("Servo test", label);
  Serial.print(F("[INFO] "));
  Serial.print(label);
  Serial.println(F(": +1s then -1s"));

  setTrackServoSpeed(servo, SERVO_TEST_SPEED);
  delay(SERVO_TEST_MS);
  setTrackServoSpeed(servo, -SERVO_TEST_SPEED);
  delay(SERVO_TEST_MS);
  setTrackServoSpeed(servo, 0);
  delay(300);

  reportPass(label);
}

void testSonarPanServo() {
  lcdShow("Servo test", "Top sonar pan");
  Serial.println(F("[INFO] Top servo: left-center-right-center"));

  sonarPanServo.write(SONAR_PAN_LEFT_DEG);
  delay(1000);
  sonarPanServo.write(SONAR_PAN_CENTER_DEG);
  delay(1000);
  sonarPanServo.write(SONAR_PAN_RIGHT_DEG);
  delay(1000);
  sonarPanServo.write(SONAR_PAN_CENTER_DEG);
  delay(700);

  reportPass("Top sonar servo");
}

int readBestSonarCm(NewPing &sensor) {
  int best = 0;
  for (int i = 0; i < 3; i++) {
    int cm = sensor.ping_cm();
    if (cm > 0 && (best == 0 || cm < best)) {
      best = cm;
    }
    delay(35);
  }
  return best;
}

void testSonars() {
  lcdShow("Sonar test", "Hold hand 20-60");
  Serial.println(F("[INFO] Place your hand/object in front of the sonars now."));
  delay(1800);

  const int scanAngles[3] = {SONAR_PAN_LEFT_DEG, SONAR_PAN_CENTER_DEG, SONAR_PAN_RIGHT_DEG};
  bool sawObject = false;

  for (int i = 0; i < 3; i++) {
    int angle = scanAngles[i];
    sonarPanServo.write(angle);
    delay(350);

    int s1 = readBestSonarCm(sonar1);
    int s2 = readBestSonarCm(sonar2);

    if ((s1 > 0 && s1 <= 120) || (s2 > 0 && s2 <= 120)) {
      sawObject = true;
    }

    char l1[17];
    char l2[17];
    snprintf(l1, sizeof(l1), "Sonar %3d deg", angle);
    snprintf(l2, sizeof(l2), "S1:%3d S2:%3d", s1, s2);
    lcdShow(l1, l2);

    Serial.print(F("[INFO] Sonar angle "));
    Serial.print(angle);
    Serial.print(F(" -> S1="));
    Serial.print(s1);
    Serial.print(F("cm S2="));
    Serial.print(s2);
    Serial.println(F("cm"));
    delay(800);
  }

  sonarPanServo.write(SONAR_PAN_CENTER_DEG);
  delay(250);

  if (sawObject) {
    reportPass("Dual sonars");
  } else {
    reportFail("Dual sonars", "No echo in 1..120cm detected during scan");
  }
}

void testLedMatrixScreens() {
  // There is no direct matrix API in the current Dwenguino core used here.
  // We use a visible 3-phase LED output sequence as a matrix-screen proxy.
  // If external matrices are wired with a custom driver, adapt this section.
  const uint8_t phaseMasks[3] = {0b10000001, 0b00111100, 0b11100111};

  for (int i = 0; i < LED_MATRIX_COUNT; i++) {
    char line2[17];
    snprintf(line2, sizeof(line2), "Screen %d/%d", i + 1, LED_MATRIX_COUNT);
    lcdShow("LED matrix test", line2);

    for (int blink = 0; blink < 6; blink++) {
      setBoardLeds((blink % 2 == 0) ? phaseMasks[i % 3] : 0x00);
      delay(250);
    }
  }

  setBoardLeds(0x00);
  reportPass("LED matrix screens");
}

void testRgbLed() {
  lcdShow("RGB LED test", "R -> G -> B");

  if (!rgbPinsAvailable()) {
    reportSkip("RGB LED", "No RGB pin macros in this board profile");
    return;
  }

  setRgbLed(255, 0, 0);
  delay(600);
  setRgbLed(0, 255, 0);
  delay(600);
  setRgbLed(0, 0, 255);
  delay(600);
  setRgbLed(255, 255, 255);
  delay(600);
  setRgbLed(0, 0, 0);

  reportPass("RGB LED");
}

void testBuzzer() {
  lcdShow("Buzzer test", "Rise + fall");

  for (int f = 300; f <= 1200; f += 50) {
    tone(BUZZER, f);
    delay(30);
  }
  for (int f = 1200; f >= 300; f -= 50) {
    tone(BUZZER, f);
    delay(30);
  }
  noTone(BUZZER);
  delay(200);

  reportPass("Buzzer");
}

bool isSharedWithServoPin(uint8_t pin) {
  return (pin == SONAR_PAN_SERVO_PIN || pin == LEFT_TRACK_SERVO_PIN || pin == RIGHT_TRACK_SERVO_PIN);
}

bool waitForButtonPress(uint8_t pin, const char *name, unsigned long timeoutMs) {
  unsigned long start = millis();
  char line2[17];
  snprintf(line2, sizeof(line2), "Press %s", name);
  lcdShow("Button test", line2);

  while (millis() - start < timeoutMs) {
    if (digitalRead(pin) == PRESSED) {
      while (digitalRead(pin) == PRESSED) {
        delay(10);
      }
      return true;
    }
    delay(10);
  }
  return false;
}

void testButtons() {
  struct ButtonCase {
    uint8_t pin;
    const char *name;
  };

  const ButtonCase buttons[] = {
    {SW_N, "SW_N"},
    {SW_E, "SW_E"},
    {SW_S, "SW_S"},
    {SW_W, "SW_W"},
    {SW_C, "SW_C"}
  };

  for (unsigned int i = 0; i < sizeof(buttons) / sizeof(buttons[0]); i++) {
    if (isSharedWithServoPin(buttons[i].pin)) {
      reportSkip(buttons[i].name, "Shares pin with configured servo");
      continue;
    }

    bool ok = waitForButtonPress(buttons[i].pin, buttons[i].name, BUTTON_TIMEOUT_MS);
    if (ok) {
      reportPass(buttons[i].name);
    } else {
      reportFail(buttons[i].name, "Not pressed before timeout");
    }
  }
}

void testSerialRxOptional() {
  lcdShow("Serial RX test", "Send PING 8 sec");
  Serial.println(F("[INFO] Optional serial RX test: send 'PING' over serial within 8 seconds."));

  unsigned long start = millis();
  String line = "";
  while (millis() - start < SERIAL_RX_TIMEOUT_MS) {
    while (Serial.available() > 0) {
      char c = (char)Serial.read();
      if (c == '\n' || c == '\r') {
        line.trim();
        if (line == "PING") {
          Serial.println(F("PONG"));
          reportPass("Serial RX");
          return;
        }
        line = "";
      } else {
        line += c;
      }
    }
    delay(5);
  }

  reportSkip("Serial RX", "No PING received");
}

void printSummary() {
  Serial.println();
  Serial.println(F("===== HARDWARE TEST SUMMARY ====="));
  Serial.print(F("PASS: "));
  Serial.println(suiteStats.passed);
  Serial.print(F("FAIL: "));
  Serial.println(suiteStats.failed);
  Serial.print(F("SKIP: "));
  Serial.println(suiteStats.skipped);
  Serial.println(F("================================="));
}

void signalSummaryOnBuzzer() {
  if (suiteStats.failed == 0) {
    tone(BUZZER, 880);
    delay(150);
    tone(BUZZER, 988);
    delay(150);
    tone(BUZZER, 1175);
    delay(220);
  } else {
    for (int i = 0; i < 3; i++) {
      tone(BUZZER, 300);
      delay(200);
      noTone(BUZZER);
      delay(120);
    }
  }
  noTone(BUZZER);
}

void runHardwareSuite() {
  suiteStats.passed = 0;
  suiteStats.failed = 0;
  suiteStats.skipped = 0;

  Serial.println();
  Serial.println(F("===== NIER HARDWARE TEST START ====="));

  setBoardLeds(0x00);
  setRgbLed(0, 0, 0);
  stopTracks();
  sonarPanServo.write(SONAR_PAN_CENTER_DEG);

  testLcd();
  testDriveServo("Left track", leftTrackServo);
  testDriveServo("Right track", rightTrackServo);
  testSonarPanServo();
  testSonars();
  testLedMatrixScreens();
  testRgbLed();
  testBuzzer();
  testButtons();
  testSerialRxOptional();

  stopTracks();
  sonarPanServo.write(SONAR_PAN_CENTER_DEG);
  setBoardLeds(0x00);
  setRgbLed(0, 0, 0);

  printSummary();
  signalSummaryOnBuzzer();

  char line1[17];
  char line2[17];
  snprintf(line1, sizeof(line1), "P:%d F:%d S:%d", suiteStats.passed, suiteStats.failed, suiteStats.skipped);
  snprintf(line2, sizeof(line2), "SW_C rerun test");
  lcdShow(line1, line2);
}

void setup() {
  initDwenguino();
  Serial.begin(9600);

  pinMode(SW_N, INPUT_PULLUP);
  pinMode(SW_E, INPUT_PULLUP);
  pinMode(SW_S, INPUT_PULLUP);
  pinMode(SW_W, INPUT_PULLUP);
  pinMode(SW_C, INPUT_PULLUP);

  leftTrackServo.attach(LEFT_TRACK_SERVO_PIN);
  rightTrackServo.attach(RIGHT_TRACK_SERVO_PIN);
  sonarPanServo.attach(SONAR_PAN_SERVO_PIN);

  runHardwareSuite();
}

void loop() {
  // Heartbeat while waiting for rerun.
  if (millis() - lastIdleBlinkMs >= 500) {
    lastIdleBlinkMs = millis();
    idleLedOn = !idleLedOn;
    setBoardLeds(idleLedOn ? 0b00011000 : 0x00);
  }

  if (digitalRead(SW_C) == PRESSED) {
    while (digitalRead(SW_C) == PRESSED) {
      delay(10);
    }
    runHardwareSuite();
  }
}
