# ESP_ticker
A 'news' ticker with esp8266 and *MAX7219 Dot matrix modules*

based on [**this post**](https://willem.aandewiel.nl/index.php/2020/06/09/an-esp8266-ticker/)
<p>Firmware by Willem Aandewiel

## uses:
<pre>
tzapu/WiFiManager @ 0.16.0
majicdesigns/MD_Parola @ 3.7.3
https://github.com/mrWheel/ModUpdateServer
</pre>

## platformio.ini
<pre>
; PlatformIO Project Configuration File
;
;   Build options: build flags, source filter
;   Upload options: custom upload port, speed and extra flags
;   Library options: dependencies, extra library storages
;   Advanced options: extra scripting
;
; Please visit documentation for the other options and examples
; https://docs.platformio.org/page/projectconf.html

[platformio]
workspace_dir   = .pio.nosync
default_envs    = myBoard

[env:myBoard]
platform        = espressif8266
board           = esp12e
board_build.filesystem = littlefs
framework       = arduino
monitor_speed   = 115200
upload_speed    = 115200
#-- you NEED the next line (with the correct port)
#-- or the data upload will NOT work!
upload_port     = /dev/cu.usbserial-0001
build_unflags = 

build_flags = 
    	-D DEBUG
      -D ARDUINO_ESP8266_GENERIC

lib_ldf_mode = deep+
lib_deps = 
      tzapu/WiFiManager @ 0.16.0
      majicdesigns/MD_Parola @ 3.7.3
      https://github.com/mrWheel/ModUpdateServer

monitor_filters = 
	esp8266_exception_decoder
<pre>



