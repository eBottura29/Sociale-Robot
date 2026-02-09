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
- [Creatieve Ideeen & Toekomstige Uitbreidingen](#creatieve-ideeen--toekomstige-uitbreidingen)
- [Technische Overwegingen](#technische-overwegingen)
- [Team](#team)
- [Contact](#contact)

---

## Over het Project

NIER is een sociale companion robot die ontworpen is om eenzaamheid te bestrijden door menselijke interactie na te bootsen en gezelschap te bieden. De robot combineert kunstmatige intelligentie, emotionele verwerking en fysieke aanwezigheid om een engagerend en ondersteunend companion te creeren.

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

### Andere Potentiele Toepassingen

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
- Natuurlijke gesprekken via LLM (HuggingFace, lokaal, Engels)
- NL -> EN vertaling voor de LLM en EN -> NL vertaling na de LLM (mBART)
- Emotie-detectie en -verwerking van conversaties (nlptown/bert-base-multilingual-uncased-sentiment)
- Desktop applicatie voor tekstcommunicatie
- Real-time communicatie via seriele verbinding (PySerial)

### Emotionele Expressie
- **3x LED Matrices** voor visuele emoties:
  - **Happiness** (Geluk/Blijdschap)
  - **Fatigue** (Moeheid/Energie Level)
  - **Hunger** (Honger)
  - **Sadness** (Verdriet/Eenzaamheid)
  - **Anxiety** (Ongerustheid/Stress)
  - **Affection** (Genegenheid/Verbondenheid)
  - **Curiosity** (Nieuwsgierigheid)
  - **Frustration** (Frustratie)

- **LCD Scherm** (2x16 karakters = 32 totaal)
  - Toont robotantwoorden
  - Kan ook stats weergeven (nog te bepalen)

### Navigatie & Sensoren
- **2x Sonar Sensors** gemonteerd op 180Â° servo
  - Meten afstand tot objecten
  - Data wordt naar laptop gestuurd voor navigatiebeslissingen
  
- **Tank Rups Systeem** (4 wielen met loopbanden)
  - Bestuurd door 2x 360Â° continue servos (een per kant)
  - Navigeert naar locaties bepaald door laptop

### Extra Features
- **RGB LED** - Debugging of visuele effecten
- **Buzzer** - R2D2-achtige piepjes voor acties en feedback
- **Bidirectionele communicatie** - Robot â†” Laptop via seriele verbinding

---

### Communicatieflow

1. **Gebruiker - Laptop**: Typt bericht in desktop app
2. **Laptop**: 
   - LLM genereert antwoord
   - Emotie AI analyseert conversatie
   - Stuurt commando's naar robot via serieel
3. **Robot**: 
   - Ontvangt emotie-data en bewegingscommando's
   - Update LED matrices (emoties)
   - Toont antwoord op LCD
   - Sonar data â†’ terug naar laptop
4. **Laptop**: Verwerkt sonar data voor navigatiebeslissingen

---

## Hardware Componenten

### Microcontroller
- **1x Dwenguino Board (PIC18F4550)** - Hoofdbesturing

### Display & Visualisatie
- **3x LED Matrix (8x8) (1088AS)** - Emoties en weergeven
- **1x LCD Scherm (16x2) (WH1602B)** - Tekst output (32 karakters totaal)
- **1x RGB LED** - Debugging/visuele effecten

### Sensoren
- **2x Ultrasone Sonar Sensors (HC-SR04)** - Afstandsmeting
- **3x 180Â° Servo Motor** - Een voor sonar pan/tilt mechanisme en twee resterende voor wenkbrauwen

### Aandrijving
- **2x 360Â° Continue Servo Motors** - Tank aandrijving (links/rechts)
- **4x Wielen** - Tank rups/loopband systeem

### Audio
- **1x Buzzer** - R2D2-achtige geluiden

### Communicatie
- **USB Kabel (USB-A --> MICRO USB)** - Seriele verbinding met laptop

### Voeding
- **USB Kabel (USB-A --> MICRO USB)** - Diezelfde verbinding met laptop

---

## Software Componenten

### Laptop Software (Python)

#### 1. Desktop Applicatie
```
Desktop App Features:
- GUI Interface (tkinter)
  - Tekstinvoer venster
  - Emotie/stats visualisatie
- LLM Integratie
  - HuggingFace model lokaal (transformers)
  - Prompt engineering
- Emotie Verwerking AI
  - Sentiment analyse
  - Emotie classificatie
  - Stats berekening (honger, moeheid, etc.)
- Seriele Communicatie
  - Arduino Serial protocol
  - Commando formatting
```

#### 2. LLM Opties (Gratis)
**Actuele implementatie:** openai-community/gpt2-large (Engels, lokaal) + facebook/mbart-large-50-many-to-many-mmt (vertaling NL <-> EN)
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
- **Output**: Emotie scores -> LED matrix patterns

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

### Robot Software (C++)

#### Firmware Structuur
```cpp
// Hoofdcomponenten
- setup()
  - Initialiseer LED matrices
  - Initialiseer LCD
  - Initialiseer servos
  - Initialiseer sonars
  - Start seriele communicatie
-  loop()
  - Lees seriele commando's
  - Update emotie displays
  - Control beweging
  - Lees sonar data
  - Stuur data terug

```

#### Emotie Patterns voor LED Matrices
```cpp
// Voorbeelden van emotie patronen
Happiness (Smile pattern)
Sadness (Tears + frown)
Fatigue (Closed eyes)
Hunger (Empty battery icon)
Anxiety (Sweat drops)
Affection (Heart eyes)
Curiosity (Raised eyebrow)
Frustration (Angry face)
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
- Python 3.8+
- Git

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
pyserial>=3.5
transformers>=4.30.0
torch>=2.0.0
sentencepiece>=0.1.99
```
pyserial>=3.5
tkinter
```

### Robot Setup

1. Open `https://blockly.dwengo.org/`
2. Importeer code van `src/robot/firmware/main.cpp`
3. Druk op de RESET knop en dan op de S knop (dwenguino bord)
4. Laat bijde knoppen los
5. Klik op de "play" knop in de website
6. Als de programma gedownload is, kopieer die naar de USB van de DWENGUINO

---

## Gebruik

### 1. Start de Robot
```bash
# Verbind Dwenguino via USB
# Zet robot aan
```

### 2. Start de Desktop App
```bash
python src/desktop_app/main.py
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
- **Serial Monitor** (op blockly.dwengo.org): Bekijk debug info
- **Desktop App**: Zie conversatie en emotie scores
- **RGB LED**: Toont systeem status

---

## Creatieve Ideeen & Toekomstige Uitbreidingen

### Huidige Ideeen voor Verbetering

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

#### 4. **Muziek/Melodieen**
- Buzzer speelt herkenbare melodieen
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
- ðŸ”´ **Rood**: Laag batterij
- ðŸŸ¢ **Groen**: Alles OK / Verbonden
- ðŸ”µ **Blauw**: Aan het "denken" (LLM verwerkt)
- ðŸŸ¡ **Geel**: Wacht op input
- ðŸŸ£ **Paars**: Navigatie modus
- âšª **Wit**: Aandacht nodig
- ðŸŽ¨ **Regenboog**: Gelukkig/feestmodus
- ðŸ”¶ **Oranje**: Waarschuwing (obstakel)

### Emotie Stats Verwerking

Hoe emoties stats beinvloeden:
```
Happiness: Robot is energieker, beweegt meer
Sadness: Langzamere bewegingen, rustiger
Fatigue: Vraagt om "rust", dimmed LED's
Hunger: Vraagt actief om interactie
Anxiety: Voorzichtiger navigatie
Affection: Blijft dichterbij gebruiker
```

---

## Technische Overwegingen

### Mogelijke Uitdagingen

#### 1. **Stroomverbruik**
- 4 LED matrices + 2 servos + LCD = veel stroom
- **Oplossing**: Krachtige Li-Po batterij (7.4V 2200mAh+)
- Voeg laag batterij waarschuwing toe

#### 2. **Seriele Communicatie Snelheid**
- LLM responses kunnen lang zijn voor LCD
- **Oplossing**: Scroll text op LCD, of splits in chunks
- Gebruik efficient protocol (JSON?)

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
Vaartdijkstraat 3, Brugge, Belgie

### Teamleden

| Naam | Rol | Email | Discord |
|------|-----|-------|---------|
| **Enrico Stefanuto Bottura** | Hoofd Programmeur, Planner/Organiser, Elektrische Schakeling | enrico.stefanutobott@vtibrugge.be | @eBottura |
| **Sam de Waele** | 2e Programmeur, Hoofd Elektrische Schakeling, Onderzoeker van regelementen | sam.dewaele@vtibrugge.be | @de_crusader |
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
- **Claude** - Dit README.md bestand

---

<div align="center">

[![Dwengo](https://img.shields.io/badge/Powered%20by-Dwengo-orange)](https://www.dwengo.org/)

</div>

