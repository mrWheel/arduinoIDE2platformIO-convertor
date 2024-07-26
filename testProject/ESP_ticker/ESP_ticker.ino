/*
***************************************************************************  
**  Program  : ESP_ticker (lichtkrant)
*/
#define _FW_VERSION "v1.7.3 (04-05-2023)"
/* 
**  Copyright (c) 2021 .. 2023 Willem Aandewiel
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
***************************************************************************      

    Arduino-IDE settings for ESP-12E:

    - Board: "Generic ESP8266 Module" (ALLWAYS!!!!!)
    - Buildin Led: "2"
    - Upload Speed: "115200"
    - CPU Frequency: "80 MHz" (or if you need the speed: 160MHz)
    - Flash size: "4MB (FS:2M OTA~1019KB)"
    - Flash mode: "DIO" / "DOUT"
    - Flash Frequency: "40MHz"
    - Reset Method: "nodemcu" or something else
    - Debug port: "Disabled"
    - Debug Level: "None"
    - IwIP Variant: "v2 Lower Memory"
    - VTables: "Flash"
    - Exceptions: "Legacy (new can return nullptr)"
    - Erase Flash: "Only Sketch"
    - Espressif FW: "nonos-sdk 2.2.1+100 (190703)"
    - SSL Support: "All SSL ciphers (most compatible)"
    - Port: "ESPticker at <-- IP address -->"

    Arduino ESP8266 core v2.7.+
*/


// Use the Parola library to scroll text on the display
// IP address for the ESP8266 is displayed on the scrolling display
// after startup initialisation and connected to the WiFi network.
//
// Connections for ESP8266 hardware SPI are:
// Vcc       3v3     LED matrices seem to work at 3.3V
// GND       GND     GND
// DIN        D7     HSPID or HMOSI
// CS or LD   D8     HSPICS or HCS
// CLK        D5     CLK or HCLK
//
// MD_MAX72XX library can be found at https://github.com/MajicDesigns/MD_MAX72XX
//

#define USE_UPDATE_SERVER

#define _HOSTNAME   "ESPticker"
#include "ESP_ticker.h"

// HARDWARE SPI
MD_Parola P = MD_Parola(HARDWARE_TYPE, CS_PIN, MAX_DEVICES);

// WiFi Server object and parameters
WiFiServer server(80);

// Scrolling parameters

uint8_t  inFX, outFX;
textEffect_t  effect[] =
  {
    PA_PRINT,
  //PA_SCAN_HORIZ,
    PA_SCROLL_LEFT,
    PA_WIPE,
    PA_SCROLL_UP_LEFT,
    PA_SCROLL_UP,
    PA_OPENING_CURSOR,
    PA_GROW_UP,
    PA_MESH,
    PA_SCROLL_UP_RIGHT,
  //PA_BLINDS,
    PA_CLOSING,
    PA_RANDOM,
    PA_GROW_DOWN,
    PA_SCAN_VERT,
    PA_SCROLL_DOWN_LEFT,
    PA_WIPE_CURSOR,
  //PA_DISSOLVE,
    PA_OPENING,
    PA_CLOSING_CURSOR,
    PA_SCROLL_DOWN_RIGHT,
    PA_SCROLL_RIGHT,
  //PA_SLICE,
    PA_SCROLL_DOWN,
  };


//---------------------------------------------------------------------
int16_t calculateIntensity()
{
  int a0In = 0;
  for (int l=0; l<2; l++)
  {
    //--- read analog A0
    a0In+= analogRead(A0);
    delay(200);
  }
  a0In = a0In / 2;  //-- smooth things up a bit
  
  DebugTf("analogRead[%d], ", a0In);
  //---test if (a0In < settingLDRlowOffset) a0In = settingLDRlowOffset;
  Debugf(" LDRlowOffset[%d] LDRhighOffset[%d] ", settingLDRlowOffset, settingLDRhighOffset);
  valueLDR = (valueLDR + a0In) / 2;
  if (valueLDR < settingLDRlowOffset)   valueLDR = settingLDRlowOffset;
  if (valueLDR > settingLDRhighOffset)  valueLDR = settingLDRhighOffset;
  Debugf(" ==> valueLDR[%d]\r\n", valueLDR);

  //--- map LDR to offset..1024 -> 0..settingMax
  int intensity = map(valueLDR, settingLDRlowOffset, settingLDRhighOffset,  0, settingMaxIntensity);
  //DebugTf("map(%d, %d, %d, 0, %d) => [%d]\r\n", valueLDR, settingLDRlowOffset, settingLDRhighOffset
  //                                                      , 0                  , settingMaxIntensity);


/*
  if ( ((minute() % 15) == 0) && (lastMinute != minute()) ) 
  {
    lastHour = hour();
    lastMinute = minute();
    char line[50];
    snprintf(line, sizeof(line), "valueLDR[%4d] intensity[%2d]", valueLDR, intensity);
    writeToLog(line);
  }
*/
  
  return intensity;

} // calculateIntensity()


