/*
***************************************************************************  
**  Program : updateServerHtml.h
**
**  Copyright (c) 2021 Willem Aandewiel
**
**  TERMS OF USE: MIT License. See bottom of file.                                                            
***************************************************************************      
*/

static const char UpdateServerIndex[] PROGMEM =
  R"(<html charset="UTF-8">
     <style type='text/css'>
        body {background-color: lightblue;}
     </style>
     <body>
     <h1>ESP - lichtKrant Flash utility</h1>
     <form method='POST' action='?cmd=0' enctype='multipart/form-data'>
          Selecteer een "<b>.ino.bin</b>" bestand<br/>
          <input type='file' accept='ino.bin' name='firmware'>
          <input type='submit' value='Flash Firmware'>
      </form>
      <form method='POST' action='?cmd=100' enctype='multipart/form-data'> 
          Selecteer een "<b>.mklittlefs.bin</b>" bestand<br/>
          <input type='file' accept='mklittlefs.bin' name='filesystem'>
          <input type='submit' value='Flash LittleFS'>
      </form>
      <hr>
      <br/><font color='red'>Let op!!!</font>
      <br/>Bij het flashen van LittleFS raakt u alle bestanden op LittleFS kwijt. 
      <br/>Maak daarom eerst een kopie van deze bestanden (met de FSexplorer) 
      en zet deze na het flashen van LittleFS weer terug.
      <hr>
      <br/>
        Klik <span style='font-size:1.3em;'><b><a href="/">hier</a></b></span> 
        om terug te keren naar het hoofdscherm!
     </body>
     </html>)";

static const char UpdateServerSuccess[] PROGMEM = 
  R"(<html charset="UTF-8">
     <style type='text/css'>
        body {background-color: lightgray;}
     </style>
     <body>
     <h1>lichtKrant Flash utility</h1>
     <br/>
     <h2>Update successful!</h2>
     <br/>
     <br/>Wait for the lichtKrant to reboot and start the HTTP server
     <br/>
     <br>
     <br/>Wacht nog <span style='font-size: 1.3em;' id="waitSeconds">30</span> seconden ..
     <br/>Als het lijkt of er niets gebeurd, wacht dan tot de teller
          op 'nul' staat en klik daarna <span style='font-size:1.3em;'><b><a href="/">hier</a></b></span>!
     </body>
     <script>
         var seconds = document.getElementById("waitSeconds").textContent;
         var countdown = setInterval(function() {
           seconds--;
           document.getElementById('waitSeconds').textContent = seconds;
           if (seconds <= 0) {
              clearInterval(countdown);
              window.location.assign("/")
           }
         }, 1000);
     </script>
     </html>)";



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
