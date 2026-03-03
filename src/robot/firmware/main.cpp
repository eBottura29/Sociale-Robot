#include <Wire.h>
#include <Dwenguino.h>
#include <LiquidCrystal.h>
#include <NewPing.h>
#include <Servo.h>
#include <LedController.hpp>

// --- Dwenguino simulator compatibility shims ---
// Use LedController to drive 4 LED matrix segments; choose one fixed segment for emotion output.
LedController<4, 1> led_matrix;
#define LED_MATRIX_SEGMENT_INDEX 2  // 0..3

static inline void compatInitLedMatrix() {
  auto conf = controller_configuration<4, 1>();
  conf.useHardwareSpi = false;
  conf.SPI_CLK = 13;
  conf.SPI_MOSI = 2;
  conf.SPI_CS = 10;
  led_matrix.init(conf);
  led_matrix.activateAllSegments();
  led_matrix.setIntensity(8);
  led_matrix.clearMatrix();
}

static inline void compatClearLedMatrix() {
  led_matrix.clearMatrix();
}

static inline void compatSetRGBLed(int r, int g, int b) {
  // Dwenguino RGB LED pins are fixed in hardware.
  analogWrite(11, constrain(r, 0, 255));  // Red
  analogWrite(14, constrain(g, 0, 255));  // Green
  analogWrite(15, constrain(b, 0, 255));  // Blue
}

// Serieel protocol (regels, ASCII, newline)
// PC -> Robot
// - HELLO
// - PING
// - STOP
// - RESET                              software reset (state reset)
// - SONAR:ON / SONAR:OFF               sonar sensors + pan servo enable/disable
// - MOVE:<left>,<right>                 left/right = -255..255
// - LCD:<text>                          tekst op LCD
// - EMO:<h>,<fat>,<hun>,<sad>,<anx>,<aff>,<cur>,<fru>   0..100
// - BROW:<leftAngle>,<rightAngle>       0..180
// - PAN:AUTO / PAN:MANUAL               sonar pan servo mode
// - PAN:<angle>                          set pan angle in MANUAL mode
// - RGB:<r>,<g>,<b>                      0..255
// - BUZZER:ON,<pitch> / BUZZER:OFF       pitch in Hz (100..5000)
//
// Robot -> PC
// - READY
// - PONG
// - ACK:<command>
// - ACK:RESET
// - STAT:<sonarL>,<sonarR>,<closest>,<battery>,<mode>  mode=STOP/CMD/MANUAL/AVOID/APPROACH/SEARCH/SONAR_OFF
// - OUT:<r>,<g>,<b>,<buzzer>,<matrix>,<lcd>
// - ACT:<panMode>,<panAngle>,<buzzerOn>,<buzzerPitch>
// - BROW:<leftAngle>,<rightAngle>
// - EMO:<h>,<fat>,<hun>,<sad>,<anx>,<aff>,<cur>,<fru>

// Keep these in sync with src/settings/settings.json (robot.pins / robot.* defaults).
// RGB LED is fixed by Dwenguino hardware: R=11, G=14, B=15.
#define DRIVE_LEFT_PIN 41
#define DRIVE_RIGHT_PIN 40
#define SONAR_PAN_PIN 19
#define EYEBROW_LEFT_PIN 18
#define EYEBROW_RIGHT_PIN 17
#define ECHO_PIN_A0 A0
#define ECHO_PIN_A2 A2
#define TRIGGER_PIN_A1 A1
#define TRIGGER_PIN_A3 A3
#define MAX_DISTANCE 200
#define MAX_VEL 50
#define SONAR_FAR_CM (MAX_DISTANCE + 1)
#define TELEMETRY_INTERVAL_MS 250
#define CMD_TIMEOUT_MS 1000
#define LCD_SCROLL_INTERVAL_MS 450
#define SONAR_SCAN_SETTLE_MS 140
#define SONAR_PAN_STEP_DEG 2
#define SONAR_PAN_STEP_INTERVAL_MS 20
#define NAV_AVOID_THRESHOLD_CM 20
#define NAV_APPROACH_THRESHOLD_CM 60
#define NAV_AVOID_SPEED 40
#define NAV_APPROACH_SLOW 25
#define NAV_APPROACH_FAST 45
#define NAV_SEARCH_FORWARD_SPEED 35
#define NAV_SEARCH_TURN_SPEED 30
#define NAV_SEARCH_FORWARD_MS 1200
#define NAV_SEARCH_TURN_MS 800
#define BUZZER_MIN_PITCH 100
#define BUZZER_MAX_PITCH 5000

