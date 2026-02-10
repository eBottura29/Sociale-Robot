#include <Wire.h>
#include <Dwenguino.h>
#include <LiquidCrystal.h>
#include <NewPing.h>
#include <Servo.h>

// --- Dwenguino simulator compatibility shims ---
// Some simulator builds expose the LCD helpers but not the LED matrix/RGB helpers.
// Keep LED matrix calls as no-ops when the API isn't available so the sketch compiles.
static inline void compatClearLedMatrix() {}

static inline void compatSetLedMatrixPixel(int x, int y, bool on) {
  (void)x;
  (void)y;
  (void)on;
}

static inline void compatSetRGBLed(int r, int g, int b) {
#if defined(LED_R) && defined(LED_G) && defined(LED_B)
  analogWrite(LED_R, constrain(r, 0, 255));
  analogWrite(LED_G, constrain(g, 0, 255));
  analogWrite(LED_B, constrain(b, 0, 255));
#elif defined(RGB_LED_R) && defined(RGB_LED_G) && defined(RGB_LED_B)
  analogWrite(RGB_LED_R, constrain(r, 0, 255));
  analogWrite(RGB_LED_G, constrain(g, 0, 255));
  analogWrite(RGB_LED_B, constrain(b, 0, 255));
#else
  (void)r;
  (void)g;
  (void)b;
#endif
}

// Serieel protocol (regels, ASCII, newline)
// PC -> Robot
// - HELLO
// - PING
// - STOP
// - RESET                              software reset (state reset)
// - MOVE:<left>,<right>                 left/right = -255..255
// - LCD:<text>                          tekst op LCD
// - EMO:<h>,<fat>,<hun>,<sad>,<anx>,<aff>,<cur>,<fru>   0..100
//
// Robot -> PC
// - READY
// - PONG
// - ACK:<command>
// - ACK:RESET
// - STAT:<sonarL>,<sonarR>,<closest>,<battery>,<mode>
// - OUT:<r>,<g>,<b>,<buzzer>,<matrix>,<lcd>
// - EMO:<h>,<fat>,<hun>,<sad>,<anx>,<aff>,<cur>,<fru>

#define ECHO_PIN_A0 A0
#define ECHO_PIN_A2 A2
#define TRIGGER_PIN_A1 A1
#define TRIGGER_PIN_A3 A3
#define MAX_DISTANCE 200
#define MAX_VEL 50
#define TELEMETRY_INTERVAL_MS 250
#define CMD_TIMEOUT_MS 1000
#define LCD_SCROLL_INTERVAL_MS 450

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
unsigned long lastCmdMs = 0;
unsigned long lastTelemetryMs = 0;

int currentEmo[EMO_COUNT] = {0};
int currentRgb[3] = {0, 0, 0};
bool currentBuzzerOn = false;
int currentMatrixIndex = 0;
char currentLcdText[LCD_TEXT_MAX + 1] = " ";
unsigned long lastLcdScrollMs = 0;
int lcdScrollIndex = 0;
int lcdScrollLength = 0;

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

NewPing sonarA1A0(TRIGGER_PIN_A1, ECHO_PIN_A0, MAX_DISTANCE);
NewPing sonarA3A2(TRIGGER_PIN_A3, ECHO_PIN_A2, MAX_DISTANCE);

int sonar1;
int sonar2;
int closest;

Servo servo1;  // pin 40: cont. servo
Servo servo2;  // pin 41: cont. servo
Servo servo3;  // pin 19: 180° servo

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

void useContServo1(int vel) {
  servo1.attach(40);
  servo1.writeMicroseconds(
    map(constrain(vel, -255, 255),
        -255, 255,
        1000, 2000)
  );
}

void useContServo2(int vel) {
  servo2.attach(41);
  servo2.writeMicroseconds(
    map(constrain(vel, -255, 255),
        -255, 255,
        1000, 2000)
  );
}

void rotateRobot(int vel) {
  useContServo1(vel);
  useContServo2(-vel);
}

void stopRobot() {
  useContServo1(0);
  useContServo2(0);
}

/* ---- Sonars ---- */

void scanSonars(float readings[2]) {
  readings[0] = sonarA1A0.ping_cm();
  readings[1] = sonarA3A2.ping_cm();
}

