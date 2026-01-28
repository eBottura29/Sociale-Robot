#include <Wire.h>
#include <Dwenguino.h>
#include <LiquidCrystal.h>

int wakePattern = 0x5DAA;
int timePerBit = 100;

int valueOne = 0;
int valueTwo = 0;
bool patternFound = false;

#define SOUND_SENSOR_PIN_A4 A4
#define BUTTON_PIN_SW_S SW_S

uint64_t bitBuffer = 0;
unsigned long lastSampleTime = 0;

bool readStableBit() {
    int highCount = 0;
    for (int i = 0; i < 5; i++) {
        highCount += digitalRead(SOUND_SENSOR_PIN_A4);
    }
    return highCount >= 3;
}

void setup() {
    initDwenguino();
    pinMode(SOUND_SENSOR_PIN_A4, INPUT);
    pinMode(BUTTON_PIN_SW_S, INPUT_PULLUP);
}

void loop() {
    if (!patternFound) {
        unsigned long now = millis();
        if (now - lastSampleTime >= timePerBit) {
        lastSampleTime = now;

        bool bit = readStableBit();
        bitBuffer = (bitBuffer << 1) | bit;

        uint16_t receivedWake = (bitBuffer >> 48) & 0xFFFF;

        if (receivedWake == wakePattern) {
            uint16_t rawValueOne = (bitBuffer >> 32) & 0xFFFF;
            uint16_t rawValueTwo = (bitBuffer >> 16) & 0xFFFF;
            uint16_t receivedXor  = bitBuffer & 0xFFFF;

            if ((rawValueOne ^ rawValueTwo) == receivedXor) {
            valueOne = (int16_t)rawValueOne;
            valueTwo = (int16_t)rawValueTwo;
            patternFound = true;
            } else {
            dwenguinoLCD.setCursor(0,0);
            dwenguinoLCD.print("ERROR");
            dwenguinoLCD.setCursor(0,1);
            dwenguinoLCD.print("XOR FAIL");
            }
        }
        }
    } else {
        dwenguinoLCD.setCursor(0,0);
        dwenguinoLCD.print(valueOne / 256.0);
        dwenguinoLCD.setCursor(0,1);
        dwenguinoLCD.print(valueTwo / 256.0);

        if (digitalRead(BUTTON_PIN_SW_S) == 0) {
        patternFound = false;
        bitBuffer = 0;
        }
    }
}