const int EMO_COUNT = 8;
const char *EMO_NAMES[EMO_COUNT] = {
  "HAPPINESS",
  "FATIGUE",
  "HUNGER",
  "SADNESS",
  "ANXIETY",
  "AFFECTION",
  "CURIOSITY",
  "FRUSTRATION"
};

const int INPUT_BUFFER_SIZE = 192;
const int LCD_TEXT_MAX = 128;
char inputBuffer[INPUT_BUFFER_SIZE];
int inputPos = 0;

int cmdLeft = 0;
int cmdRight = 0;
bool cmdActive = false;
bool stopLatch = false;
unsigned long lastCmdMs = 0;
unsigned long lastTelemetryMs = 0;
const char *currentNavMode = "STOP";

const int SONAR_SCAN_POINTS = 3;
const int SONAR_SCAN_ANGLES[SONAR_SCAN_POINTS] = {20, 90, 160};  // left, center, right
int sonarScanBySector[SONAR_SCAN_POINTS] = {SONAR_FAR_CM, SONAR_FAR_CM, SONAR_FAR_CM};
int sonarScanIndex = 0;
bool sonarEnabled = true;
bool sonarPanWaiting = false;
unsigned long sonarPanMovedAtMs = 0;
unsigned long sonarPanLastStepMs = 0;
int sonarPanCurrentAngle = SONAR_SCAN_ANGLES[1];
int sonarPanTargetAngle = SONAR_SCAN_ANGLES[1];
bool sonarPanAutoMode = true;
unsigned long navSearchUntilMs = 0;
int navSearchLeft = 0;
int navSearchRight = 0;

int currentEmo[EMO_COUNT] = {0};
int currentRgb[3] = {0, 0, 0};
bool currentBuzzerOn = false;
int currentBuzzerPitch = 880;
int currentMatrixIndex = 0;
char currentLcdText[LCD_TEXT_MAX + 1] = " ";
unsigned long lastLcdScrollMs = 0;
int lcdScrollIndex = 0;
int lcdScrollLength = 0;
int eyebrowLeftAngle = 90;
int eyebrowRightAngle = 90;

const byte MATRIX_PATTERNS[EMO_COUNT][8] = {
  {0b00000000, 0b01000010, 0b10100101, 0b10000001, 0b10100101, 0b10011001, 0b01000010, 0b00111100}, // HAPPINESS
  {0b00000000, 0b11000011, 0b10100101, 0b10000001, 0b10100101, 0b10000001, 0b01000010, 0b00111100}, // FATIGUE
  {0b00011000, 0b00111100, 0b01111110, 0b11111111, 0b11111111, 0b01111110, 0b00111100, 0b00011000}, // HUNGER
  {0b00000000, 0b01000010, 0b10100101, 0b10000001, 0b10011001, 0b10100101, 0b01000010, 0b00111100}, // SADNESS
  {0b00111100, 0b01000010, 0b10100101, 0b10011001, 0b10000001, 0b10100101, 0b01000010, 0b00111100}, // ANXIETY
  {0b00000000, 0b01000010, 0b10100101, 0b10011001, 0b10011001, 0b10100101, 0b01000010, 0b00111100}, // AFFECTION
  {0b00011000, 0b00100100, 0b01000010, 0b10100101, 0b10000001, 0b01000010, 0b00100100, 0b00011000}, // CURIOSITY
  {0b11111111, 0b10000001, 0b10111101, 0b10100101, 0b10100101, 0b10111101, 0b10000001, 0b11111111}  // FRUSTRATION
};
const int EYEBROW_ANGLES[EMO_COUNT][2] = {
  {120, 60},   // HAPPINESS
  {75, 105},   // FATIGUE
  {85, 95},    // HUNGER
  {65, 115},   // SADNESS
  {140, 40},   // ANXIETY
  {110, 70},   // AFFECTION
  {130, 50},   // CURIOSITY
  {45, 135}    // FRUSTRATION
};