//---------------------------------------------------------------------
char *updateTime()
{
  snprintf(timeMsg, 20, "%02d : %02d", hour(), minute()); 
  return timeMsg;

} // updateTime()


//---------------------------------------------------------------------
void splitNewsNoWords(const char *noNo)
{
  DebugTln(noNo);
  int8_t wc = splitString(String(noNo), ' ', noWords, MAX_NO_NO_WORDS);
  for(int8_t i=0; i<wc; i++)
  {
    noWords[i].trim();
    if (noWords[i].length() > 1)
    {
      noWords[i].toLowerCase();
      DebugTf("NoNoWord[%d] [%s]\r\n", i, noWords[i].c_str());
    }
  }
  
} // splitNewsNoWords()

//---------------------------------------------------------------------
bool hasNoNoWord(const char *cIn)
{
  for(int8_t i=0; i<MAX_NO_NO_WORDS; i++)
  {
    String sIn = String(cIn);
    sIn.toLowerCase();
    int idx = sIn.indexOf(noWords[i]);
    if ((idx > -1) && (noWords[i].length() > 1))  // yes! it's in there somewhere
    {
      DebugTf("found [%s]\r\n", noWords[i].c_str());
      return true;      
    }
  }
  //DebugTln("no NoNo words found!");
  return false;
  
} // hasNoNoWord()


//---------------------------------------------------------------------
void nextNieuwsBericht()
{
  bool breakOut  = false;
  newsMsgID++;
  if (newsMsgID >= settingNewsMaxMsg) newsMsgID = 0;
  while (!readFileById("NWS", newsMsgID))
  {
    DebugTln("File not found!");
    newsMsgID++;
    if (newsMsgID > settingNewsMaxMsg) 
    {
      newsMsgID = 0;
      breakOut  = true;
      break;
    }
  }
  if (!breakOut)
  {
    snprintf(actMessage, NEWS_SIZE, "** %s **", fileMessage);
    //DebugTf("newsMsgID[%d] %s\r\n", newsMsgID, actMessage);
    utf8Ascii(actMessage);
    P.displayScroll(actMessage, PA_LEFT, PA_SCROLL_LEFT, (MAX_SPEED - settingTextSpeed));
  }
  
} // nextNieuwsBericht()


//---------------------------------------------------------------------
void nextLocalBericht()
{
  bool nothingThere = false;
  
  localMsgID++;
  if (localMsgID > settingLocalMaxMsg) 
  {
    localMsgID    = 0;
    nothingThere  = true;
  }
  while (!readFileById("LCL", localMsgID))
  {
    DebugTf("File [/newsFiles/LCL-%03d] not found!\r\n", localMsgID);
    localMsgID++;
    if (localMsgID > settingLocalMaxMsg) 
    {
      DebugTln("Back to LCL-000, exit while-loop");
      localMsgID = 0;
      continue;
    }
  }
  if (nothingThere && (localMsgID == 0)) 
  { 
    nothingThere = true;
    getRevisionData();
  }
  else  nothingThere = false;

  snprintf(actMessage, LOCAL_SIZE, "** %s **", fileMessage);
  //DebugTf("localMsgID[%d] %s\r\n", localMsgID, actMessage);
  utf8Ascii(actMessage);
  P.displayScroll(actMessage, PA_LEFT, PA_SCROLL_LEFT, (MAX_SPEED - settingTextSpeed));
    
  if ((millis() - revisionTimer) > 900000)
  {
    revisionTimer = millis();
    getRevisionData();
  }

} // nextLocalBericht()


