/* 
***************************************************************************  
**  rotaryPulserInt     
**
**  Versie datum: 01-08-2020 
**
**  Copyright (c) 2020 Willem Aandewiel 
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
***************************************************************************  
**  
**  This program is based on the Timer1 interrupt handeling (COMPA)
**  to generate interupts.
**  Every four interrupts generate a full cycle A and B pulse
**  that are 50% shifted from each other.
**  
**  Frequency can either be keyed in from a 4x4 keypad
**  or calculated from the position of a potmeter.
**  
**  01-08-2020  Added 3 status leds (potmeter active, sweep mode, pulse output)
**              Added code to set sweep-time
**  31-07-2020  Added Sweep mode
**  10-07-2020  Advanced calculation of Timer1 values from requested frequency
**  09-07-2020  Changed from Timer2 to Timer1
**  08-07-2020  Added keypad input and LCD display
**  07-07-2020  Calculate timer2 values from input (not reliable)
**  06-07-2020  Initial release using Timer2 and potmeter reading
***************************************************************************      

* Pulsgever
* 
*      +---+   +---+   +--
*    A |   |   |   |   |        8 (11)
*    --+   +---+   +---+
*        +---+   +---+   +--
*      B |   |   |   |   |      9 (12)
*     ---+   +---+   +---+
* 
* Connections:
* 
*   KeyPad
*  ---------+                 Arduino
*  top view |              +------------+      (pins for JDJ PCB)
*           +-x nc         |            |
* [7] [*]   +------------> 2            0 ----> Tx
*           +------------> 3            1 <---- Rx 
* [8] [0]   +------------> 4            |
*           +------------> 5            4 <---> SDA
* [9] [#]   +------------> 6            5 <---> SCL
*           +------------> 7            |
* [C] [D]   +------------> 8 (11)   (8) 11 ----> Pulse A
*           +------------> 9 (12)   (9) 12 ----> Pulse B
*           +-x nc         |            |
*           |              |            A0 <--- Potmeter loper
*  ---------+              |            A1 ---> pulse out LED
*                          |            A2 ---> potmeter Active LED
*                          |            A3 ---> Sweep Mode Active LED
*                          +------------+
* 
* Connect lineair potmeter 10K between 5v, GND and A0
* 
*   5V  -------+
*              |
*             +-+
*             | |
*             | |<--- A0
*             | |
*             +-+
*              |
*   GND -------+ 
*
*   set frequency     : [0]-[9] .. [0]-[9] + [A]
*   set sweep         : from active frequency to new frequency and back in 10 seconds
*   activate sweep    : [0]-[9] .. [0]-[9] + [A] - [0]-[9] .. [0]-[9] + [B]
*   set sweep time    : [0]-[9] + [D]
*   activate potmeter : [*] + [A]
*   clear input       : [C] (and stop pulse)
*
*/

//#define _ALTERATIVE_CONNECTIONS       // this PCB has "D8 & D9 on D11 & D12" and "D11 & D12 on D8 & D9"

#define SETBIT(a,b)             ((a) |= _BV(b))
#define CLEARBIT(a, b)          ((a) &= ~_BV(b))
#define SET_LOW(_port, _pin)    ((_port) &= ~_BV(_pin))
#define SET_HIGH(_port, _pin)   ((_port) |= _BV(_pin))

#ifdef _ALTERATIVE_CONNECTIONS
  //--- alternative board
  #define pinA        8     // PB0    
  #define pinAbit     0     // PB0
  #define pinB        9     // PB1   
  #define pinBbit     1     // PB1
#else
  //--- normal board
  #define pinA       11     // PB3   
  #define pinAbit     3     // PB3
  #define pinB       12     // PB4   
  #define pinBbit     4     // PB5
#endif

#define POTMETER      A0     // PC0
#define LED_PULSE_ON  A1
#define LED_POTMETER  A2
#define LED_SWEEPMODE A3

#define _CLOCK    16000000
#define _MAXFREQCHAR    20
#define _HYSTERESIS      5

#include <Keypad.h>