NewPing sonarA1A0(TRIGGER_PIN_A1, ECHO_PIN_A0, MAX_DISTANCE);
NewPing sonarA3A2(TRIGGER_PIN_A3, ECHO_PIN_A2, MAX_DISTANCE);

int sonar1;
int sonar2;
int closest;

Servo servo1;  // pin 41: cont. servo (left)
Servo servo2;  // pin 40: cont. servo (right)
Servo servo3;  // pin 19: 180° servo
Servo servo4;  // pin 18: eyebrow left
Servo servo5;  // pin 17: eyebrow right

void setEyebrowAngles(int leftAngle, int rightAngle) {
  eyebrowLeftAngle = constrain(leftAngle, 0, 180);
  eyebrowRightAngle = constrain(rightAngle, 0, 180);
  if (servo4.attached()) {
    servo4.write(eyebrowLeftAngle);
  }
  if (servo5.attached()) {
    servo5.write(eyebrowRightAngle);
  }
}

void setPanAutoMode(bool enabled) {
  sonarPanAutoMode = enabled;
  if (sonarPanAutoMode) {
    sonarPanTargetAngle = SONAR_SCAN_ANGLES[1];
    sonarPanWaiting = false;
  } else {
    sonarPanWaiting = false;
    sonarPanLastStepMs = 0;
    if (servo3.attached()) {
      servo3.write(sonarPanCurrentAngle);
    }
  }
}

void setPanManualAngle(int angle) {
  sonarPanCurrentAngle = constrain(angle, 0, 180);
  sonarPanTargetAngle = sonarPanCurrentAngle;
  setPanAutoMode(false);
  if (servo3.attached()) {
    servo3.write(sonarPanCurrentAngle);
  }
}

void setRgbOutput(int r, int g, int b) {
  currentRgb[0] = constrain(r, 0, 255);
  currentRgb[1] = constrain(g, 0, 255);
  currentRgb[2] = constrain(b, 0, 255);
  compatSetRGBLed(currentRgb[0], currentRgb[1], currentRgb[2]);
}

void setBuzzerOutput(bool enabled, int pitch) {
  currentBuzzerPitch = constrain(pitch, BUZZER_MIN_PITCH, BUZZER_MAX_PITCH);
  currentBuzzerOn = enabled;
  if (currentBuzzerOn) {
    tone(BUZZER, currentBuzzerPitch);
  } else {
    noTone(BUZZER);
  }
}

void updateLCD(String str) {
  dwenguinoLCD.clear();
  String trimmed = str;
  trimmed.replace(',', ' ');
  trimmed.replace('\n', ' ');
  trimmed.replace('\r', ' ');
  trimmed.trim();
  if (trimmed.length() < 1) {
    trimmed = " ";
  }
  if (trimmed.length() > LCD_TEXT_MAX) {
    trimmed = trimmed.substring(0, LCD_TEXT_MAX);
  }
  trimmed.toCharArray(currentLcdText, LCD_TEXT_MAX + 1);
  lcdScrollIndex = 0;
  lcdScrollLength = trimmed.length();
  lastLcdScrollMs = millis();

  dwenguinoLCD.setCursor(0, 0);
  dwenguinoLCD.print(trimmed.substring(0, 16));
  dwenguinoLCD.setCursor(0, 1);
  dwenguinoLCD.print(trimmed.substring(16, 32));
}