//=====================================================================
void setup()
{
  Serial.begin(115200);
  while(!Serial) { /* wait a bit */ }

  lastReset     = ESP.getResetReason();

  startTelnet();
  
  DebugTln("\r\n[MD_Parola WiFi Message Display]\r\n");
  DebugTf("Booting....[%s]\r\n\r\n", String(_FW_VERSION).c_str());
  
  P.begin();
  P.displayClear();
  P.displaySuspend(false);
  P.displayScroll(actMessage, PA_LEFT, PA_SCROLL_LEFT, (MAX_SPEED - settingTextSpeed));

  actMessage[0]  = '\0';
  
//================ LittleFS ===========================================
  if (LittleFS.begin()) 
  {
    DebugTln(F("LittleFS Mount succesfull\r"));
    LittleFSmounted = true;
       
    readSettings(true);
    splitNewsNoWords(settingNewsNoWords);

    if (settingNewsInterval == 0)
    {
      removeNewsData();
    }
    else
    {
      if (!LittleFS.exists("/newsFiles/LCL-000"))
      {
        char LCL000[100];
        sprintf(LCL000, "ESP_ticker %s by Willem Aandewiel", String(_FW_VERSION).c_str());
        writeFileById("LCL", 0, LCL000);
      }
      if (!LittleFS.exists("/newsFiles/LCL-001"))
      {
        char LCL001[100];
        sprintf(LCL001, "ESP_ticker %s by Willem Aandewiel", String(_FW_VERSION).c_str());
        writeFileById("LCL", 1, LCL001);
      }
      writeFileById("NWS", 1, "(c) 2021 Willem Aandewiel");
    }
  } 
  else 
  { 
    DebugTln(F("LittleFS Mount failed\r"));   // Serious problem with LittleFS 
    LittleFSmounted = false;
  }
  //==========================================================//
  // writeLastStatus();  // only for firsttime initialization //
  //==========================================================//
  readLastStatus(); // place it in actTimestamp

  // attempt to connect to Wifi network:
  int t = 0;
  while ((WiFi.status() != WL_CONNECTED) && (t < 25))
  {
    delay(500);
    Serial.print(".");
    t++;
  }
  if ( WiFi.status() != WL_CONNECTED) {
    DebugTln("Attempting to connect to WiFi network\r");
    sprintf(actMessage, "Connect to AP '%s' and configure WiFi on  192.168.4.1   ", _HOSTNAME);
    P.setTextEffect(PA_SCROLL_LEFT, PA_NO_EFFECT);
    do { yield(); } while( !P.displayAnimate() );
    //P.print("   192.168.4.1");
  }
  // Connect to and initialise WiFi network
  digitalWrite(LED_BUILTIN, HIGH);
  startWiFi(_HOSTNAME, 240);  // timeout 4 minuten
  digitalWrite(LED_BUILTIN, LOW);

  startMDNS(settingHostname);
    
  //--- ezTime initialisation
  setDebug(INFO);  
  waitForSync(); 
  CET.setLocation(F("Europe/Amsterdam"));
  CET.setDefault(); 
  
  DebugTln("UTC time: "+ UTC.dateTime());
  DebugTln("CET time: "+ CET.dateTime());

  nrReboots++;
  writeLastStatus();
  //writeToLog("=========REBOOT==========================");

  snprintf(cMsg, sizeof(cMsg), "Last reset reason: [%s]", ESP.getResetReason().c_str());
  DebugTln(cMsg);
  //writeToLog(cMsg);

  Serial.print("\nGebruik 'telnet ");
  Serial.print (WiFi.localIP());
  Serial.println("' voor verdere debugging\r\n");

//================ Start HTTP Server ================================
  setupFSexplorer();
  httpServer.serveStatic("/FSexplorer.png",   LittleFS, "/FSexplorer.png");
  httpServer.on("/",          sendIndexPage);
  httpServer.on("/index",     sendIndexPage);
  httpServer.on("/index.html",sendIndexPage);
  httpServer.serveStatic("/index.css", LittleFS, "/index.css");
  httpServer.serveStatic("/index.js",  LittleFS, "/index.js");
  // all other api calls are catched in FSexplorer onNotFounD!
  httpServer.on("/api", HTTP_GET, processAPI);


  httpServer.begin();
  DebugTln("\nServer started\r");
  
  // Set up first message as the IP address
  sprintf(actMessage, "%03d.%03d.%d.%d", WiFi.localIP()[0], WiFi.localIP()[1], WiFi.localIP()[2], WiFi.localIP()[3]);
  DebugTf("\nAssigned IP[%s]\r\n", actMessage);
  P.displayScroll(actMessage, PA_LEFT, PA_NO_EFFECT, (MAX_SPEED - settingTextSpeed));
  P.setTextEffect(PA_SCROLL_LEFT, PA_NO_EFFECT);
  
  valueIntensity = calculateIntensity(); // read analog input pin 0

  P.setIntensity(valueIntensity);
  newsMsgID = 0;
  do { yield(); } while( !P.displayAnimate() );

  P.setFont(ExtASCII);

  inFX = 0;
  outFX= 0;

  for (int i=0; i<=settingNewsMaxMsg; i++)
  {
    writeFileById("NWS", i, "");
    //DebugTf("readFileById(NWS, %d)\r\n", i);
    //readFileById("NWS", i);
  }
  
} // setup()


