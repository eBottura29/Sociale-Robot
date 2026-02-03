# NIER - Neural Interactive Emotional Robot

[![Dwenguino](https://img.shields.io/badge/Platform-Dwenguino-orange)](https://www.dwengo.org/)
[![Arduino](https://img.shields.io/badge/Arduino-Compatible-blue)](https://www.arduino.cc/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-In%20Development-yellow)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**NIER** (Neural Interactive Emotional Robot) is een intelligente sociale robot gebouwd met Dwenguino die eenzaamheid helpt bestrijden door middel van AI-gestuurde conversaties, emotionele intelligentie en autonome navigatie.

> *Een project voor de Sociale Robot Wedstrijd gehost door Dwengo VZW*

---

## Inhoudsopgave

- [Over het Project](#over-het-project)
- [Maatschappelijk Probleem](#maatschappelijk-probleem)
- [Kenmerken](#kenmerken)
- [Systeemarchitectuur](#systeemarchitectuur)
- [Hardware Componenten](#hardware-componenten)
- [Software Componenten](#software-componenten)
- [Installatie](#installatie)
- [Gebruik](#gebruik)
- [Creatieve Ideeën & Toekomstige Uitbreidingen](#creatieve-ideeën--toekomstige-uitbreidingen)
- [Technische Overwegingen](#technische-overwegingen)
- [Team](#team)
- [Contact](#contact)

---

## Over het Project

NIER is een sociale companion robot die ontworpen is om eenzaamheid te bestrijden door menselijke interactie na te bootsen en gezelschap te bieden. De robot combineert kunstmatige intelligentie, emotionele verwerking en fysieke aanwezigheid om een engagerend en ondersteunend companion te creëren.

Het project maakt gebruik van:
- **Dwenguino microcontroller** voor robotcontrole
- **Gratis LLM** (Large Language Model) van HuggingFace voor natuurlijke conversaties
- **Emotie-verwerkings AI** die de stemming van gesprekken analyseert
- **Tank rups systeem** voor autonome navigatie
- **LED matrices** voor emotionele expressie

---

## Maatschappelijk Probleem: Eenzaamheid

**Eenzaamheid** is een groeiend maatschappelijk probleem dat mensen van alle leeftijden treft. Volgens onderzoek:
- Voelt **1 op de 3 jongeren** zich regelmatig eenzaam
- Heeft eenzaamheid **vergelijkbare gezondheidsrisico's** als roken
- Neemt sociaal isolement toe door digitalisering en individualisering van de samenleving

### Hoe NIER Helpt

Onze sociale robot biedt:
- **Constant gezelschap** - altijd beschikbaar voor een gesprek
- **Oordeel-vrije interactie** - geen angst voor sociale afwijzing
- **Emotionele ondersteuning** - herkent en reageert op emoties
- **Fysieke aanwezigheid** - meer dan alleen een scherm of stem
- **Interactief gedrag** - beweegt, piept en toont emoties

### Andere Potentiële Toepassingen

Dit robotconcept kan ook ingezet worden voor:
- **Dementiezorg** - gezelschap en geheugenondersteuning voor ouderen
- **Therapieondersteuning** - hulpmiddel voor psychologen en therapeuten  
- **Educatie** - interactieve leerassistent voor kinderen met sociale angst
- **Autisme-ondersteuning** - voorspelbare, veilige sociale interactie
- **Thuiszorg** - monitoring en gezelschap voor alleenstaanden
- **Entertainment** - interactieve gaming companion

---

## Kenmerken

### Conversatie & AI
- Natuurlijke gesprekken via LLM (HuggingFace of alternatief)
- Emotie-detectie en -verwerking van conversaties
- Desktop applicatie voor tekstcommunicatie
- Real-time communicatie via seriële verbinding (Arduino IDE Serial Monitor)

### Emotionele Expressie
- **4x LED Matrices** voor visuele emoties en stats:
  - **Happiness** (Geluk/Blijdschap)
  - **Fatigue** (Moeheid/Energie Level)
  - **Hunger** (Honger/Behoefte aan interactie)
  - **Sadness** (Verdriet/Eenzaamheid)
  - **Anxiety** (Ongerustheid/Stress)
  - **Affection** (Genegenheid/Verbondenheid)
  - **Curiosity** (Nieuwsgierigheid)
  - **Frustration** (Frustratie bij obstakels)

- **LCD Scherm** (2x16 karakters = 32 totaal)
  - Toont robotantwoorden
  - Kan ook stats weergeven (nog te bepalen)

### Navigatie & Sensoren
- **2x Sonar Sensors** gemonteerd op 180° servo
  - Meten afstand tot objecten
  - Data wordt naar laptop gestuurd voor navigatiebeslissingen
  
- **Tank Rups Systeem** (4 wielen met loopbanden)
  - Bestuurd door 2x 360° continue servos (één per kant)
  - Navigeert naar locaties bepaald door laptop

### Extra Features
- **RGB LED** - Debugging of visuele effecten
- **Buzzer** - R2D2-achtige piepjes voor acties en feedback
- **Bidirectionele communicatie** - Robot ↔ Laptop via seriële verbinding

---

## Systeemarchitectuur

```
┌─────────────────────────────────────────────────────────────┐
│                         LAPTOP                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Desktop Applicatie (Python)               │    │
│  │                                                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────┐    │    │
│  │  │  LLM Model   │  │   Emotie     │  │  GUI    │    │    │
│  │  │ (HuggingFace)│  │ Verwerking   │  │Interface│    │    │
│  │  │              │  │      AI      │  │         │    │    │
│  │  └──────┬───────┘  └──────┬───────┘  └─────┬───┘    │    │
│  │         │                 │                │        │    │
│  │         └─────────┬───────┴────────────────┘        │    │
│  │                   │                                 │    │
│  │         ┌─────────▼──────────┐                      │    │
│  │         │ Navigatie Logica   │                      │    │
│  │         │ (Sonar Data → Pad) │                      │    │
│  │         └─────────┬──────────┘                      │    │
│  └───────────────────┼─────────────────────────────────┘    │
└────────────────────┼─┼──────────────────────────────────────┘
                     │ │
              ┌──────▼─▼───────┐
              │ Serial Monitor │
              │  (USB Kabel)   │
              └──────┬─┬───────┘
                     │ │
┌────────────────────▼─▼────────────────────────────────────┐
│                    DWENGUINO / ROBOT                      │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Microcontroller Firmware               │  │
│  │                                                     │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Input     │  │  Verwerking │  │   Output    │  │  │
│  │  │ Handlers    │  │   Logica    │  │  Control    │  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │  │
│  └─────────┼────────────────┼────────────────┼─────────┘  │
│            │                │                │            │
│  ┌─────────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐     │
│  │ Sonar Sensors  │  │ LED Matrices│  │   Servos    │     │
│  │  (op servo)    │  │  (4x 8x8)   │  │ (2x Continu)│     │
│  └────────────────┘  └─────────────┘  └─────────────┘     │
│                                                           │
│  ┌────────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  LCD Display   │  │   RGB LED   │  │   Buzzer    │     │
│  │   (2x16)       │  │ (Debugging) │  │  (Geluiden) │     │
│  └────────────────┘  └─────────────┘  └─────────────┘     │
└───────────────────────────────────────────────────────────┘
```

### Communicatieflow

1. **Gebruiker → Laptop**: Typt bericht in desktop app
2. **Laptop**: 
   - LLM genereert antwoord
   - Emotie AI analyseert conversatie
   - Stuurt commando's naar robot via serieel
3. **Robot**: 
   - Ontvangt emotie-data en bewegingscommando's
   - Update LED matrices (emoties/stats)
   - Toont antwoord op LCD
   - Sonar data → terug naar laptop
4. **Laptop**: Verwerkt sonar data voor navigatiebeslissingen

---

## Hardware Componenten

### Microcontroller
- **1x Dwenguino Board** - Hoofdbesturing

### Display & Visualisatie
- **4x LED Matrix (8x8)** - Emoties en stats weergeven
- **1x LCD Scherm (16x2)** - Tekst output (32 karakters totaal)
- **1x RGB LED** - Debugging/visuele effecten

### Sensoren
- **2x Ultrasone Sonar Sensors (HC-SR04)** - Afstandsmeting
- **3x 180° Servo Motor** - Een voor sonar pan/tilt mechanisme en twee resterende voor wenkbrauwen

### Aandrijving
- **2x 360° Continue Servo Motors** - Tank aandrijving (links/rechts)
- **4x Wielen** - Tank rups/loopband systeem

### Audio
- **1x Buzzer** - R2D2-achtige geluiden

### Communicatie
- **USB Kabel** - Seriële verbinding met laptop

### Voeding
- **USB Kabel** - Zelfde verbinding met laptop

---

## Software Componenten

### Laptop Software (Python)

#### 1. Desktop Applicatie
```
Desktop App Features:
├── GUI Interface (tkinter/PyQt)
│   ├── Tekstinvoer venster
│   ├── Conversatie geschiedenis
│   └── Emotie/stats visualisatie
├── LLM Integratie
│   ├── HuggingFace API verbinding
│   └── Prompt engineering
├── Emotie Verwerking AI
│   ├── Sentiment analyse
│   ├── Emotie classificatie
│   └── Stats berekening (honger, moeheid, etc.)
└── Seriële Communicatie
    ├── Arduino Serial protocol
    └── Commando formatting
```

#### 2. LLM Opties (Gratis)
Mogelijke gratis LLM's via HuggingFace:
- **GPT-2** - Lichtgewicht, snel
- **BLOOM** - Meertalig (Nederlands!)
- **Flan-T5** - Goed in gesprekken
- **DistilGPT-2** - Compacte versie
- **LLaMA 2** (7B) - Via HuggingFace Inference API

#### 3. Emotie Verwerking
- **Sentiment Analysis Models**:
  - `nlptown/bert-base-multilingual-uncased-sentiment`
  - `cardiffnlp/twitter-roberta-base-sentiment`
- **Output**: Emotie scores → LED matrix patterns

#### 4. Navigatie Logica
```python
# Pseudocode
sonar_left, sonar_right = get_sonar_data()
if object_found(sonar_left, sonar_right):
    point_to_object()
    move_to_object()
else:
    move_randomly()
    search_for_object()
```

### Robot Software (Arduino/C++)

#### Firmware Structuur
```cpp
// Hoofdcomponenten
├── setup()
│   ├── Initialiseer LED matrices
│   ├── Initialiseer LCD
│   ├── Initialiseer servos
│   ├── Initialiseer sonars
│   └── Start seriële communicatie
├── loop()
│   ├── Lees seriële commando's
│   ├── Update emotie displays
│   ├── Control beweging
│   ├── Lees sonar data
│   └── Stuur data terug
└── Helper functies
    ├── displayEmotion()
    ├── updateLCD()
    ├── moveRobot()
    ├── playSoundEffect()
    └── scanSonars()
```

#### Emotie Patterns voor LED Matrices
```cpp
// Voorbeelden van emotie patronen
Happiness:    😊 (Smile pattern)
Sadness:      😢 (Tears + frown)
Fatigue:      😴 (Closed eyes)
Hunger:       🍔 (Empty battery icon)
Anxiety:      😰 (Sweat drops)
Affection:    😍 (Heart eyes)
Curiosity:    🤔 (Raised eyebrow)
Frustration:  😡 (Angry face)
```

---

## Installatie

### Vereisten

**Hardware:**
- Dwenguino board
- Alle componenten uit hardware lijst
- USB kabel
- Laptop met USB poort

**Software:**
- Arduino IDE (1.8.x of 2.x)
- Python 3.8+
- Dwenguino bibliotheek voor Arduino

### Laptop Setup

```bash
# Clone de repository
git clone https://github.com/eBottura29/Sociale-Robot
cd Sociale-Robot

# Installeer dependencies
pip install -r requirements.txt
```

**requirements.txt:**
```
transformers>=4.30.0
torch>=2.0.0
pyserial>=3.5
sentencepiece>=0.1.99
tkinter  # Of PyQt5
numpy>=1.24.0
```

### Robot Setup

1. Open Arduino IDE
2. Installeer Dwenguino board package
3. Open `src/robot/main/main.ino`
4. Selecteer **Tools > Board > Dwenguino**
5. Selecteer juiste COM poort
6. Upload code naar Dwenguino

---

## Gebruik

### 1. Start de Robot
```bash
# Verbind Dwenguino via USB
# Zet robot aan
```

### 2. Start de Desktop App
```bash
cd laptop_app
python main.py
```

### 3. Selecteer COM Poort
- Kies correcte poort in de app (bijv. COM3, /dev/ttyUSB0)
- Klik "Connect"

### 4. Begin Conversatie
- Typ een bericht in het invoerveld
- Druk op Enter of klik "Send"
- NIER's antwoord verschijnt op LCD
- Emoties worden getoond op LED matrices
- Robot navigeert autonoom in ruimte

### 5. Monitoring
- **Serial Monitor** (Arduino IDE): Bekijk debug info
- **Desktop App**: Zie conversatie en emotie scores
- **RGB LED**: Toont systeem status

---

## Creatieve Ideeën & Toekomstige Uitbreidingen

### Huidige Ideeën voor Verbetering

#### 1. **Gepersonaliseerde Geheugen**
- Robot onthoudt vorige conversaties
- Leert voorkeuren van gebruiker
- Refereert naar eerdere gesprekken

#### 2. **Dag/Nacht Ritme**
- Slaapmodus 's nachts (lagere moeheid gain)
- Actievere emoties overdag
- Licht-sensor om tijd te detecteren

#### 3. **"Huisdier" Gedrag**
- Volgt gebruiker door kamer
- Komt naar je toe als je belt
- Gaat "slapen" in oplaadstation

#### 4. **Muziek/Melodieën**
- Buzzer speelt herkenbare melodieën
- Verschillende tunes voor verschillende emoties
- Reactie op muziek in omgeving (microfoon?)

#### 5. **Gezichtsherkenning** (toekomstig)
- Camera module toevoegen
- Herkent verschillende gebruikers
- Verschillende persoonlijkheid per persoon

#### 6. **Voice Input/Output** (upgrade)
- Spraakherkenning via laptop
- Text-to-speech voor antwoorden
- Natuurlijkere conversaties

#### 7. **Social Media Integratie**
- Leest berichten voor
- Deelt quotes/grappige momenten
- Herinnert aan verjaardagen

#### 8. **Games & Activiteiten**
- Quiz spellen via LCD
- Geheugen spelletjes
- Woordraadsels

#### 9. **Gezondheids Monitoring**
- Herinnert aan medicatie
- Moedigt beweging aan
- Track slaappatroon (via moeheid stat)

#### 10. **Multi-Robot Interactie**
- Meerdere NIER robots kunnen "praten"
- Gezamenlijke taken uitvoeren
- Sociale groep simuleren

### RGB LED Toepassingen

Mogelijke toepassingen voor de RGB LED:
- 🔴 **Rood**: Laag batterij
- 🟢 **Groen**: Alles OK / Verbonden
- 🔵 **Blauw**: Aan het "denken" (LLM verwerkt)
- 🟡 **Geel**: Wacht op input
- 🟣 **Paars**: Navigatie modus
- ⚪ **Wit**: Aandacht nodig
- 🎨 **Regenboog**: Gelukkig/feestmodus
- 🔶 **Oranje**: Waarschuwing (obstakel)

### Emotie Stats Verwerking

Hoe emoties stats beïnvloeden:
```
Happiness ↑ → Robot is energieker, beweegt meer
Sadness ↑ → Langzamere bewegingen, rustiger
Fatigue ↑ → Vraagt om "rust", dimmed LED's
Hunger ↑ → Vraagt actief om interactie
Anxiety ↑ → Voorzichtiger navigatie
Affection ↑ → Blijft dichterbij gebruiker
```

---

## Technische Overwegingen

### Mogelijke Uitdagingen

#### 1. **Stroomverbruik**
- 4 LED matrices + 2 servos + LCD = veel stroom
- **Oplossing**: Krachtige Li-Po batterij (7.4V 2200mAh+)
- Voeg laag batterij waarschuwing toe

#### 2. **Seriële Communicatie Snelheid**
- LLM responses kunnen lang zijn voor LCD
- **Oplossing**: Scroll text op LCD, of splits in chunks
- Gebruik efficiënt protocol (JSON?)

#### 3. **LLM Response Tijd**
- Gratis HuggingFace API kan traag zijn
- **Oplossing**: Loading animatie op LED matrices
- Cache veel voorkomende vragen

#### 4. **Navigatie Precisie**
- 2 sonars misschien niet genoeg voor complexe omgevingen
- **Oplossing**: Conservatieve navigatie algoritme
- Gebruik buzzer bij obstakels

#### 5. **Emotie Accuraatheid**
- Sentiment analysis niet altijd perfect
- **Oplossing**: Laat gebruiker emotie bevestigen
- Machine learning op feedback

#### 6. **LCD Character Limit**
- 32 karakters is weinig voor lange zinnen
- **Oplossing**: 
  - Scroll horizontaal
  - Of splits in meerdere "pagina's"
  - Of toon alleen key phrases

### Voorgestelde Verbeteringen aan Huidige Plan

Een paar suggesties:

**Stats op LCD**: Misschien wissel tussen antwoord en stats met een delay
```
[0-3 sec]: "Hoi! Hoe gaat het?"
[3-6 sec]: "😊95% 😴32%"  // Happiness & Fatigue
```

**Sonar Servo Pattern**: 
```cpp
// Scan pattern voor betere detectie
servo.write(0);    // Links
delay(200);
readSonar();
servo.write(90);   // Midden  
delay(200);
readSonar();
servo.write(180);  // Rechts
delay(200);
readSonar();
```

**Buzzer Sound Effects**:
- Startup: Oplopende toon
- Bericht ontvangen: Korte beep
- Obstakel: Waarschuwingstoon
- Laag batterij: Repeterende beep
- Blij: Vrolijke melodie

**Emergency Stop**: 
- Knop op robot voor noodstop
- Of commando via laptop

---

## Team

**VTI Brugge**  
Vaartdijkstraat 3, Brugge, België

### Teamleden

| Naam | Rol | Email | Discord |
|------|-----|-------|---------|
| **Enrico Stefanuto Bottura** | Hoofd Programmeur, Planner/Organiser, Elektrische Schakeling | enrico.stefanutobott@vtibrugge.be | @eBottura |
| **Sam de Waele** | 2e Programmeur, Hoofd Elektrische Schakeling | sam.dewaele@vtibrugge.be | @de_crusader |
| **Yesse Dirk Paul Jozef Geeraert** | Design Helper, Wiel Designer, Emotionele Support | yesse.geeraert@vtibrugge.be | @sylq. |
| **Razvan Marian Aioanei** | Hoofd Designer, Graphical Designer, Hoofd Romeens | razvan.marianaioanei@vtibrugge.be | @boiiiiiiiiiiiiiiiiiiiiiiiiii |

---

## Contact

**Project:** NIER - Neural Interactive Emotional Robot  
**Wedstrijd:** Sociale Robot Wedstrijd (Dwengo VZW)  
**School:** VTI Brugge, Vaartdijkstraat 3, Brugge

Voor vragen over het project:
- **Algemene vragen**: ebottura@proton.me
- **Discord**: Contacteer een van de teamleden via Discord
- **Bug reports**: Open een issue op GitHub
- **Feature requests**: Open een discussion op GitHub

---

## Licentie

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Dankwoord

- **Dwengo VZW** - Voor het organiseren van de wedstrijd en de Dwenguino platform
- **HuggingFace** - Voor gratis toegang tot LLM modellen
- **VTI Brugge** - Voor de ondersteuning en apparatuur
- **ChatGPT & Google Gemini** - Algemene hulp
- **Claude** - Dit README.md

---

<div align="center">

[![Dwengo](https://img.shields.io/badge/Powered%20by-Dwengo-orange)](https://www.dwengo.org/)

</div>