/* ---- Continuous servo control ---- */

int sonarForNavigation(int cm) {
  return (cm > 0) ? cm : SONAR_FAR_CM;
}

int sonarForTelemetry(int cm) {
  return (cm <= MAX_DISTANCE) ? cm : 0;
}

int readCombinedSonarCm() {
  int readingA = sonarA1A0.ping_cm();
  int readingB = sonarA3A2.ping_cm();
  int a = sonarForNavigation(readingA);
  int b = sonarForNavigation(readingB);
  return (a < b) ? a : b;
}

void useContServo1(int vel) {
  servo1.writeMicroseconds(
    map(constrain(vel, -255, 255),
        -255, 255,
        2000, 1000)
  );
}

void useContServo2(int vel) {
  servo2.writeMicroseconds(
    map(constrain(vel, -255, 255),
        -255, 255,
        1000, 2000)
  );
}

void setTrackSpeeds(int leftVel, int rightVel) {
  useContServo1(leftVel);
  useContServo2(rightVel);
}

void moveForward(int vel) {
  int v = abs(constrain(vel, -255, 255));
  setTrackSpeeds(v, v);
}

void moveBackward(int vel) {
  int v = abs(constrain(vel, -255, 255));
  setTrackSpeeds(-v, -v);
}

void rotateLeft(int vel) {
  int v = abs(constrain(vel, -255, 255));
  setTrackSpeeds(-v, v);
}

void rotateRight(int vel) {
  int v = abs(constrain(vel, -255, 255));
  setTrackSpeeds(v, -v);
}

void stopRobot() {
  setTrackSpeeds(0, 0);
}

/* ---- Sonars ---- */

void refreshSonarSnapshot() {
  int left = sonarForTelemetry(sonarScanBySector[0]);
  int center = sonarForTelemetry(sonarScanBySector[1]);
  int right = sonarForTelemetry(sonarScanBySector[2]);

  sonar1 = left;
  sonar2 = right;

  int navLeft = sonarForNavigation(left);
  int navCenter = sonarForNavigation(center);
  int navRight = sonarForNavigation(right);
  int nearest = min(navLeft, min(navCenter, navRight));
  closest = (nearest > MAX_DISTANCE) ? 0 : nearest;
}

void setSonarEnabled(bool enabled) {
  sonarEnabled = enabled;
  if (!sonarEnabled) {
    sonarPanWaiting = false;
    sonarPanLastStepMs = 0;
    sonarPanCurrentAngle = SONAR_SCAN_ANGLES[1];
    sonarPanTargetAngle = SONAR_SCAN_ANGLES[1];
    if (servo3.attached()) {
      servo3.write(SONAR_SCAN_ANGLES[1]);
      delay(120);
      servo3.detach();
    }
    for (int i = 0; i < SONAR_SCAN_POINTS; i++) {
      sonarScanBySector[i] = SONAR_FAR_CM;
    }
    refreshSonarSnapshot();
    return;
  }

  if (!servo3.attached()) {
    servo3.attach(SONAR_PAN_PIN);
  }
  sonarPanWaiting = false;
  sonarPanLastStepMs = 0;
  if (sonarPanAutoMode) {
    sonarPanCurrentAngle = SONAR_SCAN_ANGLES[1];
    sonarPanTargetAngle = SONAR_SCAN_ANGLES[1];
    servo3.write(SONAR_SCAN_ANGLES[1]);
  } else {
    sonarPanTargetAngle = sonarPanCurrentAngle;
    servo3.write(sonarPanCurrentAngle);
  }
  for (int i = 0; i < SONAR_SCAN_POINTS; i++) {
    sonarScanBySector[i] = SONAR_FAR_CM;
  }
  refreshSonarSnapshot();
}

