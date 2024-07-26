/*
***************************************************************************  
**  Program  : settingsStuff, part of ESP_ticker
**
**  Copyright (c) 2021 Willem Aandewiel
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
***************************************************************************      
*/

//=======================================================================
void writeSettings(bool show) 
{
  DebugTf("Writing to [%s] ..\r\n", SETTINGS_FILE);
  File file = LittleFS.open(SETTINGS_FILE, "w"); // open for reading and writing
  if (!file) 
  {
    DebugTf("open(%s, 'w') FAILED!!! --> Bailout\r\n", SETTINGS_FILE);
    return;
  }
  yield();

  DebugT(F("Start writing setting data "));

  file.print("Hostname = ");          file.println(settingHostname);            Debug(F("."));
  file.print("localMaxMsg = ");       file.println(settingLocalMaxMsg);         Debug(F("."));
  file.print("textSpeed = ");         file.println(settingTextSpeed);           Debug(F("."));
  file.print("maxIntensity = ");      file.println(settingMaxIntensity);        Debug(F("."));
  file.print("LDRlowOffset = ");      file.println(settingLDRlowOffset);        Debug(F("."));
  file.print("LDRhighOffset = ");     file.println(settingLDRhighOffset);       Debug(F("."));
  file.print("weerLiveAUTH = ");      file.println(settingWeerLiveAUTH);        Debug(F("."));
  file.print("weerLiveLocatie = ");   file.println(settingWeerLiveLocation);    Debug(F("."));
  file.print("weerLiveInterval = ");  file.println(settingWeerLiveInterval);    Debug(F("."));
  file.print("newsAUTH = ");          file.println(settingNewsAUTH);            Debug(F("."));
  file.print("newsNoWords = ");       file.println(settingNewsNoWords);         Debug(F("."));
  file.print("newsMaxMsg = ");        file.println(settingNewsMaxMsg);          Debug(F("."));
  file.print("newsInterval = ");      file.println(settingNewsInterval);        Debug(F("."));

  file.close();  
  
  Debugln(F(" done"));

  if (show) 
  {
    DebugTln(F("Wrote this:"));
    DebugT(F("        Hostname = ")); Debugln(settingHostname);
    DebugT(F("     newsNoWords = ")); Debugln(settingNewsNoWords);
    DebugT(F("     localMaxMsg = ")); Debugln(settingLocalMaxMsg);     
    DebugT(F("       textSpeed = ")); Debugln(settingTextSpeed);     
    DebugT(F("    LDRlowOffset = ")); Debugln(settingLDRlowOffset);     
    DebugT(F("   LDRhighOffset = ")); Debugln(settingLDRhighOffset);     
    DebugT(F("    maxIntensity = ")); Debugln(settingMaxIntensity);     
    DebugT(F("    weerLiveAUTH = ")); Debugln(settingWeerLiveAUTH);     
    DebugT(F(" weerLiveLocatie = ")); Debugln(settingWeerLiveLocation);     
    DebugT(F("weerLiveInterval = ")); Debugln(settingWeerLiveInterval);     
    DebugT(F("        newsAUTH = ")); Debugln(settingNewsAUTH);     
    DebugT(F("      newsMaxMsg = ")); Debugln(settingNewsMaxMsg);    
    DebugT(F("    newsInterval = ")); Debugln(settingNewsInterval);    

  } // Verbose
  
} // writeSettings()


