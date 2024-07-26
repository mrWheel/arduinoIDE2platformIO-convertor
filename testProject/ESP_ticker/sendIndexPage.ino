/*
***************************************************************************  
**  Program : sendIndexPage
**
**  Copyright (c) 2021 Willem Aandewiel
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
***************************************************************************      
*/

static const char indexPage[] =
R"(
<!DOCTYPE html>
<html charset="UTF-8">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">  
    <link rel="stylesheet" type="text/css" href="/index.css">
    <script src="/index.js"></script>
    <title>ESP Lichtkrant</title>
  </head>
  <body>
    <font face="Arial">
    <!-- <div class="dev-header"> -->
    <div class="header">
      <h1>
        <span id="sysName">ESP - lichtKrant</span> &nbsp; &nbsp; &nbsp;
        <span id="devName"    style='font-size: small;'>-</span> &nbsp;
        <span id="devVersion" style='font-size: small;'>[version]</span>
        <span id='theTime' class='nav-item nav-clock'>00:00</span>
      </h1>
    </div>
    </font>
    <div id="displayMainPage"      style="display:none">
      <div class="nav-container">
        <div class='nav-left'>
          <a id='saveMsg' class='nav-item tabButton' style="background: lightblue;">opslaan</a>
          <a id='M_FSexplorer'    class='nav-img'>
                      <img src='/FSexplorer.png' alt='FSexplorer'></a>
          <a id='Settings'      class='nav-img'>
                      <img src='/settings.png' alt='Settings'></a>
        </div>
      </div>
      <br/>
      <div id="mainPage">
        <div id="waiting">Wait! retrieving local messages .....</div>
      </div>
    </div>

    <div id="displaySettingsPage"  style="display:none">
      <div class="nav-container">
        <div class='nav-left'>
          <a id='back' class='nav-item tabButton' style="background: lightblue;">Terug</a>
          <a id='saveSettings' class='nav-item tabButton' style="background: lightblue;">opslaan</a>
          <a id='S_FSexplorer' class='nav-img'>
                      <img src='/FSexplorer.png' alt='FSexplorer'></a>
        </div>
      </div>
      <br/>
      <div id="settingsPage"></div>
    </div>
  
    <!-- KEEP THIS --->

    <!-- Pin to bottom right corner -->
    <div class="bottom right-0">2021 &copy; Willem Aandewiel</div>

    <!-- Pin to bottom left corner -->
    <div id="message" class="bottom left-0">-</div>
  
    <script>
       window.onload=bootsTrapMain;
    </script>

  </body>

</html>
)";

void sendIndexPage()
{
  httpServer.send(200, "text/html", indexPage);

} // sendIndexPage()



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
