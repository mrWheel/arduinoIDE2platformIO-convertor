/* 
***************************************************************************  
**  Program  : helperStuff, part of ESP_ticker
**
**  Copyright (c) 2021 Willem Aandewiel
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
***************************************************************************      
*/


//===========================================================================================
bool compare(String x, String y) 
{ 
    for (int i = 0; i < min(x.length(), y.length()); i++) { 
      if (x[i] != y[i]) 
      {
        return (bool)(x[i] < y[i]); 
      }
    } 
    return x.length() < y.length(); 
    
} // compare()


//===========================================================================================
boolean isValidIP(IPAddress ip)
{
 /* Works as follows:
   *  example: 
   *  127.0.0.1 
   *   1 => 127||0||0||1 = 128>0 = true 
   *   2 => !(false || false) = true
   *   3 => !(false || false || false || false ) = true
   *   4 => !(true && true && true && true) = false
   *   5 => !(false) = true
   *   true && true & true && false && true = false ==> correct, this is an invalid addres
   *   
   *   0.0.0.0
   *   1 => 0||0||0||0 = 0>0 = false 
   *   2 => !(true || true) = false
   *   3 => !(false || false || false || false) = true
   *   4 => !(true && true && true && tfalse) = true
   *   5 => !(false) = true
   *   false && false && true && true && true = false ==> correct, this is an invalid addres
   *   
   *   192.168.0.1 
   *   1 => 192||168||0||1 =233>0 = true 
   *   2 => !(false || false) = true
   *   3 +> !(false || false || false || false) = true
   *   4 => !(false && false && true && true) = true
   *   5 => !(false) = true
   *   true & true & true && true && true = true ==> correct, this is a valid address
   *   
   *   255.255.255.255
   *   1 => 255||255||255||255 =255>0 = true 
   *   2 => !(false || false ) = true
   *   3 +> !(true || true || true || true) = false
   *   4 => !(false && false && false && false) = true
   *   5 => !(true) = false
   *   true && true && false && true && false = false ==> correct, this is an invalid address
   *   
   *   0.123.12.1       => true && false && true && true && true = false  ==> correct, this is an invalid address 
   *   10.0.0.0         => true && false && true && true && true = false  ==> correct, this is an invalid address 
   *   10.255.0.1       => true && true && false && true && true = false  ==> correct, this is an invalid address 
   *   150.150.255.150  => true && true && false && true && true = false  ==> correct, this is an invalid address 
   *   
   *   123.21.1.99      => true && true && true && true && true = true    ==> correct, this is annvalid address 
   *   1.1.1.1          => true && true && true && true && true = true    ==> correct, this is annvalid address 
   *   
   *   Some references on valid ip addresses: 
   *   - https://www.quora.com/How-do-you-identify-an-invalid-IP-address
   *   
   */
  boolean _isValidIP = false;
  _isValidIP = ((ip[0] || ip[1] || ip[2] || ip[3])>0);                             // if any bits are set, then it is not 0.0.0.0
  _isValidIP &= !((ip[0]==0) || (ip[3]==0));                                       // if either the first or last is a 0, then it is invalid
  _isValidIP &= !((ip[0]==255) || (ip[1]==255) || (ip[2]==255) || (ip[3]==255)) ;  // if any of the octets is 255, then it is invalid  
  _isValidIP &= !(ip[0]==127 && ip[1]==0 && ip[2]==0 && ip[3]==1);                 // if not 127.0.0.0 then it might be valid
  _isValidIP &= !(ip[0]>=224);                                                     // if ip[0] >=224 then reserved space  
  
  DebugTf( "%d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3]);
  if (_isValidIP) 
    Debugln(F(" = Valid IP")); 
  else 
    Debugln(F(" = Invalid IP!"));
    
  return _isValidIP;
  
} //  isValidIP()


//===========================================================================================
bool isNumericp(const char *timeStamp, int8_t len)
{
  for (int i=0; (i<len && i<12);i++)
  {
    if (timeStamp[i] < '0' || timeStamp[i] > '9')
    {
      return false;
    }
  }
  return true;
  
} // isNumericp()


//===========================================================================================
int8_t splitString(String inStrng, char delimiter, String wOut[], uint8_t maxWords) 
{
  int16_t inxS = 0, inxE = 0, wordCount = 0;
  
    inStrng.trim();
    while(inxE < inStrng.length() && wordCount < maxWords) 
    {
      inxE  = inStrng.indexOf(delimiter, inxS);         //finds location of first ,
      wOut[wordCount] = inStrng.substring(inxS, inxE);  //captures first data String
      wOut[wordCount].trim();
      //DebugTf("[%d] => [%c] @[%d] found[%s]\r\n", wordCount, delimiter, inxE, wOut[wordCount].c_str());
      inxS = inxE;
      inxS++;
      wordCount++;
    }
    // zero rest of the words
    for(int i=wordCount; i< maxWords; i++)
    {
      wOut[wordCount][0] = 0;
    }
    // if not whole string processed place rest in last word
    if (inxS < inStrng.length()) 
    {
      wOut[maxWords-1] = inStrng.substring(inxS, inStrng.length());  // store rest of String      
    }

    return wordCount;
    
} // splitString()



//===========================================================================================
void strConcat(char *dest, int maxLen, const char *src)
{
  if (strlen(dest) + strlen(src) < maxLen) 
  {
    strcat(dest, src);
  } 
  else
  {
    DebugTf("Combined string > %d chars\r\n", maxLen);
  }
  
} // strConcat()


//===========================================================================================
void strConcat(char *dest, int maxLen, float v, int dec)
{
  static char buff[25];
  if (dec == 0)       sprintf(buff,"%.0f", v);
  else if (dec == 1)  sprintf(buff,"%.1f", v);
  else if (dec == 2)  sprintf(buff,"%.2f", v);
  else if (dec == 3)  sprintf(buff,"%.3f", v);
  else if (dec == 4)  sprintf(buff,"%.4f", v);
  else if (dec == 5)  sprintf(buff,"%.5f", v);
  else                sprintf(buff,"%f",   v);

  if (strlen(dest) + strlen(buff) < maxLen) 
  {
    strcat(dest, buff);
  } 
  else
  {
    DebugTf("Combined string > %d chars\r\n", maxLen);
  }
  
} // strConcat()


//===========================================================================================
void strConcat(char *dest, int maxLen, int v)
{
  static char buff[25];
  sprintf(buff,"%d", v);

  if (strlen(dest) + strlen(buff) < maxLen) 
  {
    strcat(dest, buff);
  } 
  else
  {
    DebugTf("Combined string > %d chars\r\n", maxLen);
  }
  
} // strConcat()


//===========================================================================================
void strToLower(char *src)
{
  for (int i = 0; i < strlen(src); i++)
  {
    if (src[i] == '\0') return;
    if (src[i] >= 'A' && src[i] <= 'Z')
        src[i] += 32;
  }
} // strToLower()

//===========================================================================================
// a 'save' string copy
void strCopy(char *dest, int maxLen, const char *src, int frm, int to)
{
  int d=0;
//DebugTf("dest[%s], src[%s] max[%d], frm[%d], to[%d] =>\r\n", dest, src, maxLen, frm, to);
  dest[0] = '\0';
  for (int i=0; i<=frm; i++)
  {
    if (src[i] == 0) return;
  }
  for (int i=frm; (src[i] != 0  && i<=to && d<maxLen); i++)
  {
    dest[d++] = src[i];
  }
  dest[d] = '\0';
    
} // strCopy()

//===========================================================================================
// a 'save' version of strncpy() that does not put a '\0' at
// the end of dest if src >= maxLen!
void strCopy(char *dest, int maxLen, const char *src)
{
  dest[0] = '\0';
  strcat(dest, src);
    
} // strCopy()

//===========================================================================================
// 'tttABCtDEtFGHttt' => 'ABCtDEtFGHttt'
void strLTrim(char *dest, int maxLen, const char tChar )
{
  char tmp[maxLen];
  int  tPos = 0;
  bool done = false;
  
  tmp[0] = '\0';

  for (int dPos=0; (dPos<maxLen && dest[dPos] != '\0'); dPos++)
  {
    if (dest[dPos] != tChar || done)
    {
      tmp[tPos++] = dest[dPos];
      done = true;
    }
  }
  tmp[tPos] = '\0';
  strCopy(dest, maxLen, tmp);
    
} // strLTrim()

//===========================================================================================
// 'tttABCtDEtFGHttt' => 'tttABCtDEtFGH'
void strRTrim(char *dest, int maxLen, const char tChar )
{
  char tmp[maxLen];
  int dPos, tPos, dMax;
  bool done = false;
  
  for(dMax=0; dMax<maxLen; dMax++) { tmp[dMax] = '\0'; }
  
  dMax = strlen(dest)-1;
  for (dPos=dMax; (dPos>=0 && !done); dPos--)
  {
    if (dest[dPos] == tChar)
    {
      tPos = dPos;
      tmp[tPos] = '\0';
    }
    else done = true;
  }
  dPos++;
  for(dMax = 0; dMax <= dPos; dMax++)
  {
    tmp[dMax] = dest[dMax];
  }
  tmp[dMax+1] = '\0';
  strCopy(dest, maxLen, tmp);
    
} // strRTrim()

//===========================================================================================
// 'tttABCtDEtFGHttt' => 'ABCtDEtFGH'
void strTrim(char *dest, int maxLen, const char tChar )
{
  char sTmp[maxLen];
  
  strCopy(sTmp, maxLen, dest); 
  strLTrim(sTmp, maxLen, tChar);
  strRTrim(sTmp, maxLen, tChar);
  strCopy(dest, maxLen, sTmp); 
    
} // strTrim()

//===========================================================================================
void strRemoveAll(char *dest, int maxLen, const char tChar)
{
  char tmp[maxLen];
  int  tPos = 0;
  tmp[0] = '\0';
  for (int dPos=0; (dPos<maxLen && dest[dPos] != '\0'); dPos++)
  {
    if (dest[dPos] != tChar)
    {
      tmp[tPos++] = dest[dPos];
    }
  }
  tmp[tPos] = '\0';
  strCopy(dest, maxLen, tmp);
    
} // strRemoveAll()


//===========================================================================================
void strTrimCntr(char *dest, int maxLen)
{
  char tmp[maxLen];
  int tPos = 0;
  tmp[0] = '\0';
  for (int dPos=0; (dPos<maxLen && dest[dPos] != '\0'); dPos++)
  {
    if (dest[dPos] >= ' ' && dest[dPos] <= '~')  // space = 32, '~' = 127
    {
      tmp[tPos++] = dest[dPos];
    }
  }
  tmp[tPos] = '\0';
  strCopy(dest, maxLen, tmp);
    
} // strTrimCntr()

//===========================================================================================
int strIndex(const char *haystack, const char *needle, int start)
{
  // strindex(hay, needle) ????
  char *p = strstr(haystack+start, needle);
  if (p) {
    //DebugTf("found [%s] at position [%d]\r\n", needle, (p - haystack));
    return (p - haystack);
  }
  return -1;
  
} // strIndex()

//===========================================================================================
int strIndex(const char *haystack, const char *needle)
{
  return strIndex(haystack, needle, 0);
  
} // strIndex()

//===========================================================================================
int stricmp(const char *a, const char *b)
{
    for (;; a++, b++) {
        int d = tolower((unsigned char)*a) - tolower((unsigned char)*b);
        if (d != 0 || !*a)
            return d;
    }
    
} // stricmp()

//===========================================================================================
char *intToStr(int32_t v)
{
  static char buff[25];
  sprintf(buff,"%d", v);
  return buff;
  
} // intToStr()

//===========================================================================================
char *floatToStr(float v, int dec)
{
  static char buff[25];
  if (dec == 0)       sprintf(buff,"%.0f", v);
  else if (dec == 1)  sprintf(buff,"%.1f", v);
  else if (dec == 2)  sprintf(buff,"%.2f", v);
  else if (dec == 3)  sprintf(buff,"%.3f", v);
  else if (dec == 4)  sprintf(buff,"%.4f", v);
  else if (dec == 5)  sprintf(buff,"%.5f", v);
  else                sprintf(buff,"%f",   v);
  return buff;
  
} // floattToStr()

//===========================================================================================
float formatFloat(float v, int dec)
{
  return (String(v, dec).toFloat());

} //  formatFloat()

//===========================================================================================
float strToFloat(const char *s, int dec)
{
  float r =  0.0;
  int   p =  0;
  int   d = -1;
  
  r = strtof(s, NULL);
  p = (int)(r*pow(10, dec));
  r = p / pow(10, dec);
  //DebugTf("[%s][%d] => p[%d] -> r[%f]\r\n", s, dec, p, r);
  return r; 

} //  strToFloat()

//===========================================================================================
void parseJsonKey(const char *sIn, const char *key, char *val, int valLen)
{
  // json key-value pair looks like:
  //      "samenv": "Zwaar bewolkt",
  // or   "samenv": "Zwaar bewolkt"}
  int keyStart   = strIndex(sIn, key);
  int sepStart   = strIndex(sIn, ",", keyStart);
  if (sepStart == -1) 
  {
    sepStart   = strIndex(sIn, "}", keyStart);
  }
  strCopy(val, valLen, sIn, keyStart+strlen(key), sepStart);
  strRemoveAll(val, valLen, ':');
  strRemoveAll(val, valLen, ',');
  strRemoveAll(val, valLen, '}');
  strRemoveAll(val, valLen, '"');
  strTrim(val, valLen, ' ');
  
} // parseJsonKey()

//===========================================================================================
uint8_t utf8Ascii(uint8_t ascii)
// Convert a single Character from UTF8 to Extended ASCII according to ISO 8859-1,
// also called ISO Latin-1. Codes 128-159 contain the Microsoft Windows Latin-1
// extended characters:
// - codes 0..127 are identical in ASCII and UTF-8
// - codes 160..191 in ISO-8859-1 and Windows-1252 are two-byte characters in UTF-8
//                 + 0xC2 then second byte identical to the extended ASCII code.
// - codes 192..255 in ISO-8859-1 and Windows-1252 are two-byte characters in UTF-8
//                 + 0xC3 then second byte differs only in the first two bits to extended ASCII code.
// - codes 128..159 in Windows-1252 are different, but usually only the €-symbol will be needed from this range.
//                 + The euro symbol is 0x80 in Windows-1252, 0xa4 in ISO-8859-15, and 0xe2 0x82 0xac in UTF-8.
//
// Modified from original code at http://playground.arduino.cc/Main/Utf8ascii
// Extended ASCII encoding should match the characters at http://www.ascii-code.com/
//
// Return "0" if a byte has to be ignored.
{
  static uint8_t cPrev;
  uint8_t c = '\0';

  if (ascii < 0x7f)   // Standard ASCII-set 0..0x7F, no conversion
  {
    cPrev = '\0';
    c = ascii;
  }
  else
  {
    switch (cPrev)  // Conversion depending on preceding UTF8-character
    {
    case 0xC2: c = ascii;  break;
    case 0xC3: c = ascii | 0xC0;  break;
    case 0x82: if (ascii==0xAC) c = 0x80; // Euro symbol special case
    }
    cPrev = ascii;   // save last char
  }
  //Debugf("\nConverted 0x%02x", ascii);
  //Debugf(" to 0x%02x", c);

  return(c);
  
} // utf8Ascii(uint8_t)

//===========================================================================================
void utf8Ascii(char* s)
// In place conversion UTF-8 string to Extended ASCII
// The extended ASCII string is always shorter.
{
  uint8_t c;
  char *cp = s;

  //DebugTf("\nConverting: %c", s);

  while (*s != '\0')
  {
    c = utf8Ascii(*s++);
    if (c != '\0')
      *cp++ = c;
  }
  *cp = '\0';   // terminate the new string

} // utf8Ascii(char)


void getRevisionData() 
{
  if (!LittleFS.exists("/newsFiles/LCL-000"))
  {
    char LCL000[100];
    sprintf(LCL000, "ESP_ticker %s (c) by Willem Aandewiel", String(_FW_VERSION).c_str());
    writeFileById("LCL", 0, LCL000);
  }

} //  getRevisionData()

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