//=======================================================================
void readSettings(bool show) 
{
  String sTmp;
  String words[10];
  char cTmp[LOCAL_SIZE], cVal[101], cKey[101];
  
  File file;
  
  DebugTf(" %s ..\r\n", SETTINGS_FILE);

  snprintf(settingHostname,    sizeof(settingHostname), "%s", _HOSTNAME);
  snprintf(settingNewsNoWords, sizeof(settingNewsNoWords),"Voetbal, show, UEFA, KNVB");
  settingLocalMaxMsg        =   5;
  settingTextSpeed          =  25;
  settingLDRlowOffset       =  70;
  settingLDRhighOffset      = 700;
  settingMaxIntensity       =   6;
  snprintf(settingWeerLiveAUTH,     50, "");
  snprintf(settingWeerLiveLocation, 50, "");
  settingWeerLiveInterval   =   0;
  snprintf(settingNewsAUTH,         50, "");
  settingNewsMaxMsg         =   4;
  settingNewsInterval       =   0;

  if (!LittleFS.exists(SETTINGS_FILE)) 
  {
    DebugTln(F(" .. file not found! --> created file!"));
    writeSettings(show);
  }

  for (int T = 0; T < 2; T++) 
  {
    file = LittleFS.open(SETTINGS_FILE, "r");
    if (!file) 
    {
      if (T == 0) DebugTf(" .. something went wrong opening [%s]\r\n", SETTINGS_FILE);
      else        DebugT(T);
      delay(100);
    }
  } // try T times ..

  DebugTln(F("Reading settings:\r"));
  while(file.available()) 
  {
    sTmp = file.readStringUntil('\n');
    snprintf(cTmp, sizeof(cTmp), "%s", sTmp.c_str());
    //strTrim(cTmp, sizeof(cTmp), '\r');
    strTrimCntr(cTmp, sizeof(cTmp));
    //DebugTf("cTmp[%s] (%d)\r\n", cTmp, strlen(cTmp));
    int sEq = strIndex(cTmp, "=");
    strCopy(cKey, 100, cTmp, 0, sEq -1);
    strCopy(cVal, 100, cTmp, sEq +1, strlen(cTmp));
    //DebugTf("cKey[%s], cVal[%s]\r\n", cKey, cVal);
    strTrim(cKey, sizeof(cKey), ' ');
    strTrim(cVal, sizeof(cVal), ' ');
    //DebugTf("cKey[%s], cVal[%s]\r\n", cKey, cVal);

    //strToLower(cKey);
    if (stricmp(cKey, "hostname") == 0)         strCopy(settingHostname,         sizeof(settingHostname), cVal);
    if (stricmp(cKey, "localMaxMsg") == 0)      settingLocalMaxMsg      = atoi(cVal);
    if (stricmp(cKey, "textSpeed") == 0)        settingTextSpeed        = atoi(cVal);
    if (stricmp(cKey, "LDRlowOffset") == 0)     settingLDRlowOffset     = atoi(cVal);
    if (stricmp(cKey, "LDRhighOffset") == 0)    settingLDRhighOffset    = atoi(cVal);
    if (stricmp(cKey, "maxIntensity") == 0)     settingMaxIntensity     = atoi(cVal);
    if (stricmp(cKey, "weerLiveAUTH") == 0)     strCopy(settingWeerLiveAUTH,     sizeof(settingWeerLiveAUTH), cVal);
    if (stricmp(cKey, "weerlivelocatie") == 0)  strCopy(settingWeerLiveLocation, sizeof(settingWeerLiveLocation), cVal);
    if (stricmp(cKey, "weerLiveInterval") == 0) settingWeerLiveInterval = atoi(cVal);
    if (stricmp(cKey, "newsAUTH") == 0)         strCopy(settingNewsAUTH,         sizeof(settingNewsAUTH), cVal);
    if (stricmp(cKey, "newsNoWords") == 0)      strCopy(settingNewsNoWords,      sizeof(settingNewsNoWords), cVal);
    if (stricmp(cKey, "newsMaxMsg") == 0)       settingNewsMaxMsg       = atoi(cVal);
    if (stricmp(cKey, "newsInterval") == 0)     settingNewsInterval     = atoi(cVal);

  } // while available()
  
  file.close();  

  //--- this will take some time to settle in
  //--- probably need a reboot before that to happen :-(
  MDNS.setHostname(settingHostname);    // start advertising with new(?) settingHostname
  if (settingLocalMaxMsg > 20)        settingLocalMaxMsg      =   20;
  if (settingLocalMaxMsg <  1)        settingLocalMaxMsg      =    1;
  if (settingTextSpeed > MAX_SPEED)   settingTextSpeed        =  MAX_SPEED;
  if (settingTextSpeed < 10)          settingTextSpeed        =   10;
  if (settingLDRlowOffset  >  500)    settingLDRlowOffset     =  500;
  if (settingLDRlowOffset  <    1)    settingLDRlowOffset     =    0;
  if (settingLDRhighOffset <  500)    settingLDRhighOffset    =  500;
  if (settingLDRhighOffset > 1024)    settingLDRhighOffset    = 1024;
  if (settingMaxIntensity > 15)       settingMaxIntensity     =   15;
  if (settingMaxIntensity <  1)       settingMaxIntensity     =    1;
  if (strlen(settingWeerLiveLocation) <  1)  sprintf(settingWeerLiveLocation, "Amsterdam");
  if (settingWeerLiveInterval ==  0) 
  {
    settingWeerLiveInterval =    0;  // geen weerberichten
  }
  else
  {
    if (settingWeerLiveInterval > 120)  settingWeerLiveInterval =  120;  // minuten!
    if (settingWeerLiveInterval <  15)  settingWeerLiveInterval =   15;
  }
  if (settingNewsMaxMsg > 20)         settingNewsMaxMsg       =   20;
  if (settingNewsMaxMsg <  1)         settingNewsMaxMsg       =    1;
  if (settingNewsInterval > 120)      settingNewsInterval     =  120;
  if (settingNewsInterval ==  0) 
  {
    settingNewsInterval  =    0; // geen nieuwsberichten
  }
  else
  {
    if (settingNewsInterval <  15)    settingNewsInterval     =   15;
  }

  DebugTln(F(" .. done\r"));

  if (!show) return;
  
  Debugln(F("\r\n==== read Settings ===================================================\r"));
  Debugf("                 Hostname : %s\r\n",  settingHostname);
  Debugf("           local Max. Msg : %d\r\n",  settingLocalMaxMsg);
  Debugf("               text Speed : %d\r\n",  settingTextSpeed);
  Debugf("           LDR low offset : %d\r\n",  settingLDRlowOffset);
  Debugf("          LDR high offset : %d\r\n",  settingLDRhighOffset);
  Debugf("            max Intensity : %d\r\n",  settingMaxIntensity);
  Debugf("         WeerLive.nl AUTH : %s\r\n",  settingWeerLiveAUTH);
  Debugf("      WeerLive.nl Locatie : %s\r\n",  settingWeerLiveLocation);
  Debugf("     WeerLive.nl Interval : %d\r\n",  settingWeerLiveInterval);
  Debugf("         newsapi.org AUTH : %s\r\n",  settingNewsAUTH);
  Debugf("      newsapi.org NoWords : %s\r\n",  settingNewsNoWords);
  Debugf("     newsapi.org Max. Msg : %d\r\n",  settingNewsMaxMsg);
  Debugf("     newsapi.org Interval : %d\r\n",  settingNewsInterval);
  
  Debugln(F("-\r"));

} // readSettings()


