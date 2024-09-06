/*
***************************************************************************  
**  Program : newsapi_org
**
**  Copyright (c) 2021 .. 2023 Willem Aandewiel
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
***************************************************************************      
*/

//-- http://newsapi.org/v2/top-headlines?country=nl&apiKey=API_KEY

//----------------------------------------------------------------------
bool getNewsapiData() 
{
  const char* newsapiHost    = "newsapi.org";
  const int   httpPort       = 80;
  int         newsapiStatus  = 0;
  char        newsMessage[NEWS_SIZE] = {};
  int         startPos, endPos;
  int32_t     maxWait;
  char        jsonResponse[1024];
  char        val[51] = "";
  
  WiFiClient newsapiClient;

  Debugln();
  DebugTf("getNewsapiData(%s)\r\n", newsapiHost);

  // We now create a URI for the request
  String url = "/v2/top-headlines?country=nl&apiKey=";
  url += settingNewsAUTH;

  DebugTf("Requesting URL: %s/v2/top-headlines?country=nl&apiKey=secret\r\n", newsapiHost);
  DebugFlush();
  //Debugln("\r\n=======================================");
  //DebugFlush();
  //Debug(newsapiHost);
  //Debugln(url);
  //Debugln("=======================================");
  
  if (!newsapiClient.connect(newsapiHost, httpPort)) 
  {
    DebugTln("connection failed");
    sprintf(tempMessage, "connection to %s failed", newsapiHost);
    //-- empty newsMessage store --
    for(int i=0; i<=settingNewsMaxMsg; i++)
    {
      //sprintf(newsMessage, "");
      if (i==1) writeFileById("NWS", i, "There is No News ....");
      else      writeFileById("NWS", i, "");
    }
    
    newsapiClient.flush();
    newsapiClient.stop();
    return false;
  }

  // This will send the request to the server
  newsapiClient.print(String("GET ") + url + " HTTP/1.1\r\n" +
               "Host: " + newsapiHost + "\r\n" + 
               "User-Agent: ESP-ticker\r\n" + 
               "Connection: close\r\n\r\n");
  delay(10);
  
  newsapiClient.setTimeout(5000);
  while (newsapiClient.connected() || newsapiClient.available())
  {
    yield();
    while(newsapiClient.available())
    {
      Debugln();
      //--- skip to find HTTP/1.1
      //--- then parse response code
      if (newsapiClient.find("HTTP/1.1"))
      {
        newsapiStatus = newsapiClient.parseInt(); // parse status code
        DebugTf("Statuscode: [%d] ", newsapiStatus); 
        if (newsapiStatus != 200)
        {
          Debugln(" ERROR!");
          while(newsapiClient.available())
          {
            char nC = newsapiClient.read();
            Debug(nC);
          }
          Debugln();
          newsapiClient.flush();
          newsapiClient.stop();
          for(int i=0; i<=settingNewsMaxMsg; i++)
          {
            //sprintf(newsMessage, "");
            if (i==1) writeFileById("NWS", i, "There is No News ....");
            else      writeFileById("NWS", i, "");
          }
          newsapiClient.flush();
          newsapiClient.stop();
          return false;  
        }
        Debugln(" OK!");
      }
      else
      {
        DebugTln("Error reading newsapi.org.. -> bailout!");
        for(int i=0; i<=settingNewsMaxMsg; i++)
        {
          //sprintf(newsMessage, "");
          if (i==1) writeFileById("NWS", i, "There is No News ....");
          else      writeFileById("NWS", i, "");
        }
        newsapiClient.flush();
        newsapiClient.stop();
        return false;
      }
      //--- skip headers
      uint16_t  msgIdx  = 0;
      int       msgNr   = 0;
      while (newsapiClient.find("\"title\":\""))
      {
        for (int i=0; i<NEWS_SIZE; i++) newsMessage[i] = 0;
        msgIdx          = 0;
        while( (strIndex(newsMessage, "\"description\":") == -1) && (msgIdx < (NEWS_SIZE - 2)) )
        {
          newsMessage[msgIdx++] = (char)newsapiClient.read();
        }
        newsMessage[msgIdx] = '\0';
        if (msgIdx > 30)  newsMessage[msgIdx - 16] = 0;
        Debugf("\t[%2d] %s\r\n", msgNr, newsMessage);
        if (!hasNoNoWord(newsMessage) && strlen(newsMessage) > 15)
        {
          if (msgNr <= settingNewsMaxMsg)
          {
            writeFileById("NWS", msgNr, newsMessage);
          }
          msgNr++;
        }
      } // while find(title)
    } // while available ..
    
  } // connected ..

  newsapiClient.flush();
  newsapiClient.stop();
  updateMessage("0", "News brought to you by 'newsapi.org'");

  return true;

} // getNewsapiData()


//----------------------------------------------------------------------
void removeNewsData()
{
  char nwsName[15];

  for(int n=0; n<=settingNewsMaxMsg; n++)
  {
    sprintf(nwsName, "/newsFiles/NWS-%03d", n);
    DebugTf("Remove [%s] from LittleFS ..\r\n", nwsName);
    LittleFS.remove(nwsName);
  }

} //  removeNewsData()

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
