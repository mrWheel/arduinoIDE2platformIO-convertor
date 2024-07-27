/* 
***************************************************************************  
**  Program  : ESP_ticker.h, part of ESP_ticker
**
**  Copyright (c) 2021 Willem Aandewiel
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
***************************************************************************      
*/

#include <LittleFS.h>

#include "TimeSyncClass.h"

#include <TelnetStream.h>       // https://github.com/jandrassy/TelnetStream/commit/1294a9ee5cc9b1f7e51005091e351d60c8cddecf
#include "Debug.h"
#include "networkStuff.h"

#include <MD_Parola.h>
#include <MD_MAX72xx.h>
#include "parola_Fonts_data.h"
#include <SPI.h>

// Define the number of devices we have in the chain and the hardware interface
// NOTE: These pin numbers are for ESP8266 hardware SPI and will probably not
// work with your hardware and may need to be adapted
//#define HARDWARE_TYPE MD_MAX72XX::PAROLA_HW
#define HARDWARE_TYPE MD_MAX72XX::FC16_HW
//#define HARDWARE_TYPE MD_MAX72XX::GENERIC_HW
#define MAX_DEVICES  8
#define MAX_SPEED   50

//#define CLK_PIN   14 // or SCK
//#define DATA_PIN  13 // or MOSI
#define CS_PIN      15 // or SS

#define SETTINGS_FILE   "/settings.ini"
#define LOCAL_SIZE      255
#define NEWS_SIZE       512
#define JSON_BUFF_MAX   255
#define MAX_NO_NO_WORDS  20

bool      Verbose = false;
char      cDate[15], cTime[10];
uint32_t  nrReboots;
// Global message buffers shared by Wifi and Scrolling functions
char      cMsg[NEWS_SIZE];
char      tempMessage[LOCAL_SIZE] = "";
uint8_t   msgType;
char      actMessage[NEWS_SIZE], timeMsg[20];
char      onTickerMessage[LOCAL_SIZE] = {};
char      fileMessage[LOCAL_SIZE];
uint8_t   newsMsgID   = 0;
uint8_t   localMsgID  = 0;
int16_t   valueLDR, valueIntensity;
char      fChar[10];
String    lastReset   = "";
uint32_t  timeTimer   = 0;
uint32_t  ntpTimer    = millis() + 30000;
uint32_t  weerTimer   = 0;
uint32_t  newsapiTimer = 0;
uint32_t  revisionTimer = 0;
String    noWords[MAX_NO_NO_WORDS+1];
char      settingHostname[41];
char      settingNewsNoWords[LOCAL_SIZE];
uint8_t   settingLocalMaxMsg, settingTextSpeed, settingMaxIntensity;
uint16_t  settingLDRlowOffset, settingLDRhighOffset;
char      settingWeerLiveAUTH[51], settingWeerLiveLocation[51];
uint8_t   settingWeerLiveInterval;
char      settingNewsAUTH[51];
uint8_t   settingNewsInterval, settingNewsMaxMsg;
time_t    now; 
struct tm timeinfo;
bool      timeSynced = false;


TimeSync        timeSync;

const char *weekDayName[]  {  "Unknown", "Zondag", "Maandag", "Dinsdag", "Woensdag"
                            , "Donderdag", "Vrijdag", "Zaterdag", "Unknown" };
const char *flashMode[]    { "QIO", "QOUT", "DIO", "DOUT", "Unknown" };


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
