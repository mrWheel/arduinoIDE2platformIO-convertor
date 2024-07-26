/*
***************************************************************************  
**  Program : weerlive_nl
**
**  Copyright (c) 2021 .. 2023 Willem Aandewiel
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
***************************************************************************      
*/

void getWeerLiveData() 
{
  const char* weerliveHost    = "weerlive.nl";
  const int   httpPort        = 80;
  int         weerliveStatus  = 0;
  String      tempString;
  int         startPos, endPos;
  int32_t     maxWait;
  char        jsonResponse[1536];
  char        val[51] = "";
  bool        gotData = false;
  
  WiFiClient weerliveClient;

  DebugTf("getWeerLiveData(%s)\r\n", weerliveHost);

  // We now create a URI for the request
  String url = "/api/json-data-10min.php?key=";
  url += settingWeerLiveAUTH;
  url += "&locatie=";
  url += settingWeerLiveLocation;

  DebugTf("Requesting URL: %s/api/json-data-10min.php?key=secret&locatie=%s\r\n", weerliveHost, settingWeerLiveLocation);
  Debugln(url);
  if (!weerliveClient.connect(weerliveHost, httpPort)) 
  {
    DebugTln("connection failed");
    sprintf(tempMessage, "connection to %s failed", weerliveHost);
    weerliveClient.flush();
    weerliveClient.stop();
    return;
  }

  // This will send the request to the server
  weerliveClient.print(String("GET ") + url + " HTTP/1.1\r\n" +
               "Host: " + weerliveHost + "\r\n" + 
               "Connection: close\r\n\r\n");
  delay(10);
  
  weerliveClient.setTimeout(5000);

  while ((weerliveClient.connected() || weerliveClient.available()) && !gotData)
  {
    yield();
    while(weerliveClient.available() && !gotData)
    {
      //--- skip to find HTTP/1.1
      //--- then parse response code
      if (weerliveClient.find("HTTP/1.1"))
      {
        weerliveStatus = weerliveClient.parseInt(); // parse status code
        DebugTf("Statuscode: [%d] ", weerliveStatus); 
        if (weerliveStatus != 200)
        {
          Debugln(" ERROR!");
          weerliveClient.flush();
          weerliveClient.stop();
          return;  
        }
        Debugln(" OK!");
      }
      else
      {
        DebugTln("Error reading weerLive.. -> bailout!");
        weerliveClient.flush();
        weerliveClient.stop();
        return;
      }
      //--- skip headers
      if (weerliveClient.find("\r\n\r\n"))
      {
        int charsRead = 0;
        charsRead = weerliveClient.readBytesUntil('\0',  jsonResponse, sizeof(jsonResponse));
        jsonResponse[(charsRead -1)] = '\0';
        gotData = true;
        DebugTln("Got weer data!");
      }
    } // while available ..
    
  } // connected ..

  weerliveClient.flush();
  weerliveClient.stop();
  //-- jsonResponse looks like:
  //-- { "liveweer": [{"plaats": "Baarn", "timestamp": "1683105785", "time": "03-05-2023 11:23", "temp": "10.4", "gtemp": "8.8", "samenv": "Licht bewolkt", "lv": "56", "windr": "NO", "windrgr": "44", "windms": "3", "winds": "2", "windk": "5.8", "windkmh": "10.8", "luchtd": "1029.4", "ldmmhg": "772", "dauwp": "2", "zicht": "35", "verw": "Zonnig en droog, donderdag warmer", "sup": "06:03", "sunder": "21:08", "image": "lichtbewolkt", "d0weer": "halfbewolkt", "d0tmax": "15", "d0tmin": "3", "d0windk": "2", "d0windknp": "6", "d0windms": "3", "d0windkmh": "11", "d0windr": "NO", "d0windrgr": "44", "d0neerslag": "0", "d0zon": "35", "d1weer": "halfbewolkt", "d1tmax": "20", "d1tmin": "5", "d1windk": "2", "d1windknp": "6", "d1windms": "3", "d1windkmh": "11", "d1windr": "O", "d1windrgr": "90", "d1neerslag": "20", "d1zon": "60", "d2weer": "regen", "d2tmax": "19", "d2tmin": "12", "d2windk": "2", "d2windknp": "6", "d2windms": "3", "d2windkmh": "11", "d2windr": "ZW", "d2windrgr": "225", "d2neerslag": "80", "d2zon": "30", "alarm": "0", "alarmtxt": ""}]}
  
  int prevLength = strlen(jsonResponse);
  strTrimCntr(jsonResponse, 1534);
  DebugTf("jsonResponse now [%d]chars (before trim [%d]chars)\r\n", strlen(jsonResponse), prevLength);
  DebugTf("jsonResponse is [%s]\r\n\n", jsonResponse);
  
  parseJsonKey(jsonResponse, "plaats", val, 50);
  snprintf(tempMessage, LOCAL_SIZE, val);
  parseJsonKey(jsonResponse, "samenv", val, 50);
  snprintf(cMsg, LOCAL_SIZE, " %s %s ", tempMessage, val);
  parseJsonKey(jsonResponse, "d0tmin", val, 50);
  snprintf(tempMessage, LOCAL_SIZE, "%s min %s°C ", cMsg, val);
  parseJsonKey(jsonResponse, "d0tmax", val, 50);
  snprintf(cMsg, LOCAL_SIZE, "%s max %s°C", tempMessage, val);
  parseJsonKey(jsonResponse, "luchtd", val, 50);
  snprintf(tempMessage, LOCAL_SIZE, "%s - luchtdruk %s hPa ", cMsg, val);

  parseJsonKey(jsonResponse, "d1weer", val, 50);
  snprintf(cMsg, LOCAL_SIZE, "%s - morgen %s ", tempMessage, val);
  parseJsonKey(jsonResponse, "d1tmin", val, 50);
  snprintf(tempMessage, LOCAL_SIZE, "%s min %s°C ", cMsg, val);
  parseJsonKey(jsonResponse, "d1tmax", val, 50);
  snprintf(cMsg, LOCAL_SIZE, "%s max %s°C", tempMessage, val);

  snprintf(tempMessage, LOCAL_SIZE, "%s", cMsg);
  Debugln("\r\n");
  Debugf("\tWeer[%s]\r\n", tempMessage);
  
} // getWeerLiveData()


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
