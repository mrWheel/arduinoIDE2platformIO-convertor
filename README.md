# ArduinoIDE to PlatformIO Converter

This Python script automates the process of converting an Arduino IDE project to a PlatformIO project structure. It's designed to simplify the transition from Arduino's traditional setup to PlatformIO's more organized and powerful environment.

For more information look <a href="https://willem.aandewiel.nl/index.php/2024/08/16/arduino-to-platformio-project-conversion/">here</a>.

## To Do (If you want to help, please create a merge request)
- ~~`struct` definitions should als be 'commented out' and placed in `arduinoGlue.h`~~
- Array declarations in the form
  ```
      char actualTableArray[][35] = { "timestamp"
                           , "power_returned_l1", "power_returned_l2", "power_returned_l3"
                           , "\0"
                         };
   ```
   should also be declared in `arduinoGlue.h` like:
     ```
     extern char actualTableArray[][35];
     ```
- A run-option to name the `arduinoGlue.h` file to your liking.
- A run-option to place the `PlatformIO` folder anywhere you want (and not inside the Arduino program folder).
- ~~More testing (f.i. does the `--project_dir` option works - never tested it myself).~~
- Macros like
  ```
  #ifdef xyz
      #include <libA.h>
  #else
      #include <libB.h>
  #endif
  ```
  are not processed correctly and both libraries are included
- More testing in general (what works and what does not work).
     
## Features

- Converts Arduino (.ino) files to C++ (.cpp) files
- Creates appropriate header (.h) files for each source file
- Extracts and centralizes all #define statements into a single `arduinoGlue.h` file
- Identifies and properly handles global variables
- Generates function prototypes in the `arduinoGlue.h` file
- Preserves existing code structure and comments
- Copies the project's data folder (if it exists) to the PlatformIO structure
- Creates a basic `platformio.ini` file for PlatformIO configuration

## How It Works

1. **Project Structure Creation**: 
   - Creates a PlatformIO folder structure with `src` and `include` directories

2. **File Conversion**:
   - Converts `.ino` files to `.cpp` files
   - Creates corresponding `.h` files for each `.cpp` file

3. **Define Handling**:
   - Extracts all #define statements
   - Places them in a centralized `arduinoGlue.h` file
   - Comments out original #define statements in source files

4. **Global Variable Management**:
   - Identifies global variables
   - Places them into the `arduinoGlue.h` file and adds `extern` in front of the declarations

5. **Function Prototype Generation**:
   - Extracts function declarations
   - Adds them to the `arduinoGlue.h` header file

6. **Main Project File Handling**:
   - Specially processes the main project file (originally .ino, converted to .cpp)
   - Ensures all necessary includes are present

7. **Data Folder Handling**:
   - Copies the `data` folder from the Arduino project to the PlatformIO structure (if it exists)

8. **PlatformIO Configuration**:
   - Generates a basic `platformio.ini` file with common settings

## Usage

1. Ensure you have Python installed on your system
2. Place the script in a directory accessible to your Arduino project
3. Run the script with the following command:
```
python3 arduinoIDE2platformIO.py --project_dir /path/to/your/arduino/project
```
  or `cd` to the directory where the Arduino.ino files are located and run the following command:
```
cd /path/to/your/arduino/project
python arduinoIDE2platformIO.py 
```
5. The script will create a new `PlatformIO` folder in your project directory with the converted project structure

## Notes

- Always backup your project before running this converter
- Review the generated files to ensure everything was converted correctly
- You may need to make minor adjustments to the code or PlatformIO configuration based on your specific project requirements

## Contributing

Contributions to improve the converter are welcome. Please feel free to submit issues or merge requests on the GitHub repository.

## License

MIT License

Copyright (c) 2024 Willem Aandewiel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