void updateSonarScan() {
  if (!sonarEnabled) {
    return;
  }
  if (!sonarPanAutoMode) {
    sonarScanBySector[1] = readCombinedSonarCm();
    refreshSonarSnapshot();
    return;
  }
  if (!sonarPanWaiting) {
    sonarPanTargetAngle = SONAR_SCAN_ANGLES[sonarScanIndex];
    if (sonarPanCurrentAngle == sonarPanTargetAngle) {
      sonarPanMovedAtMs = millis();
    }
    sonarPanLastStepMs = 0;
    sonarPanWaiting = true;
    return;
  }

  if (sonarPanCurrentAngle != sonarPanTargetAngle) {
    unsigned long now = millis();
    if (sonarPanLastStepMs == 0 || now - sonarPanLastStepMs >= SONAR_PAN_STEP_INTERVAL_MS) {
      int remaining = sonarPanTargetAngle - sonarPanCurrentAngle;
      if (abs(remaining) <= SONAR_PAN_STEP_DEG) {
        sonarPanCurrentAngle = sonarPanTargetAngle;
      } else if (remaining > 0) {
        sonarPanCurrentAngle += SONAR_PAN_STEP_DEG;
      } else {
        sonarPanCurrentAngle -= SONAR_PAN_STEP_DEG;
      }
      servo3.write(sonarPanCurrentAngle);
      sonarPanLastStepMs = now;
      sonarPanMovedAtMs = now;
    }
    return;
  }

  if (millis() - sonarPanMovedAtMs < SONAR_SCAN_SETTLE_MS) {
    return;
  }

  sonarScanBySector[sonarScanIndex] = readCombinedSonarCm();
  sonarScanIndex = (sonarScanIndex + 1) % SONAR_SCAN_POINTS;
  sonarPanWaiting = false;
  refreshSonarSnapshot();
}

void chooseSearchMotion() {
  int choice = random(0, 3);
  if (choice == 0) {
    navSearchLeft = NAV_SEARCH_FORWARD_SPEED;
    navSearchRight = NAV_SEARCH_FORWARD_SPEED;
    navSearchUntilMs = millis() + NAV_SEARCH_FORWARD_MS;
  } else if (choice == 1) {
    navSearchLeft = -NAV_SEARCH_TURN_SPEED;
    navSearchRight = NAV_SEARCH_TURN_SPEED;
    navSearchUntilMs = millis() + NAV_SEARCH_TURN_MS;
  } else {
    navSearchLeft = NAV_SEARCH_TURN_SPEED;
    navSearchRight = -NAV_SEARCH_TURN_SPEED;
    navSearchUntilMs = millis() + NAV_SEARCH_TURN_MS;
  }
}

void applyAutonomousNavigation() {
  int left = sonarForNavigation(sonar1);
  int right = sonarForNavigation(sonar2);
  int nearest = min(left, right);

  if (nearest <= NAV_AVOID_THRESHOLD_CM) {
    if (left < right) {
      setTrackSpeeds(-NAV_AVOID_SPEED, NAV_AVOID_SPEED);
    } else {
      setTrackSpeeds(NAV_AVOID_SPEED, -NAV_AVOID_SPEED);
    }
    currentNavMode = "AVOID";
    return;
  }

  if (nearest <= NAV_APPROACH_THRESHOLD_CM) {
    if (left < right) {
      setTrackSpeeds(NAV_APPROACH_SLOW, NAV_APPROACH_FAST);
    } else {
      setTrackSpeeds(NAV_APPROACH_FAST, NAV_APPROACH_SLOW);
    }
    currentNavMode = "APPROACH";
    return;
  }

  if (millis() >= navSearchUntilMs) {
    chooseSearchMotion();
  }
  setTrackSpeeds(navSearchLeft, navSearchRight);
  currentNavMode = "SEARCH";
}

void setMatrixPattern(const byte pattern[8]) {
  ByteBlock block = {};
  for (int row = 0; row < 8; row++) {
    block[row] = pattern[row];
  }
  led_matrix.displayOnSegment(LED_MATRIX_SEGMENT_INDEX, block);
}