void setMatrixPattern(const byte pattern[8]) {
  compatClearLedMatrix();
  for (int y = 0; y < 8; y++) {
    for (int x = 0; x < 8; x++) {
      bool on = (pattern[y] >> (7 - x)) & 0x01;
      compatSetLedMatrixPixel(x, y, on);
    }
  }
}

void softResetState() {
  cmdLeft = 0;
  cmdRight = 0;
  cmdActive = false;
  lastCmdMs = millis();
  lastTelemetryMs = 0;
  inputPos = 0;
  currentRgb[0] = 0;
  currentRgb[1] = 0;
  currentRgb[2] = 0;
  currentBuzzerOn = false;
  currentMatrixIndex = 0;
  for (int i = 0; i < EMO_COUNT; i++) {
    currentEmo[i] = 0;
  }
  stopRobot();
  noTone(BUZZER);
  updateLCD(" ");
  compatClearLedMatrix();
  applyEmotionOutputs();
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
    case 0: currentRgb[0] = 0; currentRgb[1] = 255; currentRgb[2] = 0; break;    // Happiness
    case 1: currentRgb[0] = 255; currentRgb[1] = 140; currentRgb[2] = 0; break;  // Fatigue
    case 2: currentRgb[0] = 255; currentRgb[1] = 0; currentRgb[2] = 0; break;    // Hunger
    case 3: currentRgb[0] = 0; currentRgb[1] = 0; currentRgb[2] = 255; break;    // Sadness
    case 4: currentRgb[0] = 255; currentRgb[1] = 0; currentRgb[2] = 255; break;  // Anxiety
    case 5: currentRgb[0] = 255; currentRgb[1] = 105; currentRgb[2] = 180; break;// Affection
    case 6: currentRgb[0] = 0; currentRgb[1] = 255; currentRgb[2] = 255; break;  // Curiosity
    default: currentRgb[0] = 255; currentRgb[1] = 70; currentRgb[2] = 0; break;  // Frustration
  }
  compatSetRGBLed(currentRgb[0], currentRgb[1], currentRgb[2]);

  currentBuzzerOn = (currentEmo[4] > 70 || currentEmo[7] > 70);
  if (currentBuzzerOn) {
    tone(BUZZER, 880);
  } else {
    noTone(BUZZER);
  }
}

void sendTelemetry() {
  float sonar_readings[2];
  scanSonars(sonar_readings);
  sonar1 = (int)sonar_readings[0];
  sonar2 = (int)sonar_readings[1];
  closest = (sonar1 < sonar2) ? sonar1 : sonar2;

  Serial.print(F("STAT:"));
  Serial.print(sonar1);
  Serial.print(F(","));
  Serial.print(sonar2);
  Serial.print(F(","));
  Serial.print(closest);
  Serial.print(F(","));
  Serial.print(0);
  Serial.print(F(","));
  Serial.print(F("AUTO"));
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
    stopRobot();
    Serial.println(F("ACK:STOP"));
    return;
  }
  if (line == "RESET") {
    softResetState();
    Serial.println(F("ACK:RESET"));
    return;
  }
  if (line.startsWith("MOVE:")) {
    int commaIndex = line.indexOf(',', 5);
    if (commaIndex > 0) {
      int leftVal = line.substring(5, commaIndex).toInt();
      int rightVal = line.substring(commaIndex + 1).toInt();
      cmdLeft = leftVal;
      cmdRight = rightVal;
      cmdActive = true;
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

  pinMode(SW_N, INPUT_PULLUP);
  pinMode(SW_W, INPUT_PULLUP);
  pinMode(SW_S, INPUT_PULLUP);
  pinMode(SW_E, INPUT_PULLUP);
  pinMode(SW_C, INPUT_PULLUP);

  Serial.begin(9600);

  updateLCD(" ");
  compatClearLedMatrix();
  applyEmotionOutputs();
}

void loop() {
  readSerial();

  if (cmdActive && millis() - lastCmdMs < CMD_TIMEOUT_MS) {
    useContServo1(cmdLeft);
    useContServo2(cmdRight);
  } else {
    cmdActive = false;
    if (!digitalRead(SW_W)) {
      rotateRobot(MAX_VEL);
    } else if (!digitalRead(SW_E)) {
      rotateRobot(-MAX_VEL);
    } else {
      stopRobot();
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