const byte ROWS = 4; //four rows
const byte COLS = 4; //four columns
//define the symbols on the buttons of the keypads

char hexaKeys[ROWS][COLS] = {
      {'1', '2', '3', 'A'},
      {'4', '5', '6', 'B'},
      {'7', '8', '9', 'C'},
      {'*', '0', '#', 'D'}
};

#ifdef _ALTERATIVE_CONNECTIONS
  byte rowPins[ROWS] = { 5,  4, 3, 2}; 
  byte colPins[COLS] = {12, 11, 7, 6}; 
#else
  byte rowPins[ROWS] = { 5, 4, 3, 2}; 
  byte colPins[COLS] = { 9, 8, 7, 6}; 
#endif

Keypad inputKeypad = Keypad(makeKeymap(hexaKeys), rowPins, colPins, ROWS, COLS); 

char      inputKey;
char      newInputChar[_MAXFREQCHAR];
int32_t   newFrequency, startSweepFreq, endSweepFreq, diffFrequency;
float     stepFrequency;
uint32_t  sweepTimer, sweepTime = 4000;
uint32_t  ledBuiltinTimer;
uint8_t   freqKeyPos = 0;
uint16_t  potValue, potSaved, newPotValue;
bool      sweepModeActive, potmeterActive;

volatile int8_t  togglePin = 0;
volatile int32_t frequency;


//====================================================================
ISR(TIMER1_COMPA_vect)  //-- timer1 interrupt toggles pin 8 & 9 (should be 11 & 12)
{
  //--- generates pulse wave 
  //--- (takes two cycles for full wave - toggle high then toggle low)
  switch (togglePin)
  {
    case 0: //-- digitalWrite(pinA, HIGH);
            SET_HIGH(PORTB, pinAbit); 
            togglePin++;
            break;
    case 1: //-- digitalWrite(pinA, HIGH);
            SET_HIGH(PORTB, pinBbit); 
            togglePin++;
            break;
    case 2: //-- digitalWrite(pinA, LOW);
            SET_LOW(PORTB, pinAbit);  
            togglePin++;
            break;
    case 3: //-- digitalWrite(pinB, LOW);
            SET_LOW(PORTB, pinBbit); 
            togglePin = 0;
            break;
  }

} // ISR()


//====================================================================
void explanation()
{
  Serial.println(F("\r\nEnter frequency with [0]-[9] key's (in Hz)"));
  Serial.println(F("Enter [A] to accept new frequency"));
  Serial.println(F("Enter [B] accept second frequency for sweep"));
  Serial.println(F("Enter [C] to clear input"));
  Serial.println(F("Enter [D] to set sweep time (3-20 seconds)"));
  Serial.println(F("Enter [*] + [A] for potmeter reading"));
  
} // explanation()


//====================================================================
void readPotmeter()
{
  if (!potmeterActive) 
  {
    digitalWrite(LED_POTMETER, LOW);
    return;
  }
  
  digitalWrite(LED_POTMETER, HIGH);
  
  int16_t newPotValue = analogRead(POTMETER);
  //--- only changes within hesteresis are processed
  if (newPotValue > (potValue + _HYSTERESIS))       potValue = newPotValue;  
  else if (newPotValue < (potValue - _HYSTERESIS))  potValue = newPotValue;  

  newFrequency = map(potValue, 0, 1024, 5, 25500);

  if (newFrequency < 10)      newFrequency =    10;
  if (newFrequency > 25000)   newFrequency = 25000;
  
  if (potSaved != potValue)
  {
    Serial.print(F("Potmeter frequency: ")); Serial.println(newFrequency);
    setupTimer1(newFrequency);
    potSaved = potValue;
    sprintf(newInputChar, "potMeter");
    updateLCD();
  }

} // readPotmeter()