void softResetState() {
  cmdLeft = 0;
  cmdRight = 0;
  cmdActive = false;
  stopLatch = true;
  lastCmdMs = millis();
  lastTelemetryMs = 0;
  inputPos = 0;
  setRgbOutput(0, 0, 0);
  setBuzzerOutput(false, 880);
  currentMatrixIndex = 0;
  currentNavMode = "STOP";
  navSearchUntilMs = 0;
  navSearchLeft = 0;
  navSearchRight = 0;
  sonarPanCurrentAngle = SONAR_SCAN_ANGLES[1];
  sonarPanTargetAngle = SONAR_SCAN_ANGLES[1];
  setPanAutoMode(true);
  for (int i = 0; i < SONAR_SCAN_POINTS; i++) {
    sonarScanBySector[i] = SONAR_FAR_CM;
  }
  sonarScanIndex = 0;
  setSonarEnabled(true);
  refreshSonarSnapshot();
  for (int i = 0; i < EMO_COUNT; i++) {
    currentEmo[i] = 0;
  }
  stopRobot();
  updateLCD(" ");
  compatClearLedMatrix();
  setEyebrowAngles(90, 90);
}

void applyEmotionOutputs() {
  int maxIndex = 0;
  int maxValue = currentEmo[0];
  for (int i = 1; i < EMO_COUNT; i++) {
    if (currentEmo[i] > maxValue) {
      maxValue = currentEmo[i];
      maxIndex = i;
    }
  }
  currentMatrixIndex = maxIndex;
  setMatrixPattern(MATRIX_PATTERNS[maxIndex]);

  switch (maxIndex) {
    case 0: setRgbOutput(0, 255, 0); break;      // Happiness
    case 1: setRgbOutput(255, 140, 0); break;    // Fatigue
    case 2: setRgbOutput(255, 0, 0); break;      // Hunger
    case 3: setRgbOutput(0, 0, 255); break;      // Sadness
    case 4: setRgbOutput(255, 0, 255); break;    // Anxiety
    case 5: setRgbOutput(255, 105, 180); break;  // Affection
    case 6: setRgbOutput(0, 255, 255); break;    // Curiosity
    default: setRgbOutput(255, 70, 0); break;    // Frustration
  }

  setBuzzerOutput(currentEmo[4] > 70 || currentEmo[7] > 70, 880);
  setEyebrowAngles(EYEBROW_ANGLES[maxIndex][0], EYEBROW_ANGLES[maxIndex][1]);
}

void sendTelemetry() {
  refreshSonarSnapshot();

  Serial.print(F("STAT:"));
  Serial.print(sonar1);
  Serial.print(F(","));
  Serial.print(sonar2);
  Serial.print(F(","));
  Serial.print(closest);
  Serial.print(F(","));
  Serial.print(0);
  Serial.print(F(","));
  Serial.print(currentNavMode);
  Serial.println();

  Serial.print(F("OUT:"));
  Serial.print(currentRgb[0]);
  Serial.print(F(","));
  Serial.print(currentRgb[1]);
  Serial.print(F(","));
  Serial.print(currentRgb[2]);
  Serial.print(F(","));
  Serial.print(currentBuzzerOn ? 1 : 0);
  Serial.print(F(","));
  Serial.print(EMO_NAMES[currentMatrixIndex]);
  Serial.print(F(","));
  Serial.println(currentLcdText);

  Serial.print(F("BROW:"));
  Serial.print(eyebrowLeftAngle);
  Serial.print(F(","));
  Serial.println(eyebrowRightAngle);

  Serial.print(F("ACT:"));
  Serial.print(sonarPanAutoMode ? F("AUTO") : F("MANUAL"));
  Serial.print(F(","));
  Serial.print(sonarPanCurrentAngle);
  Serial.print(F(","));
  Serial.print(currentBuzzerOn ? 1 : 0);
  Serial.print(F(","));
  Serial.println(currentBuzzerPitch);

  Serial.print(F("EMO:"));
  for (int i = 0; i < EMO_COUNT; i++) {
    Serial.print(currentEmo[i]);
    if (i < EMO_COUNT - 1) {
      Serial.print(F(","));
    }
  }
  Serial.println();
}

