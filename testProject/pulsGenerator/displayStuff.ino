/*  
**  displayStuff.ino - part of pulsGenerator.ino
**
**  Copyright (c) 2020 Willem Aandewiel 
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
**************************************************************************
*/



#include <Wire.h>  
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27,16,2); 



//====================================================================
void setupLCD()
{
  lcd.init();
  lcd.backlight();
  lcd.setBacklight(HIGH);

} // setupLCD()


//====================================================================
void initLCD()
{
  //--- initialize the library
  lcd.setCursor(0,0);
  lcd.print("JDengineers");
  lcd.setCursor(0,1);
  lcd.print("Encoder Pulse");
  
} // initOLED()

//====================================================================
void updateLCD()
{
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("FREQUENCY: "); 
  lcd.print(frequency);
  lcd.setCursor(0,1);
  lcd.print("NEW FREQ.: "); 
  lcd.print(newInputChar);
  
  Serial.print(F("FREQUENCY: ")); Serial.println(frequency);
  Serial.print(F("NEW FREQ.: ")); Serial.println(newInputChar);
  
} // updateDisplay()


//====================================================================
void easterLCD()
{
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print(" (c) Willem "); 
  lcd.setCursor(0,1);
  lcd.print("Aandewiel"); 
  Serial.println(F("(c) Willem Aandewiel"));
  
} // updateDisplay()



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