//=======================================================================
void updateSetting(const char *field, const char *newValue)
{
  DebugTf("-> field[%s], newValue[%s]\r\n", field, newValue);

  if (!stricmp(field, "Hostname")) {
    strCopy(settingHostname, sizeof(settingHostname), newValue); 
    if (strlen(settingHostname) < 1) strCopy(settingHostname, sizeof(settingHostname), _HOSTNAME); 
    char *dotPntr = strchr(settingHostname, '.') ;
    if (dotPntr != NULL)
    {
      byte dotPos = (dotPntr-settingHostname);
      if (dotPos > 0)  settingHostname[dotPos] = '\0';
    }
    Debugln();
    DebugTf("Need reboot before new %s.local will be available!\r\n\n", settingHostname);
  }
  if (!stricmp(field, "localMaxMsg"))      settingLocalMaxMsg   = String(newValue).toInt();  
  if (!stricmp(field, "textSpeed"))        settingTextSpeed     = String(newValue).toInt();  
  if (!stricmp(field, "LDRlowOffset"))     settingLDRlowOffset  = String(newValue).toInt();  
  if (!stricmp(field, "LDRhighOffset"))    settingLDRhighOffset = String(newValue).toInt();  
  if (!stricmp(field, "maxIntensity"))     settingMaxIntensity  = String(newValue).toInt();  

  if (!stricmp(field, "weerLiveAUTH"))     strCopy(settingWeerLiveAUTH, sizeof(settingWeerLiveAUTH), newValue);   
  if (!stricmp(field, "weerLiveLocation")) strCopy(settingWeerLiveLocation, sizeof(settingWeerLiveLocation), newValue);
  if (!stricmp(field, "weerLiveInterval")) settingWeerLiveInterval  = String(newValue).toInt();  
  
  if (!stricmp(field, "newsapiAUTH"))      strCopy(settingNewsAUTH, sizeof(settingNewsAUTH), newValue);   
  if (!stricmp(field, "newsNoWords"))      strCopy(settingNewsNoWords, sizeof(settingNewsNoWords), newValue);   
  if (!stricmp(field, "newsapiMaxMsg"))    settingNewsMaxMsg   = String(newValue).toInt();
  if (!stricmp(field, "newsapiInterval"))  settingNewsInterval = String(newValue).toInt();

  writeSettings(false);

  if (settingWeerLiveInterval == 0)      memset(tempMessage, 0, sizeof(tempMessage));
  else if (settingWeerLiveInterval < 15) settingWeerLiveInterval = 15;
  if (settingNewsInterval == 0)          removeNewsData();
  else if (settingNewsInterval < 15)     settingNewsInterval = 15;
  //--- rebuild noWords array --
  splitNewsNoWords(settingNewsNoWords);
  
} // updateSetting()


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
