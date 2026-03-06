#include <Arduino.h>

const uint16_t WAKE_PATTERN = 0x5DAA;
const int TOTAL_BITS = 64;

void setup() {
    Serial.begin(9600);
    while (!Serial) {}

    Serial.println("Binary decoder ready.");
    Serial.println("Send 64 bits of 0/1 followed by newline.");
}

uint16_t read16Bits(const String& s, int start) {
    uint16_t value = 0;
    for (int i = 0; i < 16; i++) {
      value <<= 1;
      value |= (s[start + i] == '1') ? 1 : 0;
    }
    return value;
}

void loop() {
    if (Serial.available()) {

      String input = Serial.readStringUntil('\n');
      input.trim();

      if (input.length() != TOTAL_BITS) {
        Serial.println("ERROR: Input must be exactly 64 bits.");
        return;
      }

      // Validate characters
      for (int i = 0; i < TOTAL_BITS; i++) {
        if (input[i] != '0' && input[i] != '1') {
          Serial.println("ERROR: Only '0' and '1' allowed.");
          return;
        }
      }

      uint16_t wake     = read16Bits(input, 0);
      uint16_t rawOne   = read16Bits(input, 16);
      uint16_t rawTwo   = read16Bits(input, 32);
      uint16_t xorBits  = read16Bits(input, 48);

      Serial.print("Wake pattern: 0x");
      Serial.println(wake, HEX);

      if (wake != WAKE_PATTERN) {
        Serial.println("ERROR: Wake pattern mismatch.");
        return;
      }

      uint16_t computedXor = rawOne ^ rawTwo;

      Serial.print("Value One (raw): ");
      Serial.println((int16_t)rawOne);

      Serial.print("Value Two (raw): ");
      Serial.println((int16_t)rawTwo);

      Serial.print("XOR received: 0x");
      Serial.println(xorBits, HEX);

      Serial.print("XOR computed: 0x");
      Serial.println(computedXor, HEX);

      if (xorBits != computedXor) {
        Serial.println("ERROR: XOR CHECK FAILED");
        return;
      }

      float valueOne = ((int16_t)rawOne) / 256.0;
      float valueTwo = ((int16_t)rawTwo) / 256.0;

      Serial.println("=== DECODE OK ===");
      Serial.print("Value One (Q7.8): ");
      Serial.println(valueOne, 4);

      Serial.print("Value Two (Q7.8): ");
      Serial.println(valueTwo, 4);
      Serial.println("=================");
    }
}