void handleLine(String line) {
  line.trim();
  if (line.length() == 0) {
    return;
  }
  if (line == "HELLO") {
    Serial.println(F("READY"));
    return;
  }
  if (line == "PING") {
    Serial.println(F("PONG"));
    return;
  }
  if (line == "STOP") {
    cmdActive = false;
    stopLatch = true;
    stopRobot();
    currentNavMode = "STOP";
    Serial.println(F("ACK:STOP"));
    return;
  }
  if (line == "RESET") {
    softResetState();
    Serial.println(F("ACK:RESET"));
    return;
  }
  if (line == "SONAR:ON") {
    setSonarEnabled(true);
    Serial.println(F("ACK:SONAR:ON"));
    return;
  }
  if (line == "SONAR:OFF") {
    setSonarEnabled(false);
    Serial.println(F("ACK:SONAR:OFF"));
    return;
  }
  if (line.startsWith("MOVE:")) {
    int commaIndex = line.indexOf(',', 5);
    if (commaIndex > 0) {
      int leftVal = line.substring(5, commaIndex).toInt();
      int rightVal = line.substring(commaIndex + 1).toInt();
      cmdLeft = constrain(leftVal, -255, 255);
      cmdRight = constrain(rightVal, -255, 255);
      cmdActive = true;
      stopLatch = false;
      lastCmdMs = millis();
      Serial.println(F("ACK:MOVE"));
    }
    return;
  }
  if (line.startsWith("LCD:")) {
    String msg = line.substring(4);
    updateLCD(msg);
    Serial.println(F("ACK:LCD"));
    return;
  }
  if (line.startsWith("BROW:")) {
    int commaIndex = line.indexOf(',', 5);
    if (commaIndex > 0) {
      int leftAngle = line.substring(5, commaIndex).toInt();
      int rightAngle = line.substring(commaIndex + 1).toInt();
      setEyebrowAngles(leftAngle, rightAngle);
      Serial.println(F("ACK:BROW"));
    }
    return;
  }
  if (line == "PAN:AUTO") {
    setPanAutoMode(true);
    Serial.println(F("ACK:PAN:AUTO"));
    return;
  }
  if (line == "PAN:MANUAL") {
    setPanAutoMode(false);
    Serial.println(F("ACK:PAN:MANUAL"));
    return;
  }
  if (line.startsWith("PAN:")) {
    int angle = line.substring(4).toInt();
    setPanManualAngle(angle);
    Serial.println(F("ACK:PAN"));
    return;
  }
  if (line.startsWith("RGB:")) {
    int first = line.indexOf(',', 4);
    int second = line.indexOf(',', first + 1);
    if (first > 0 && second > first) {
      int r = line.substring(4, first).toInt();
      int g = line.substring(first + 1, second).toInt();
      int b = line.substring(second + 1).toInt();
      setRgbOutput(r, g, b);
      Serial.println(F("ACK:RGB"));
    }
    return;
  }
  if (line == "BUZZER:OFF") {
    setBuzzerOutput(false, currentBuzzerPitch);
    Serial.println(F("ACK:BUZZER:OFF"));
    return;
  }
  if (line.startsWith("BUZZER:ON")) {
    int pitch = currentBuzzerPitch;
    int commaIndex = line.indexOf(',');
    if (commaIndex > 0) {
      pitch = line.substring(commaIndex + 1).toInt();
    }
    setBuzzerOutput(true, pitch);
    Serial.println(F("ACK:BUZZER:ON"));
    return;
  }
  if (line.startsWith("EMO:")) {
    String payload = line.substring(4);
    int idx = 0;
    int value = 0;
    bool hasValue = false;
    for (unsigned int i = 0; i <= payload.length(); i++) {
      char c = (i < payload.length()) ? payload.charAt(i) : ',';
      if (c >= '0' && c <= '9') {
        value = value * 10 + (c - '0');
        hasValue = true;
      } else if (c == ',' || i == payload.length()) {
        if (hasValue && idx < EMO_COUNT) {
          currentEmo[idx++] = constrain(value, 0, 100);
        }
        value = 0;
        hasValue = false;
      }
    }
    while (idx < EMO_COUNT) {
      currentEmo[idx++] = 0;
    }
    applyEmotionOutputs();
    Serial.println(F("ACK:EMO"));
    return;
  }
}