//=====================================================================
void loop()
{
//handleNTP();
  events(); // trigger ezTime update etc.
  httpServer.handleClient();
  MDNS.update();
  yield();
  
  if ((millis() > weerTimer) && (strlen(settingWeerLiveAUTH) > 5))
  {
    weerTimer = millis() + (settingWeerLiveInterval * (60 * 1000)); // Interval in Minutes!
    if (settingWeerLiveInterval > 0)  getWeerLiveData();
  }

  if ((millis() > newsapiTimer) && (strlen(settingNewsAUTH) > 5))
  {
    newsapiTimer = millis() + (settingNewsInterval * (60 * 1000)); // Interval in Minutes!
    if (settingNewsInterval > 0) 
    {
      if (!getNewsapiData())  //-- first try ...
      {
        delay(100);
        if (!getNewsapiData())  //-- second try ...
        {
          //-- try again in two(2) minutes ...
          newsapiTimer = millis() + (2 * (60 * 1000)); // Interval in Minutes!
        }
      }
    }
  }

  if (P.displayAnimate()) // done with animation, ready for next message
  {
    yield();
    msgType++;
    DebugTf("msgType[%d]\r\n", msgType);
    
    switch(msgType)
    {
      case 1:   if (!(millis() > timeTimer))  return;
                inFX  = random(0, ARRAY_SIZE(effect));
                outFX = random(0, ARRAY_SIZE(effect));
                snprintf(actMessage, LOCAL_SIZE, weekDayName[weekday()]);
                P.displayText(actMessage, PA_CENTER, (MAX_SPEED - settingTextSpeed), 1000, effect[inFX], effect[outFX]);
                DebugTf("Animate IN[%d], OUT[%d] %s\r\n", inFX, outFX, actMessage);
                break;
      case 2:   if (!(millis() > timeTimer))  return;
                timeTimer = millis() + 60000;
                inFX  = random(0, ARRAY_SIZE(effect));
                outFX = random(0, ARRAY_SIZE(effect));
                sprintf(actMessage, "%s", updateTime());
                P.displayText(actMessage, PA_CENTER, (MAX_SPEED - settingTextSpeed), 2000, effect[inFX], effect[outFX]);
                DebugTf("Animate IN[%d], OUT[%d] %s\r\n", inFX, outFX, actMessage);
                break;
      case 3:   nextLocalBericht();
                P.setTextEffect(PA_SCROLL_LEFT, PA_NO_EFFECT);
                break;          
      case 6:   nextLocalBericht();
                P.setTextEffect(PA_SCROLL_LEFT, PA_NO_EFFECT);
                break;    
      case 4:            
      case 5:            
      case 7:            
      case 8:   if (settingNewsInterval > 0)
                      nextNieuwsBericht();
                else  nextLocalBericht();
                P.setTextEffect(PA_SCROLL_LEFT, PA_NO_EFFECT);
                break;
      case 9:   if (settingWeerLiveInterval > 0)
                {
                  snprintf(actMessage, LOCAL_SIZE, "** %s **", tempMessage);
                  Debugf("\t[%s]\r\n", actMessage);
                  utf8Ascii(actMessage);
                }
                else  nextLocalBericht();
                P.setTextEffect(PA_SCROLL_LEFT, PA_NO_EFFECT);
                break;
      case 10:  if (settingNewsInterval > 0)
                      nextNieuwsBericht();
                else  nextLocalBericht();
                break;
      default:  msgType = 0;
                return;
                
    } // switch()

    //DebugTln(actMessage);
    valueIntensity = calculateIntensity(); // read analog input pin 0
    DebugTf("Intensity set to [%d]\r\n", valueIntensity);
    P.setIntensity(valueIntensity);
    // Tell Parola we have a new animation
    P.displayReset();
    DebugTln("End of displayAnimate()..");
    
  } // dislayAnimate()

  
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
