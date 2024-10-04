# How to convert a ArduinoIDE project to PlatformIO

1) You have to clone the repo to your computer.
2) In a terminal window you ‘cd’ to the folder where you cloned the repo.
3) Then you type “python3 arduinoIDE2platformIO.py –project_dir &lt;pathToArduinoProject&gt;<br>
(there are two ‘-‘ before ‘project_dir’)

The converted project is located in &lt;pathToArduinoProject&gt;/platformIO/

All you have to do is edit the ‘platformio.ini’ file to your needs.

Mind you: the convertor will not always do everything for you. Sometimes you have to iterate [compile] -> solve compile errors -> [compile] -> solve compile errors ...

If it compiles without errors test it. If it works as expected you can cleanup the ‘arduinoGlue.h’ file with the ‘crossReference.py’ file.

Next step can be to look for prototypes that are not used in any other file then where the function is defined. You can then move that prototype definition to the '.h' file of the corresponding '.cpp' file.
It is not necessary but it makes better C(++) code.


## structure ArduinoIDE project

## structure PlatformIO project

