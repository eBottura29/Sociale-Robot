#include <Wire.h>
#include <Dwenguino.h>
#include <LiquidCrystal.h>

int wakePattern = 0x0001;
int timePerBit = 300;

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

void uint16_to_bitstring(unsigned int value, char out[17]) {
    for (int i = 15; i >= 0; --i) {
        out[15 - i] = (value & (1u << i)) ? '1' : '0';
    }
    out[16] = '\0';
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
                uint16_t receivedXor = bitBuffer & 0xFFFF;

                if ((rawValueOne ^ rawValueTwo) == receivedXor) {
                    valueOne = (int16_t)rawValueOne;
                    valueTwo = (int16_t)rawValueTwo;
                    patternFound = true;
                } else {
                    dwenguinoLCD.setCursor(0,0);
                    dwenguinoLCD.print("ERROR CODE 1");
                    dwenguinoLCD.setCursor(0,1);
                    dwenguinoLCD.print("XOR FAIL");
                }
            }
        }
        uint64_t first32 = bitBuffer & 0xFFFFFFFFULL;

        unsigned int first16  = (first32 >> 16) & 0xFFFF;
        unsigned int second16 = first32 & 0xFFFF;

        char first16Str[17];
        char second16Str[17];

        uint16_to_bitstring(first16,  first16Str);
        uint16_to_bitstring(second16, second16Str);

        dwenguinoLCD.setCursor(0,0);
        dwenguinoLCD.print(first16Str);
        dwenguinoLCD.setCursor(0,1);
        dwenguinoLCD.print(second16Str);
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