//====================================================================
void calculateSweep()
{
  diffFrequency = endSweepFreq - startSweepFreq;
  Serial.print(F("diffFreq[")); Serial.print(diffFrequency*10.0);
  Serial.print(F("] -> step[")); Serial.print((sweepTime / 10.0));
  Serial.println(F("]"));
  stepFrequency = (diffFrequency * 10.0) / (sweepTime / 10.0);  // steps
  Serial.print(F("sweep from[")); Serial.print(startSweepFreq);
  Serial.print(F("] Hz to[")); Serial.print(endSweepFreq);
  Serial.print(F("] Hz step[")); Serial.print(stepFrequency);
  Serial.println(F("]"));
  if (stepFrequency < 2.0)
  {
    sprintf(newInputChar, "SWEEP ERROR");
    digitalWrite(LED_SWEEPMODE, LOW);
    sweepModeActive = false;
  }
  else 
  {
    sprintf(newInputChar, "SWEEPMODE");
    digitalWrite(LED_SWEEPMODE, HIGH);
  }
  updateLCD();
  
} // calculateSweep()


//====================================================================
void sweep()
{
  static int8_t  stepDir = 1;
  static uint32_t elapse = millis();
  
  if (!sweepModeActive) 
  {
    digitalWrite(LED_SWEEPMODE, LOW);
    return;
  }
  
  digitalWrite(LED_SWEEPMODE, HIGH);

  if (millis() > sweepTimer)
  {
    newFrequency = frequency + (stepFrequency * stepDir);
 
    sweepTimer = millis() + 100;
    if (newFrequency <= startSweepFreq) 
    {
      sweepTimer = millis() + 500;
      Serial.print("elapsed time Sweep ["); Serial.print((float)((millis() - elapse) / 1000.0)); Serial.println("] seconds");
      newFrequency = startSweepFreq;
      stepDir =  1;
    }
    else if (newFrequency >= endSweepFreq) 
    {
      sweepTimer = millis() + 500;
      elapse = millis() - 505;  // beetje smokkelen ;-)
      stepDir = -1;
      newFrequency = endSweepFreq;
    }
    
    setupTimer1(newFrequency);

    //Serial.print(F("frequency[")); Serial.print(frequency);
    //Serial.println(F("]"));

  }
  
} // sweep()


//====================================================================
void setup()
{
  Serial.begin(115200);
  while (!Serial) { /* wait */ }

  setupLCD();
  initLCD();
  
  pinMode(pinA,          OUTPUT);
  pinMode(pinB,          OUTPUT);
  pinMode(POTMETER,      INPUT);
  pinMode(LED_BUILTIN,   OUTPUT);
  pinMode(LED_PULSE_ON,  OUTPUT);
  pinMode(LED_POTMETER,  OUTPUT);
  pinMode(LED_SWEEPMODE, OUTPUT);

  sprintf(newInputChar, "%5d", 1000);
  newFrequency = 1000;
  
  sweepModeActive = false;
  potmeterActive  = false;
  
  potValue = analogRead(POTMETER);
  
  Serial.println(F("\nAnd then it begins ...\n"));
  
  //setupTimer1(newFrequency);

  delay(1000);

  explanation();
    
} // setup()


