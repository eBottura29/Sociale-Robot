#include <Wire.h>
#include <Dwenguino.h>
#include <LiquidCrystal.h>
#include <NewPing.h>

#define ECHO_PIN_A0 A0
#define ECHO_PIN_A2 A2
#define TRIGGER_PIN_A1 A1
#define TRIGGER_PIN_A3 A3
#define MAX_DISTANCE 200

NewPing sonarA1A0(TRIGGER_PIN_A1, ECHO_PIN_A0, MAX_DISTANCE);
NewPing sonarA3A2(TRIGGER_PIN_A3, ECHO_PIN_A2, MAX_DISTANCE);

int sonar1;
int sonar2;
int closest;

void setup() {
  initDwenguino();
}

void loop() {
  sonar1 = (sonarA1A0.ping_cm());
  sonar2 = (sonarA3A2.ping_cm());

  closest = (sonar1 < sonar2) ? sonar1 : sonar2;

  dwenguinoLCD.clear();
  dwenguinoLCD.setCursor(0,0);
  dwenguinoLCD.print(String(closest) + " cm");
}