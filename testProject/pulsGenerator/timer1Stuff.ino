/*  
**  timer1Stuff.ino - part of pulsGenerator.ino
**
**  Copyright (c) 2020 Willem Aandewiel
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
**************************************************************************
*/




//====================================================================
int32_t calculateTimer1(int32_t freqAsked, uint8_t &newTCCR1B)
{
  int32_t compareMatch;

  //-Serial.print(F("freqAsked[")); Serial.print(freqAsked); Serial.println(F("]"));
  //--- we need 4 interrupts for 1 cycle of A and B (4 state changes)
  freqAsked *= 4; 
  
  compareMatch = _CLOCK / (freqAsked*1) - 1;
  //-Serial.print(F("preScale 0 ->compareMatch is [")); Serial.print(compareMatch);
  if (compareMatch < 65536)
  {
    //-Serial.println(F("] < 65536 --> OK!"));
    //-Serial.flush();
    //--- Set CS12, CS11 and CS10 bits for 1 prescaler
    newTCCR1B |= (0 << CS12) | (0 << CS11) | (1 << CS10);
    return compareMatch;
  }
  //-Serial.println();

  compareMatch = _CLOCK / (freqAsked*8) - 1;
  //-Serial.print(F("preScale 8 ->compareMatch is [")); Serial.print(compareMatch);
  if (compareMatch < 65536)
  {
    //-Serial.println(F("] < 65536 --> OK!"));
    //-Serial.flush();
    //--- Set CS12, CS11 and CS10 bits for 8 prescaler
    newTCCR1B |= (0 << CS12) | (1 << CS11) | (0 << CS10);
    return compareMatch;
  }
  //-Serial.println();

  compareMatch = _CLOCK / (freqAsked*64) - 1;
  //-Serial.print(F("preScale 64 -> compareMatch is [")); Serial.print(compareMatch);
  if (compareMatch < 65536)
  {
    //-Serial.println(F("] < 65536 --> OK!"));
    //-Serial.flush();
    //--- Set CS12, CS11 and CS10 bits for 64 prescaler
    newTCCR1B |= (0 << CS12) | (1 << CS11) | (1 << CS10);
    return compareMatch;
  }
  //-Serial.println();

  compareMatch = _CLOCK / (freqAsked*256) - 1;
  //-Serial.print(F("preScale 65536 ->compareMatch is [")); Serial.print(compareMatch);
  if (compareMatch < 65536)
  {
    //-Serial.println(F("] < 65536 --> OK!"));
    //-Serial.flush();
    //--- Set CS12, CS11 and CS10 bits for 256 prescaler
    newTCCR1B |= (1 << CS12) | (0 << CS11) | (0 << CS10);
    return compareMatch;
  }
  //-Serial.println();

  //-Serial.println(F("] >= 65536 --> ERROR!"));
  //-Serial.flush();

} // calculateTimer1()


//====================================================================
void setupTimer1(int32_t newFrequency)
{
  uint8_t newTCCR1B = 0;
  
  cli(); //--- stop interrupts

  //--- clear Timer1 interrupt values
  TCCR1A = 0; // set entire TCCR1A register to 0
  TCCR1B = 0; // same for TCCR1B
  TCNT1  = 0; // initialize counter value to 0

  //---   calculate number of interrupts
  OCR1A = calculateTimer1(newFrequency, newTCCR1B);

  //--------- this is an example for a 1kHz interrupt --------------
  //-- set compare match register for 1000 Hz increments
  // OCR1A = 15999; // = 16000000 / (1 * 1000) - 1 (must be <65536)
  //-- turn on CTC mode
  //  TCCR1B |= (1 << WGM12);
  //-- Set CS12, CS11 and CS10 bits for 1 prescaler
  //  TCCR1B |= (0 << CS12) | (0 << CS11) | (1 << CS10);
  //-- enable timer compare interrupt
  //  TIMSK1 |= (1 << OCIE1A);
  //------------------ end of example ------------------------------
  
  //--- turn on CTC mode
  TCCR1B |= (1 << WGM12);
  
  //--- Set  prescaler -------------------------
  //--- | CS12 | CS11 | CS10 | Opmerking
  //--- |------+------+------+------------------
  //--- |  0   |  0   |  0   | no Clock!!!
  //--- |  0   |  0   |  1   | No Prescaler
  //--- |  0   |  1   |  0   | 1/8 Prescaler
  //--- |  0   |  1   |  1   | 1/32 Prescaler
  //--- |  1   |  0   |  0   | 1/64 Prescaler
  //--- |  1   |  0   |  1   | 1/128 Prescaler
  //--- |  1   |  1   |  0   | 1/256 Prescaler
  //--- |  1   |  1   |  1   | 1/1024 Prescaler
  //--- |------+------+------+------------------

  //--- add prescaler information from calculateTimer1()
  TCCR1B |= newTCCR1B;

  //--- enable timer compare interrupt
  TIMSK1 |= (1 << OCIE1A);

  //--- update actual frequency
  frequency = newFrequency; 

  sei();  //--- allow interrupts

} // setupTimer1()



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