//====================================================================
void loop()
{

  readPotmeter();
  sweep();
  
  inputKey = inputKeypad.getKey();
    
  if (Serial.available())
  {
    inputKey = Serial.read();
  }
  
  switch (inputKey)
  {
    case '0':
    case '1':
    case '2':
    case '3':
    case '4':
    case '5':
    case '6':
    case '7':
    case '8':
    case '9':   potmeterActive = false;
                if (freqKeyPos < _MAXFREQCHAR)
                {
                  newInputChar[freqKeyPos++] = inputKey;
                  newInputChar[freqKeyPos] = 0;
                }
                updateLCD();
                break;
                
    case 'A':   Serial.print(F("\r\nfreqKeyed in is [")); Serial.print(newInputChar); Serial.println(F("]"));
                Serial.flush();
                if (freqKeyPos == 0)  break;
                if (newInputChar[0] == '*')  
                {
                  potmeterActive = true;
                  potSaved       = 0;
                  break;
                }
                potmeterActive = false;
                newFrequency = atoi(newInputChar);
                if (newFrequency < 10) 
                {
                  newFrequency = 10;
                  sprintf(newInputChar, "< 10Hz");
                }
                if (newFrequency > 25000) 
                {
                  newFrequency = 25000;
                  sprintf(newInputChar, "> 25kHz");
                }
                setupTimer1(newFrequency);
                digitalWrite(LED_PULSE_ON, HIGH);
                updateLCD();
                freqKeyPos = 0;
                newInputChar[freqKeyPos] = 0;
                sweepModeActive = false;
                explanation();
                break;
                
    case 'B':   Serial.println(F("sweep mode"));
                sweepModeActive = true;
                startSweepFreq  = frequency;
                endSweepFreq    = atoi(newInputChar);
                if (startSweepFreq < 10)  startSweepFreq = 10;
                if (endSweepFreq < 10) 
                {
                  endSweepFreq = 10;
                }
                if (endSweepFreq > 25000) 
                {
                  endSweepFreq = 25000;
                }
                if (startSweepFreq == endSweepFreq) 
                {
                  sweepModeActive = false;
                  digitalWrite(LED_SWEEPMODE, LOW);
                  return;
                }
                if (startSweepFreq > endSweepFreq) 
                {
                  diffFrequency   = endSweepFreq;
                  endSweepFreq    = startSweepFreq;
                  startSweepFreq  = diffFrequency;
                }
                calculateSweep();
                freqKeyPos = 0;
                newInputChar[freqKeyPos] = 0;
                explanation();
                break;
                
    case 'C':   Serial.println(F("input cancelled"));
                //--- disable timer compare interrupt
                TIMSK1 = 0;
                SET_LOW(PORTB, pinAbit);
                SET_LOW(PORTB, pinBbit);
                freqKeyPos = 0;
                newInputChar[freqKeyPos] = 0;
                updateLCD();
                explanation();
                sweepModeActive = false;
                digitalWrite(LED_PULSE_ON, LOW);
                break;

    case '#':
    case '*':   //Serial.print(inputKey);
                if (freqKeyPos < _MAXFREQCHAR)
                {
                  newInputChar[freqKeyPos++] = inputKey;
                  newInputChar[freqKeyPos] = 0;
                }
                updateLCD();
                sweepModeActive = false;
                break;

    case 'D':   if (strcmp(newInputChar, "*0#") == 0)
                {
                  easterLCD();
                  //newFrequency = 1000;
                  //setupTimer1(newFrequency);
                  freqKeyPos = 0;
                  newInputChar[freqKeyPos] = 0;
                  sweepModeActive = false;
                  digitalWrite(LED_SWEEPMODE, LOW);
                  break;
                }
                Serial.print(F("sweeptime ["));
                sweepTime    = atoi(newInputChar) * 1000; // in ms
                if (sweepTime <  3000)  sweepTime =  3000;
                if (sweepTime > 20000)  sweepTime = 20000;
                Serial.print(sweepTime);
                Serial.println(F("] milliseconds"));
                sweepTime -= 1000;  // 2x 500ms stop at start and end
                calculateSweep();
                sprintf(newInputChar, "Sweep %d sec.", ((sweepTime+1000) / 1000));
                updateLCD();
                freqKeyPos = 0;
                newInputChar[freqKeyPos] = 0;
                newFrequency = startSweepFreq;
                explanation();
                break;
                
  } // switch(key)

  if (millis() > ledBuiltinTimer)
  {
    ledBuiltinTimer = millis() + 2000;
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }
  
} // loop()



/***************************************************************************
*
* Permission is hereby granted, free of charge, to any person obtaining a
* copy of this software and associated documentation files (the
* "Software"), to deal in the Software without restriction, including
* without limitation the rights to use, copy, modify, merge, publish,
* distribute, sublicense, and/or sell copies of the Software, and to permit
* persons to whom the Software is furnished to do so, subject to the
* following conditions:
*
* The above copyright notice and this permission notice shall be included
* in all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
* OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
* OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
* THE USE OR OTHER DEALINGS IN THE SOFTWARE.
* 
****************************************************************************
*/
