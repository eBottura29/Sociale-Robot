#include <Wire.h>
#include <Dwenguino.h>
#include <LiquidCrystal.h>
#include <NewPing.h>
#include <Servo.h>

#define ECHO_PIN_A0 A0
#define ECHO_PIN_A2 A2
#define TRIGGER_PIN_A1 A1
#define TRIGGER_PIN_A3 A3
#define MAX_DISTANCE 200
#define MAX_VEL 50

NewPing sonarA1A0(TRIGGER_PIN_A1, ECHO_PIN_A0, MAX_DISTANCE);
NewPing sonarA3A2(TRIGGER_PIN_A3, ECHO_PIN_A2, MAX_DISTANCE);

int sonar1;
int sonar2;
int closest;

Servo servo1;  // pin 40
Servo servo2;  // pin 41
Servo servo3;  // pin 19

void updateLCD(String str) {
  dwenguinoLCD.clear();
  dwenguinoLCD.setCursor(0, 0);
  dwenguinoLCD.print(str.substring(0, 16));
  dwenguinoLCD.setCursor(0, 1);
  dwenguinoLCD.print(str.substring(16, 32));
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

void setup() {
  initDwenguino();

  pinMode(SW_N, INPUT_PULLUP);
  pinMode(SW_W, INPUT_PULLUP);
  pinMode(SW_S, INPUT_PULLUP);
  pinMode(SW_E, INPUT_PULLUP);
  pinMode(SW_C, INPUT_PULLUP);

  Serial.begin(9600);
}

void loop() {
  float sonar_readings[2];
  scanSonars(sonar_readings);

  sonar1 = sonar_readings[0];
  sonar2 = sonar_readings[1];
  closest = (sonar1 < sonar2) ? sonar1 : sonar2;

  Serial.print(closest);
  Serial.println(F(" cm"));

  if (!digitalRead(SW_W)) {
    rotateRobot(MAX_VEL);
  } else if (!digitalRead(SW_E)) {
    rotateRobot(-MAX_VEL);
  } else {
    stopRobot();
  }
}
