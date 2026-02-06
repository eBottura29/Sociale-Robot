# Dwengo / Dwenguino – **VOLLEDIGE** C++ / Arduino (.ino) documentatie

> Dit document is bedoeld als **DE ENIGE documentatie** die je nodig hebt om de Dwenguino te programmeren.
>
> Aannames:
>
> * Je kent **C++ of Arduino** (variabelen, if, loops, functies, arrays)
> * Je kent **Dwengo/Dwenguino nog NIET**
>
> Na het lezen van dit document moet je:
>
> * Elke Dwengo-component kunnen gebruiken
> * Bestaande Dwengo-code kunnen lezen
> * Zelf volledige projecten kunnen bouwen

---

# 1. Wat is de Dwenguino?

De **Dwenguino** is een **Arduino-compatibel** microcontrollerbord met:

* ATmega microcontroller (zoals Arduino Uno)
* Ingebouwde hardware:

  * LCD-scherm (16x2)
  * 5 knoppen
  * Buzzer
  * 8 LEDs
  * 8x8 LED-matrix
  * RGB LED
* Aansluitingen voor:

  * Servo’s
  * 360° servo’s
  * Sonar sensor
  * Analoge en digitale sensoren

Je programmeert de Dwenguino met een **.ino** bestand in de Arduino IDE.

---

# 2. Verplichte structuur van ELK Dwengo-programma

Elke Dwengo-code bestaat uit:

```cpp
#include <Dwenguino.h>

void setup() {
  initDwenguino();
}

void loop() {
}
```

## 2.1 `initDwenguino()` (EXTREEM BELANGRIJK)

Deze functie:

* Initialiseert het LCD-scherm
* Initialiseert de knoppen
* Initialiseert de LEDs
* Initialiseert de LED-matrix
* Initialiseert de buzzer

❗ **Zonder `initDwenguino()` werkt Dwengo NIET correct**

---

# 3. Alle mogelijke `#include` libraries (Dwengo)

## 3.1 Altijd of bijna altijd nodig

```cpp
#include <Dwenguino.h>      // Kern van het bord
#include <Wire.h>           // I2C communicatie (intern gebruikt)
#include <LiquidCrystal.h>  // LCD scherm
```

⚠️ `Dwenguino.h` is **de belangrijkste** library

---

## 3.2 Servo library

```cpp
#include <Servo.h>
```

Nodig voor:

* 180° servo
* 360° servo

---

## 3.3 Arduino standaard libraries (soms nodig)

```cpp
#include <Arduino.h>   // impliciet, meestal niet nodig om zelf te includen
#include <Math.h>
```

---

# 4. Pin-definities op de Dwenguino

## 4.1 Digitale en analoge pinnen

Zoals Arduino:

```cpp
A0 A1 A2 A3 A4 A5
0  1  2  3  4  5
```

---

## 4.2 Knoppen (ingebouwd)

```cpp
SW_N   // Noord
SW_E   // Oost
SW_S   // Zuid
SW_W   // West
SW_C   // Center
```

### Gebruik (VERPLICHT):

```cpp
pinMode(SW_S, INPUT_PULLUP);
```

### Logica:

| Waarde | Betekenis           |
| ------ | ------------------- |
| 0      | knop ingedrukt      |
| 1      | knop niet ingedrukt |

---

# 5. LCD-scherm (16x2)

Object:

```cpp
extern LiquidCrystal dwenguinoLCD;
```

### Functies

```cpp
dwenguinoLCD.clear();
dwenguinoLCD.setCursor(kolom, rij);
dwenguinoLCD.print("tekst");
```

* `kolom`: 0–15
* `rij`: 0 of 1

---

# 6. LEDs (8 stuks)

```cpp
setLed(ledNummer, HIGH);
setLed(ledNummer, LOW);
```

* `ledNummer`: 0–7

---

# 7. RGB LED

```cpp
setRGBLed(rood, groen, blauw);
```

* Waarden: 0–255

---

# 8. Buzzer

```cpp
tone(BUZZER, frequentie);
noTone(BUZZER);
```

Frequentie in Hz.

---

# 9. LED Matrix (8x8)

```cpp
setLedMatrixPixel(x, y, true);
setLedMatrixPixel(x, y, false);
```

* x: 0–7
* y: 0–7

```cpp
clearLedMatrix();
```

---

# 10. Servo (180°)

```cpp
Servo servo;
servo.attach(SERVO_1);
servo.write(hoek);
```

* `hoek`: 0–180

---

# 11. 360° Servo

```cpp
servo.write(90);   // stop
servo.write(0);    // max links
servo.write(180);  // max rechts
```

---

# 12. Sonar sensor

```cpp
long afstand = getSonarDistance();
```

* Eenheid: cm

---

# 13. Geluidssensor

```cpp
pinMode(A4, INPUT);
int geluid = digitalRead(A4);
```

---

# 14. Tijd & timing

```cpp
delay(ms);
millis();
```

---

# 15. Arrays & buffers (essentieel voor data)

```cpp
int buffer[64];
```

---

# 16. Typische Dwengo-specifieke regels

* `initDwenguino()` altijd eerst
* Knoppen zijn **actief LOW**
* LCD heeft maar 2 lijnen
* Servo’s gebruiken vaste poorten
* LED matrix coördinaten beginnen bij 0

---

# 17. Absolute minimum template

```cpp
#include <Dwenguino.h>

void setup() {
  initDwenguino();
}

void loop() {
}
```

---

Deze documentatie is geschreven door ChatGPT!