void readSerial() {
  while (Serial.available() > 0) {
    char incoming = (char)Serial.read();
    if (incoming == '\n' || incoming == '\r') {
      if (inputPos > 0) {
        inputBuffer[inputPos] = '\0';
        handleLine(String(inputBuffer));
        inputPos = 0;
      }
    } else if (inputPos < INPUT_BUFFER_SIZE - 1) {
      inputBuffer[inputPos++] = incoming;
    }
  }
}

void setup() {
  initDwenguino();
  compatInitLedMatrix();

  pinMode(SW_N, INPUT_PULLUP);
  pinMode(SW_W, INPUT_PULLUP);
  pinMode(SW_S, INPUT_PULLUP);
  pinMode(SW_E, INPUT_PULLUP);
  pinMode(SW_C, INPUT_PULLUP);

  Serial.begin(9600);
  randomSeed(analogRead(A4));

  servo1.attach(DRIVE_LEFT_PIN);
  servo2.attach(DRIVE_RIGHT_PIN);
  servo3.attach(SONAR_PAN_PIN);
  servo4.attach(EYEBROW_LEFT_PIN);
  servo5.attach(EYEBROW_RIGHT_PIN);
  setEyebrowAngles(90, 90);
  setSonarEnabled(true);
  stopRobot();
  refreshSonarSnapshot();

  updateLCD(" ");
  compatClearLedMatrix();
  applyEmotionOutputs();
}

void loop() {
  readSerial();
  if (sonarEnabled) {
    updateSonarScan();
  }

  if (stopLatch) {
    stopRobot();
    currentNavMode = "STOP";
  } else if (cmdActive && millis() - lastCmdMs < CMD_TIMEOUT_MS) {
    setTrackSpeeds(cmdLeft, cmdRight);
    currentNavMode = "CMD";
  } else {
    cmdActive = false;
    if (!digitalRead(SW_W)) {
      rotateLeft(MAX_VEL);
      currentNavMode = "MANUAL";
    } else if (!digitalRead(SW_E)) {
      rotateRight(MAX_VEL);
      currentNavMode = "MANUAL";
    } else if (!sonarEnabled) {
      stopRobot();
      currentNavMode = "SONAR_OFF";
    } else {
      applyAutonomousNavigation();
    }
  }

  if (millis() - lastTelemetryMs >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryMs = millis();
    sendTelemetry();
  }

  if (lcdScrollLength > 32 && millis() - lastLcdScrollMs >= LCD_SCROLL_INTERVAL_MS) {
    lastLcdScrollMs = millis();
    lcdScrollIndex++;
    if (lcdScrollIndex >= lcdScrollLength) {
      lcdScrollIndex = 0;
    }
    int start = lcdScrollIndex;
    String buffer = String(currentLcdText) + "    " + String(currentLcdText);
    String view = buffer.substring(start, start + 32);
    dwenguinoLCD.clear();
    dwenguinoLCD.setCursor(0, 0);
    dwenguinoLCD.print(view.substring(0, 16));
    dwenguinoLCD.setCursor(0, 1);
    dwenguinoLCD.print(view.substring(16, 32));
  }
}
