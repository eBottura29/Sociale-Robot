#include <Wire.h>

#include <Dwenguino.h>

#include <LiquidCrystal.h>

#include <Servo.h>

int max_speed = 100;

int speed = 0;

#define BUTTON_PIN_SW_S SW_S

int cw_input;

#define BUTTON_PIN_SW_W SW_W

int ccw_input;

Servo servoOnPin40;

void setup()
{
  initDwenguino();

  pinMode(BUTTON_PIN_SW_S, INPUT_PULLUP);
  pinMode(BUTTON_PIN_SW_W, INPUT_PULLUP);
}


void loop()
{
    cw_input = !digitalRead(BUTTON_PIN_SW_S);
    ccw_input = digitalRead(BUTTON_PIN_SW_W) - 1;
    speed = (cw_input + ccw_input) * max_speed;
    servoOnPin40.attach(40);
    servoOnPin40.writeMicroseconds(map(constrain(speed, -255, 255), -255, 255, 1500 - 500, 1500 + 500));

}