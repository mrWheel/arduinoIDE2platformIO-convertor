#------------------------------------------------------------
#
#   convert a ArduinoIDE project to a PlatformIO project
#
#   file name : arduinoIDE2platformIO.py   
#
#   by        : Willem Aandewiel
#
#   Version   : v0.79 (06-09-2024)
#
#   license   : MIT (see at the bottom of this file)
#------------------------------------------------------------
import os
import sys
import shutil
import re
import argparse
import logging
import traceback
from datetime import datetime
from collections import OrderedDict

# Extended list of known classes
dict_known_classes = [
        'WiFiServer', 'ESP8266WebServer', 'WiFiClient', 'WebServer',
        'WiFiManager', 'Timezone', 'DNSServer', 'IPAddress'
        'ESP8266mDNS', 'ArduinoOTA', 'PubSubClient', 'NTPClient', 'Ticker',
        'ESP8266HTTPClient', 'WebSocketsServer', 'AsyncWebServer', 'AsyncWebSocket',
        'SPIFFSConfig', 'HTTPClient', 'WiFiUDP', 'ESP8266WiFiMulti', 'ESP8266SSDP',
        'ESP8266HTTPUpdateServer', 'ESP8266mDNS', 'Adafruit_Sensor', 'DHT',
        'LiquidCrystal', 'Servo', 'Stepper', 'SoftwareSerial', 'EEPROM',
        'TFT_eSPI', 'Adafruit_GFX', 'SD', 'Wire', 'SPI', 'OneWire', 'DallasTemperature',
        'Adafruit_NeoPixel', 'FastLED', 'IRremote', 'ESP32Encoder', 'CapacitiveSensor',
        'AccelStepper', 'ESP32Time', 'BluetoothSerial', 'BLEDevice', 'BLEServer',
        'BLEClient', 'SPIFFS', 'LittleFS', 'ESPAsyncWebServer', 'AsyncTCP',
        'ESP32_FTPClient', 'PCA9685', 'Adafruit_PWMServoDriver', 'MPU6050',
        'TinyGPS', 'RTClib', 'Preferences', 'ESPmDNS', 'Update', 'HTTPUpdate',
        'HTTPSServer', 'HTTPSServerRequest', 'HTTPSServerResponse'
    ]

# Dictionary of libraries and their associated objects
dict_singleton_classes = {
    "LittleFS.h": ["Dir", "FSInfo", "FSinfo", "File", "exists", "FS", "LittleFS"],
    "SPI.h":      ["SPI", "SPISettings", "SPIClass"],
    "Wire.h":     ["Wire", "TwoWire"],
    "IPAddress.h": ["IPAddress"]
    # Add other libraries and their keywords here
}

args                      = None
glob_project_name         = ""
glob_ino_project_folder   = ""
glob_working_dir          = os.getcwd()
glob_pio_folder           = ""
glob_pio_project_folder   = ""
glob_pio_src              = ""
glob_pio_include          = ""
dict_all_includes         = {}
dict_global_variables     = {}
dict_undefined_vars_used  = {}
dict_prototypes           = {}
dict_class_instances      = {}
dict_struct_declarations  = {}
dict_includes             = {}
platformio_marker         = "/PlatformIO"
all_includes_marker       = "//============ Includes ===================="
all_includes_added        = False
all_defines_marker        = "//============ Defines & Macros===================="
all_defines_added         = False
struct_union_and_enum_marker  = "//============ Structs, Unions & Enums ============"
struct_union_and_enum_added        = False
global_pointer_arrays_marker  = "//============ Pointer Arrays ============"
global_pointer_arrays_added = False
extern_variables_marker   = "//============ Extern Variables ============"
extern_variables_added    = False
extern_classes_marker     = "//============ Extern Classes =============="
extern_classes_added      = False
prototypes_marker         = "//============ Function Prototypes ========="
prototypes_added         = False
convertor_marker          = "//============ Added by Convertor =========="
convertor_added          = False

#------------------------------------------------------------------------------------------------------
def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)7s - :%(lineno)4d - %(message)s'
    )

#------------------------------------------------------------------------------------------------------
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Convert Arduino project to PlatformIO structure.")
    parser.add_argument("--project_dir", default=os.getcwd(), help="Path to the project directory")
    parser.add_argument("--backup", action="store_true", help="Create a backup of original files")
    parser.add_argument("--debug", action="store_true", help="Enable debug-level logging")
    return parser.parse_args()

#------------------------------------------------------------------------------------------------------
def backup_project():
    """Create a backup of the project folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = f"{glob_ino_project_folder}_backup_{timestamp}"
    shutil.copytree(glob_ino_project_folder, backup_folder)
    logging.info(f"Project backup created at: {backup_folder}")

#------------------------------------------------------------------------------------------------------
def print_dict(dict):
      keys = list(dict.keys())
      logging.info(f"Keys: {keys}")
      # Iterate over keys and values
      logging.info("Iterating over keys and values:")
      for key, value in dict_global_variables.items():
          logging.info(f"  key[{key}]: value[{value}]")

#------------------------------------------------------------------------------------------------------
def set_glob_project_info(project_dir):
    """
    Get project folder, name, and PlatformIO-related paths.

    Returns:
        tuple: Contains project_folder, glob_project_name, glob_pio_folder, glob_pio_src, glob_pio_include
    """
    logging.info("")
    logging.info(f"Processing: set_glob_project_info({os.path.basename(project_dir)})")
    global glob_ino_project_folder
    global glob_pio_project_folder
    global glob_working_dir
    global glob_project_name
    global glob_root_folder
    global glob_pio_folder
    global glob_pio_src
    global glob_pio_include

    # Use project_dir if provided, otherwise use the current working directory
    glob_ino_project_folder = os.path.abspath(project_dir) if project_dir else os.path.abspath(glob_working_dir)
    glob_project_name       = os.path.basename(glob_ino_project_folder)
    glob_pio_folder         = os.path.join(glob_ino_project_folder, "PlatformIO")
    glob_pio_project_folder = os.path.join(glob_pio_folder, glob_project_name)
    glob_pio_src            = os.path.join(glob_pio_folder, glob_project_name, "src")
    glob_pio_include        = os.path.join(glob_pio_folder, glob_project_name, "include")

    logging.debug(f"glob_ino_project_folder: {glob_ino_project_folder}")
    logging.debug(f"glob_pio_project_folder: {glob_pio_project_folder}")
    logging.debug(f"      glob_project_name: {glob_project_name}")
    logging.debug(f"        glob_pio_folder: {glob_pio_folder}")
    logging.debug(f"           glob_pio_src: {glob_pio_src}")
    logging.debug(f"       glob_pio_include: {glob_pio_include}\n")

    return

#------------------------------------------------------------------------------------------------------
def extract_word_by_position(s, word_number, separator):
    """
    Extracts the word at the specified position based on the given separator.
    
    Args:
    s (str): The input string.
    word_number (int): The position of the word to extract (0-based index).
    separator (str): The separator character to split the string.
    
    Returns:
    str: The extracted word or None if the position is out of range.
    """
    # Split the string based on the separator
    parts = s.split(separator)
    
    if separator == '(':
        # Further split the part before the first '(' by whitespace to get individual words
        words = parts[0].strip().split()
    else:
        words = parts
    
    # Return the word at the specified position if within range
    if 0 <= word_number < len(words):
        return words[word_number].strip()
    
    return None

#------------------------------------------------------------------------------------------------------
def short_path(directory_path):
    """
    Format the directory path for logging, shortening it if it contains the {marker}.
    
    Args:
    directory_path (str): The full directory path
    marker (str): The marker to look for in the path

    Returns:
    str: Formatted string suitable for logging
    """
    marker_index = directory_path.find(glob_project_name)
    if marker_index != -1:
        part_of_path = directory_path[marker_index + len(glob_project_name):]
        return f"../{glob_project_name}{part_of_path}"
    else:
        return f"{directory_path}"

#------------------------------------------------------------------------------------------------------
def create_arduinoglue_file():
    """
    Create arduinoGlue.h file with necessary markers and header guards.
    """
    try:
        all_defines_path = os.path.join(glob_pio_include, 'arduinoGlue.h')
        logging.info(f"\tCreating arduinoGlue.h")
        with open(all_defines_path, 'w') as f:
            f.write("#ifndef ARDUINOGLUE_H\n#define ARDUINOGLUE_H\n\n")
            f.write(f"\n{all_includes_marker}")
            f.write(f"\n{all_defines_marker}")
            f.write(f"\n\n{struct_union_and_enum_marker}")
            f.write(f"\n{extern_variables_marker}")
            f.write(f"\n{global_pointer_arrays_marker}")
            f.write(f"\n{extern_classes_marker}")
            f.write(f"\n{prototypes_marker}")
            f.write(f"\n{convertor_marker}")
            f.write("\n#endif // ARDUINOGLUE_H\n")

        logging.info(f"\tSuccessfully created {short_path(all_defines_path)}")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError creating arduinoGlue.h: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def find_marker_position(content, prio_marker):

    try:
        if (content == ""):
            logging.error(f"find_marker_position(): content is empty")
            return -1
        
        marker = prio_marker
        marker_index = content.find(marker)
        if marker_index != -1:
            return marker_index + len(marker +'\n')
        
        marker = all_includes_marker
        marker_index = content.find(marker)
        if marker_index != -1:
            return marker_index + len(marker +'\n')
        
        marker = extern_variables_marker
        marker_index = content.find(marker)
        if marker_index != -1:
            return marker_index + len(marker +'\n')
        
        marker = prototypes_marker
        marker_index = content.find(marker)
        if marker_index != -1:
            return marker_index + len(marker +'\n')
        
        marker = convertor_marker
        marker_index = content.find(marker)
        if marker_index != -1:
            return marker_index + len(marker +'\n')

        marker = ""
        header_guard_end = re.search(r'#define\s+\w+_H\s*\n', content)
        if header_guard_end:
            return header_guard_end.end()

        logging.info("")
        logging.info("################################### no markers found! ##################################")
        logging.info(f"{content}\n")
        logging.info("################################### no markers found! ##################################\n\n")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError creating arduinoGlue.h: {str(e)}")
        exit()

    logging.info("\t\t\t===> no markers found!")
    return 0

#------------------------------------------------------------------------------------------------------
def remove_comments(code):
    # Remove single-line comments
    code = re.sub(r'//.*', '', code)
    # Remove multi-line comments
    code = re.sub(r'/\*[\s\S]*?\*/', '', code)
    return code
   
#------------------------------------------------------------------------------------------------------
def print_global_vars(global_vars):
    """
    Print global variables line by line, grouped by file.

    Args:
    global_vars (dict): Dictionary of global variables, where keys are file paths
                        and values are lists of tuples (var_type, var_name, function, is_pointer)
    """
    if not any(vars_list for vars_list in global_vars.values()):
        return
    try:
        sorted_global_vars = sort_global_vars(global_vars)

        if (len(sorted_global_vars) > 0):
            logging.info("")
            logging.info("--- Global Variables ---")
        for file_path, vars_list in sorted_global_vars.items():
            if vars_list:  # Only print for files that have global variables
                for var_type, var_name, function, is_pointer in vars_list:
                    pointer_str = "*" if is_pointer else " "
                    function_str = function if function else "global scope"
                    logging.info(f"       {var_type:<15} {var_name:<35} {function_str:<20} (in {file_path})")
        
        logging.info("")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def sort_global_vars(global_vars):
    """
    Sort the global variables dictionary by file path and variable name.

    Args:
    global_vars (dict): Dictionary of global variables, where keys are file paths
                        and values are lists of tuples (var_type, var_name, function, is_pointer)

    Returns:
    OrderedDict: Sorted dictionary of global variables
    """
    sorted_dict = OrderedDict()
    for file_path in sorted(global_vars.keys()):
        sorted_dict[file_path] = sorted(global_vars[file_path], key=lambda x: x[1])  # Sort by var_name
    return sorted_dict


#------------------------------------------------------------------------------------------------------
def print_global_vars_undefined(global_vars_undefined):
    """
    Print global variables used in functions.
    
    Args:
    global_vars_undefined (dict): Dictionary of global variables used in functions
    """
    try:
        if (len(global_vars_undefined) > 0):
            logging.info("")
            logging.info("--- Undefined Global Variables ---")
        for key, info in sorted(global_vars_undefined.items(), key=lambda x: (x[1]['var_name'], x[1]['used_in'], x[1]['line'])):
            pointer_str = "*" if info['var_is_pointer'] else ""
            var_type_pointer = f"{info['var_type']}{pointer_str}"
            logging.info(f"  - {var_type_pointer:<15.15} {info['var_name']:<30} (line {info['line']:<4}  in {info['used_in'][:20]:<20}) [{var_type_pointer:<25.25}] (defined in {info['defined_in']})")

        logging.info("")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def print_prototypes(functions_dict):
    """
    Print the function prototypes and their source files.
    
    Args:
    functions_dict (dict): Dictionary of function prototypes, with function names as keys and tuples (prototype, file_path) as values.
    """
    try:
      if not functions_dict:
          logging.info("\tNo functions found.")
          return

      logging.info("")
      logging.info("--- Function Prototypes ---")
      for key, value in functions_dict.items():
          func_name, params = key
          prototype, file_name, bare_func_name = value
          logging.info(f"{file_name:<25}  {bare_func_name:<30} {prototype}")

      logging.info("")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()


#------------------------------------------------------------------------------------------------------
def print_class_instances(class_instances):
    """Print the dictionary of class instances."""
    try:
        if not any(vars_list for vars_list in class_instances.values()):
            return

        logging.info("")
        logging.info("--- Class Instances ---")
        for file_path, class_list in class_instances.items():
            if class_list:  # Only print for files that have classes
                for class_type, instance_name, constructor_args, fbase in class_list:
                    parentacedConstructor = "("+constructor_args+")"
                    logging.info(f"       {class_type:<25} {instance_name:<25} {parentacedConstructor:<15} (in {fbase})")
        
        logging.info("")
                                    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"A\tn error occurred at line {line_number}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def print_includes(includes):
    """
    Prints the list of include statements.

    Args:
    includes (list): List of include statements to print.
    """
    try:
        if len(includes) == 0:
            return

        logging.info("")
        logging.info("--- Include Statements ---")
        for include in includes:
            logging.info(f"  {include}")
        logging.info("")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"A\tn error occurred at line {line_number}: {str(e)}")
        exit()



#------------------------------------------------------------------------------------------------------
def print_struct_definitions(struct_definitions):
    if struct_definitions:
        logging.info(f"\tStruct definitions found:")
        for struct_name, struct_body in struct_definitions.items():
            logging.info(f"\t\t{struct_name}:")
            for line in struct_body.split('\n'):
                logging.info(f"\t\t\t{line.strip()}")
    else:
        logging.info(f"\tNo struct definitions found in the file")

#------------------------------------------------------------------------------------------------------
def list_files_in_directory(directory_path):
    """
    List and print all files in the specified directory.
    
    Args:
    directory_path (str): The path to the directory to list files from.
    """
    try:
        # Get the list of all entries in the directory
        entries = os.listdir(directory_path)
        
        # Filter out directories, keep only files
        files = [entry for entry in entries if os.path.isfile(os.path.join(directory_path, entry))]
        
        #marker_index = directory_path.find(platformio_marker)
        #if marker_index != -1:
        #    part_of_path = directory_path[marker_index + len(platformio_marker):]
        #    logging.info(f"Files in directory '{part_of_path}':")
        #else:
        #    logging.info(f"Files in the directory '{directory_path}':")
        logging.info(" ")
        logging.info(f"Files in the directory '{short_path(directory_path)}':")

        if files:
            for file in files:
                logging.info(f"\t> {file}")
        else:
            logging.info("\tNo files found in this directory.")

    except FileNotFoundError:
        logging.error(f"\tError: Directory '{short_path(directory_path)}' not found.")
    except PermissionError:
        logging.error(f"\tError: Permission denied to access directory '{short_path(directory_path)}'.")
    except Exception as e:
          exc_type, exc_obj, exc_tb = sys.exc_info()
          fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
          line_number = exc_tb.tb_lineno
          logging.error(f"\tAn error occurred in {fname} at line {line_number}: {str(e)}")
          exit()

#------------------------------------------------------------------------------------------------------
def rename_file(old_name, new_name):
    logging.info("")
    logging.info(f"rename_file(): {short_path(old_name)} -> {short_path(new_name)}")

    # Check if the paths exist
    if not os.path.exists(old_name):
        logging.info(f"\tThe file {short_path(old_name)} does not exist")
        return
    
    try:
        os.rename(old_name, new_name)
        logging.debug(f"\tFile renamed successfully from [{os.path.basename(old_name)}] to [{os.path.basename(new_name)}]")
    except FileNotFoundError:
        logging.info(f"\tThe file {short_path(old_name)} does not exist")
    except PermissionError:
        logging.info(f"\tYou don't have permission to rename this file [{short_path(old_name)}]")
    except FileExistsError:
        logging.info(f"\tA file with the name {short_path(new_name)} already exists")
    except Exception as e:
        logging.info(f"\tAn error occurred: {str(e)}")

#------------------------------------------------------------------------------------------------------
def remove_pio_tree(preserve_file):
    logging.info("")
    logging.info(f"remove_pio_tree(): {short_path(glob_pio_folder)}, project:[{glob_project_name}], preserve:[{preserve_file}]")
    # Construct the full path
    #full_path = os.path.join(glob_pio_folder, glob_project_name)
    
    # Check if the paths exist
    if not os.path.exists(glob_pio_folder):
        logging.error(f"\tError: The base path '{short_path(glob_pio_folder)}' does not exist.")
        return
    #if not os.path.exists(full_path):
    #    logging.error(f"Error: The full path '{short_path(full_path)}' does not exist.")
    #    return

    # Get the full path of the file to preserve
    preserve_file_path = os.path.join(glob_pio_project_folder, preserve_file)
    #logging.info(f"\t>>>> Preserve [{short_path(preserve_file_path)}]")
    
    # Check if the preserve_file exists and read its contents
    preserve_file_contents = None
    if os.path.exists(preserve_file_path):
        with open(preserve_file_path, 'r') as f:
            preserve_file_contents = f.read()
    
    try:
        # Remove all contents of the last folder
        for root, dirs, files in os.walk(glob_pio_folder, topdown=False):
            for name in files:
                if name == preserve_file:
                    logging.info(f"\tDONT REMOVE: [{short_path(preserve_file_path)}]")
                else:
                    #logging.info(f"\tRemoving file: [{name}]")
                    os.remove(os.path.join(root, name))
            for name in dirs:
                this_dir = os.path.join(root, name)
                #logging.info(f"Removing dir: [{this_dir}]")
                if len(os.listdir(this_dir)) != 0:
                    logging.info(f"\tRemoving dir: [{this_dir}] NOT EMPTY")
                #if os.path.exists(this_dir):
                else:
                    #logging.info(f"\tRemoving dir: [{name}]")
                    os.rmdir(os.path.join(root, name))
        
        list_files_in_directory(glob_pio_folder)
        # Remove all other contents in the base directory except the preserve_file
        for item in os.listdir(glob_pio_folder):
            item_path = os.path.join(glob_pio_folder, item)
            #if item != preserve_file and os.path.isfile(item_path):
            if os.path.isfile(item_path):
                logging.info(f"\tremove: {item_path}")
                os.remove(item_path)
            #elif item != last_folder and os.path.isdir(item_path):
            elif item != glob_pio_folder and os.path.isdir(item_path):
                logging.info(f"\tRemove tree: {item_path}")
                #shutil.rmtree(item_path)
        
        # Restore or create the preserve_file with its original contents
        with open(preserve_file_path, 'w') as f:
            if preserve_file_contents is not None:
                f.write(preserve_file_contents)
        
        logging.info(f"\tSuccessfully removed all contents in [{short_path(glob_pio_folder)}]")
        logging.info(f"\tand all other contents in [{short_path(glob_pio_folder)}] except [{preserve_file}]")
    
    except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            #fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            line_number = exc_tb.tb_lineno
            logging.error(f"\tAn error occurred at line {line_number}:\n {str(e)}")
            exit()

#------------------------------------------------------------------------------------------------------
def recreate_pio_folders():
    """Create or recreate PlatformIO folder structure."""

    logging.info("")
    logging.info("Processing: recreat_pio_folders()")

    # Ensure the main PlatformIO folder exists
    if not os.path.exists(glob_pio_folder):
        os.makedirs(glob_pio_folder)
        logging.debug(f"\tCreated PlatformIO folder: {short_path(glob_pio_folder)}")

    # Get the current working directory
    current_dir = os.getcwd()
    logging.debug(f"\tCurrent working directory: {current_dir}")

    # Construct the full base path
    full_base_path = os.path.join(current_dir, glob_pio_folder, glob_project_name)
    logging.debug(f"\t  Full base path: {full_base_path}")
    logging.debug(f"\t    glob_pio_src: {glob_pio_src}")
    logging.debug(f"\tglob_pio_include: {glob_pio_include}")

    # Recreate src and include folders
    for folder in [glob_pio_src, glob_pio_include]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        logging.debug(f"\tmakedirs [{folder}]")
        os.makedirs(folder)
        logging.debug(f"\tRecreated folder: [{folder}]")

    logging.info("\tPlatformIO folder structure recreated")

#------------------------------------------------------------------------------------------------------
def insert_include_in_header(header_lines, inserts):
    """
    Insert #include statements in the header file.
    """
    logging("")
    logging.info("Processing: insert_include_in_header() ..")

    includes_to_add = []
    includes_added = set()

    # Process inserts
    for item in inserts:
        class_name = item[0]
        logging.info(f"\t\tChecking if {class_name} ...")
        
        # Check if the class is in dict_singleton_classes
        singleton_header = None
        for header, classes in dict_singleton_classes.items():
            logging.info(f"\t\tChecking if {class_name} is in {header}")
            if class_name in classes or class_name == header:
                singleton_header = header
                break
        
        if singleton_header:
            if singleton_header not in includes_added:
                includes_to_add.append(f'#include <{singleton_header}>\t\t//-- singleton')
                includes_added.add(singleton_header)
                logging.debug(f"\t\tAdding #{class_name} via <{singleton_header}>")
        elif class_name.endswith('.h'):
            if class_name not in includes_added:
                includes_to_add.append(f'#include <{class_name}>')
                includes_added.add(class_name)
                logging.debug(f"\t\tAdding <{class_name}>")
        else:
            if class_name not in includes_added:
                includes_to_add.append(f'#include <{class_name}.h>')
                includes_added.add(class_name)
                logging.debug(f"\t\tAdding <{class_name}.h>")

    # Find the position to insert the new includes
    insert_position = 0
    for i, line in enumerate(header_lines):
        if line.strip().startswith('#include'):
            insert_position = i + 1
        elif not line.strip().startswith('#') and line.strip() != '':
            break

    # Insert the new includes
    for include in includes_to_add:
        header_lines.insert(insert_position, include + '\n')
        insert_position += 1

    return header_lines

#------------------------------------------------------------------------------------------------------
def insert_method_include_in_header(header_file, include_statement):
    logging.info("")
    logging.info("Processing: insert_method_include_in_header() ..")
    try:
        with open(header_file, 'r') as file:
            content = file.readlines()

        # Find the appropriate position to insert the include statement
        convertor_marker_position = -1
        first_comment_end = -1

        # Extract the library name from the include statement
        library_name = re.search(r'#include\s*<(.+)>', include_statement)
        if not library_name:
            logging.error(f"Invalid include statement: {include_statement}")
            return

        library_name = library_name.group(1)

        for i, line in enumerate(content):
            stripped_line = line.strip()
            
            if stripped_line == convertor_marker:
                convertor_marker_position = i
                break
            
            if first_comment_end == -1 and (stripped_line.endswith('//') or stripped_line.endswith('*/')):
                first_comment_end = i

        # If convertor_marker is not found, add it after the first comment
        if convertor_marker_position == -1 and first_comment_end != -1:
            content.insert(first_comment_end + 1, f"{convertor_marker}\n")
            convertor_marker_position = first_comment_end + 1

        # Always insert the include statement after the convertor_marker
        insert_position = convertor_marker_position + 1 if convertor_marker_position != -1 else 0
        
        # Check if the include statement already exists, ignoring comments
        include_exists = any(
            re.search(rf'#include\s*<{re.escape(library_name)}>\s*(//.*)?$', line.strip())
            for line in content
        )
        
        if not include_exists:
            content.insert(insert_position, f"{include_statement}\t\t//-- added by instance.method()\n")
            logging.debug(f"\tInserted include statement in {short_path(header_file)}: {include_statement}")
        else:
            logging.debug(f"\tInclude statement already exists in {short_path(header_file)}: {include_statement}")
        
        with open(header_file, 'w') as file:
            file.writelines(content)
    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}:\n {str(e)}")
        exit()


#------------------------------------------------------------------------------------------------------
def copy_data_folder():
    """
    Delete existing data folder in glob_pio_folder if it exists,
    then copy the data folder from the project folder to the PlatformIO folder if it exists.
    """
    logging.info("")
    logging.info("Processing: copy_data_folder()")

    source_data_folder = os.path.join(glob_ino_project_folder, 'data')
    destination_data_folder = os.path.join(glob_pio_folder, glob_project_name, 'data')

    # Delete existing data folder in glob_pio_folder if it exists
    if os.path.exists(destination_data_folder):
        try:
            shutil.rmtree(destination_data_folder)
            logging.debug(f"\tDeleted existing data folder in {short_path(glob_pio_folder)}")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            line_number = exc_tb.tb_lineno
            logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
            logging.error(f"\tError deleting existing data folder: {str(e)}")
            return  # Exit the function if we can't delete the existing folder

    # Copy data folder from project folder to glob_pio_folder if it exists
    if os.path.exists(source_data_folder):
        try:
            logging.debug("\tCopy data folder ")
            logging.debug(f"\t>> from: {short_path(source_data_folder)}")
            logging.debug(f"\t>>   to: {short_path(destination_data_folder)}")
            shutil.copytree(source_data_folder, destination_data_folder)
            logging.debug(f"\tCopied data folder from {short_path(source_data_folder)} to {short_path(destination_data_folder)}")

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            #fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            line_number = exc_tb.tb_lineno
            logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
            logging.error(f"\tError deleting existing data folder: {str(e)}")
            logging.error(f"\tError copying data folder: {str(e)}")
    else:
        logging.info("\tNo data folder found in the project folder")

#------------------------------------------------------------------------------------------------------
def create_platformio_ini():
    """Create a platformio.ini file if it doesn't exist."""
    logging.info("")
    logging.info(f"Processing: create _platformio_ini() if it doesn't exist in [{short_path(glob_pio_project_folder)}]")

    platformio_ini_path = os.path.join(glob_pio_project_folder, 'platformio.ini')
    if not os.path.exists(platformio_ini_path):
        platformio_ini_content = """
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
workspace_dir = .pio.nosync
default_envs = myBoard

[env:myBoard]
;-- esp32
#platform = espressif32
#board = esp32dev
#framework = arduino
#board_build.partitions = <min_spiffs.csv>
#board_build.filesystem = <LittleFS>|<SPIFFS>
#monitor_speed = 115200
#upload_speed = 115200
#build_flags =
#\t-D DEBUG
#
#lib_ldf_mode = deep+
#
#lib_deps =
;\t<select libraries with "PIO Home" -> Libraries

##-- you NEED the next line (with the correct port)
##-- or the data upload will NOT work!
#upload_port = </dev/serial_port>
#monitor_filters =
#  esp32_exception_decoder

;-- esp8266
#platform = espressif8266
#board = esp12e
#framework = arduino
##-- you NEED the next line (with the correct port)
##-- or the data upload will NOT work!
#upload_port = </dev/serial_port>
#board_build.filesystem = <littlefs>|<spiffs>
#build_flags =
#\t-D DEBUG
#
#lib_ldf_mode = deep+
#
#lib_deps =
;\t<select libraries with "PIO Home" -> Libraries
#monitor_filters =
#  esp8266_exception_decoder

;-- attiny85
#platform = atmelavr
#board = attiny85
#framework = arduino
#upload_protocol = usbtiny
#upload_speed = 19200
;-- Clock source Int.RC Osc. 8MHz PWRDWN/RESET: 6 CK/1
#board_fuses.lfuse = 0xE2
;-- Serial program downloading (SPI) enabled
;-- brown-out Detection 1.8v (0xDE)
;board_fuses.hfuse = 0xDE    
;-- brown-out detection 2.7v (0xDD)
#board_fuses.hfuse = 0xDD    
;-- brown-out detection 4.3v (0xDC)
;board_fuses.hfuse = 0xDC    
#board_fuses.efuse = 0xFF

#framework = arduino
#board_build.filesystem = LittleFS
#monitor_speed = 115200
#upload_speed = 115200
#upload_port = <select port like "/dev/cu.usbserial-3224144">
#build_flags =
#\t-D DEBUG
#
#lib_ldf_mode = deep+
#
#lib_deps =
;\t<select libraries with "PIO Home" -> Libraries
"""
        with open(platformio_ini_path, 'w') as f:
            f.write(platformio_ini_content)
            logging.info(f"\tCreated platformio.ini file at {short_path(platformio_ini_path)}")

    else:  
        logging.info(f"\tplatformio.ini file already exists at [{short_path(platformio_ini_path)}]")


#------------------------------------------------------------------------------------------------------
def move_struct_union_and_enum_declarations():
    logging.info("")
    logging.info(f"Processing: move_struct_union_and_enum_declarations() ")

    global struct_union_and_enum_added

    search_folders = [glob_pio_src, glob_pio_include]

    def find_declaration_end(content, start_pos):
        bracket_count = 0
        for i, char in enumerate(content[start_pos:]):
            if char == '{':
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
                if bracket_count == 0:
                    # Look for the semicolon after the closing brace
                    semicolon_pos = content.find(';', start_pos + i)
                    if semicolon_pos != -1:
                        return semicolon_pos + 1
                    return start_pos + i + 1
        return -1

    def is_in_comment(content, pos):
        # Check for single-line comment
        line_start = content.rfind('\n', 0, pos) + 1
        if '//' in content[line_start:pos]:
            return True

        # Check for multi-line comment
        last_comment_start = content.rfind('/*', 0, pos)
        if last_comment_start != -1:
            comment_end = content.find('*/', last_comment_start)
            if comment_end == -1 or comment_end > pos:
                return True

        return False

    for folder in search_folders:
        for root, _, files in os.walk(folder):
            for file in files:
                #??#if file.endswith(('.h', '.ino', '.cpp')) and not file.startswith('arduinoGlue'):
                if file.endswith(('.h', '.ino')) and not file.startswith('arduinoGlue'):
                    file_path = os.path.join(root, file)
                    logging.debug(f"\tProcessing file: {short_path(file_path)}")

                    try:
                        with open(file_path, 'r') as file:
                            content = file.read()

                        # Updated regular expression to match struct, union, and enum declarations, including 'typedef struct'
                        declaration_pattern = r'\b(typedef\s+)?(struct|union|enum)\s+(?:\w+\s+)*(?:\w+\s*)?{'

                        modified_content = content
                        declarations_to_move = []

                        for match in re.finditer(declaration_pattern, content):
                            start_pos = match.start()
                            
                            # Skip if the declaration is inside a comment
                            if is_in_comment(content, start_pos):
                                continue

                            end_pos = find_declaration_end(content, start_pos)
                            
                            if end_pos != -1:
                                decl_type = match.group(2)  # 'struct', 'union', or 'enum'
                                decl = content[start_pos:end_pos]
                                
                                # Check if the declaration is globally defined (not inside a function)
                                preceding_content = content[:start_pos]
                                brace_level = preceding_content.count('{') - preceding_content.count('}')
                                
                                if brace_level == 0:  # Declaration is globally defined
                                    # Prepare the declaration for arduinoGlue.h
                                    arduinoGlue_decl = f"//-- from {os.path.basename(file_path)}\n{decl}"
                                    declarations_to_move.append(arduinoGlue_decl)

                                    # Comment out the declaration in the original file
                                    comment_text = f"*** {decl_type} moved to arduinoGlue.h ***"
                                    commented_decl = f"/*\t\t\t\t{comment_text}\n{decl}\n*/"
                                    modified_content = modified_content.replace(content[start_pos:end_pos], commented_decl)
                                    struct_union_and_enum_added = True

                        # Write modified content back to the original file (File Under Test)
                        with open(file_path, 'w') as file:
                            file.write(modified_content)

                        # Insert declarations into arduinoGlue.h at the correct position
                        if declarations_to_move:
                            arduinoGlue_path = os.path.join(glob_pio_include, 'arduinoGlue.h')
                            with open(arduinoGlue_path, 'r+') as file:
                                arduinoGlue_content = file.read()
                                
                                # Find the correct insertion point
                                header_guard_match = re.search(r'#ifndef\s+\w+\s+#define\s+\w+', arduinoGlue_content)
                                if header_guard_match:
                                    header_guard_end = header_guard_match.end()
                                    # Find the struct_union_and_enum_marker after the header guard
                                    struct_union_and_enum_marker_pos = arduinoGlue_content.rfind(f"{struct_union_and_enum_marker}", header_guard_end)
                                    logging.info(f"\t\tstruct_union_and_enum_marker_pos: {struct_union_and_enum_marker_pos}")
                                    if struct_union_and_enum_marker_pos != -1:
                                        insert_point = arduinoGlue_content.find('\n', struct_union_and_enum_marker_pos) + 0
                                    else:
                                        # If no #define found, insert after header guard
                                        insert_point = arduinoGlue_content.find('\n', header_guard_end) + 1
                                else:
                                    # If no header guard found, insert at the beginning
                                    insert_point = 0
                                logging.info(f"\t\tinsert_point: {insert_point}")

                                # Ensure there's an empty line before the declarations and one after each declaration
                                new_content = arduinoGlue_content[:insert_point] + '\n'
                                new_content += '\n'.join(decl + '\n' for decl in declarations_to_move)
                                new_content += arduinoGlue_content[insert_point:]
                                
                                # Write the updated content back to arduinoGlue.h
                                file.seek(0)
                                file.write(new_content)
                                file.truncate()

                            logging.info(f"\tMoved {len(declarations_to_move)} struct/union/enum declaration(s) from [{os.path.basename(file_path)}] to arduinoGlue.h")
                        else:
                            logging.info(f"\tNo global struct/union/enum declarations found in [{os.path.basename(file_path)}]")

                    except FileNotFoundError:
                        logging.error(f"Error: File {file_path} not found.")
                    except IOError:
                        logging.error(f"Error: Unable to read or write file {file_path}.")
                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        line_number = exc_tb.tb_lineno
                        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
                        exit()


"""
#------------------------------------------------------------------------------------------------------
def extract_and_comment_defines():
    "" "
    Extract all #define statements (including functional and multi-line) from .h, .ino, and .cpp files,
    create arduinoGlue.h, and comment original statements with info.
    "" "
    logging.info("")
    logging.info(f"Searching for #define statements in {short_path(glob_pio_folder)}")

    try:
        all_defines = []
        define_pattern = r'^\s*#define\s+(\w+)(?:\(.*?\))?\s*(.*?)(?:(?=\\\n)|$)'

        # Only search within glob_pio_src and glob_pio_include folders
        search_folders = [glob_pio_src, glob_pio_include]

        for folder in search_folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(('.h', '.ino')):
                        file_path = os.path.join(root, file)
                        logging.debug(f"\tProcessing file: {short_path(file_path)}")
                        with open(file_path, 'r') as f:
                            content = f.read()

                        new_content = []
                        lines = content.split('\n')
                        i = 0
                        while i < len(lines):
                            line = lines[i]
                            match = re.match(define_pattern, line)
                            if match:
                                macro_name = match.group(1)
                                macro_value = match.group(2)
                                full_define = [line]

                                # Check for multi-line defines
                                while macro_value.endswith('\\') and i + 1 < len(lines):
                                    i += 1
                                    next_line = lines[i]
                                    full_define.append(next_line)
                                    macro_value += '\n' + next_line.strip()
                                    
                                # Add the closing line if it's not already included
                                if i + 1 < len(lines) and not macro_value.endswith('\\'):
                                    i += 1
                                    closing_line = lines[i]
                                    if closing_line.strip().startswith(')'):
                                        full_define.append(closing_line)
                                        macro_value += '\n' + closing_line.strip()
                                    else:
                                        i -= 1  # If it's not a closing parenthesis, go back one line

                                # Don't include header guards
                                if not macro_name.endswith('_H'):
                                    all_defines.append((macro_name, '\n'.join(full_define)))
                                    # Comment out the original #define with info
                                    new_content.extend([f"\t//-- moved to arduinoGlue.h // {line}" for line in full_define])
                                    logging.debug(f"\tAdded #define: {macro_name}")
                                else:
                                    new_content.extend(full_define)
                            else:
                                new_content.append(line)
                            i += 1

                        # Write the modified content back to the file
                        with open(file_path, 'w') as f:
                            f.write('\n'.join(new_content))
                        logging.debug(f"\tUpdated {file} with commented out #defines")

        # Create arduinoGlue.h with all macros
        all_defines_path = os.path.join(glob_pio_include, 'arduinoGlue.h')
        logging.info(f"\tCreating arduinoGlue.h with {len(all_defines)} macros")
        with open(all_defines_path, 'w') as f:
            f.write("#ifndef ARDUINOGLUE_H\n#define ARDUINOGLUE_H\n\n")
            for macro_name, macro_value in all_defines:
                f.write(f"{macro_value}\n")
            f.write(f"\n{all_includes_marker}")
            f.write(f"\n{struct_union_and_enum_marker}")
            f.write(f"\n\n{extern_variables_marker}")
            f.write(f"\n{global_pointer_arrays_marker}")
            f.write(f"\n{extern_classes_marker}")
            f.write(f"\n{prototypes_marker}")
            f.write(f"\n{convertor_marker}")
            f.write("\n#endif // ARDUINOGLUE_H\n")

        logging.info(f"\tSuccessfully created {short_path(all_defines_path)}")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        #fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError creating arduinoGlue.h: {str(e)}")
        exit()

    logging.info(f"\tExtracted {len(all_defines)} #define statements")
"""
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
def extract_and_comment_defines():
    """
    Extract all #define statements (including functional and multi-line) from .h, .ino, and .cpp files,
    comment original statements with info, and insert them into arduinoGlue.h after the all_defines_marker.
    """
    logging.info("")
    logging.info(f"Searching for #define statements in {short_path(glob_pio_folder)}")

    try:
        all_defines = []
        define_pattern = r'^\s*#define\s+(\w+)(?:\(.*?\))?\s*(.*?)(?:(?=\\\n)|$)'

        # Only search within glob_pio_src and glob_pio_include folders
        search_folders = [glob_pio_src, glob_pio_include]

        for folder in search_folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(('.h', '.ino')):
                        file_path = os.path.join(root, file)
                        logging.debug(f"\tProcessing file: {short_path(file_path)}")
                        with open(file_path, 'r') as f:
                            content = f.read()

                        new_content = []
                        lines = content.split('\n')
                        i = 0
                        while i < len(lines):
                            line = lines[i]
                            match = re.match(define_pattern, line)
                            if match:
                                macro_name = match.group(1)
                                macro_value = match.group(2)
                                full_define = [line]

                                # Check for multi-line defines
                                while macro_value.endswith('\\') and i + 1 < len(lines):
                                    i += 1
                                    next_line = lines[i]
                                    full_define.append(next_line)
                                    macro_value += '\n' + next_line.strip()
                                    
                                # Add the closing line if it's not already included
                                if i + 1 < len(lines) and not macro_value.endswith('\\'):
                                    i += 1
                                    closing_line = lines[i]
                                    if closing_line.strip().startswith(')'):
                                        full_define.append(closing_line)
                                        macro_value += '\n' + closing_line.strip()
                                    else:
                                        i -= 1  # If it's not a closing parenthesis, go back one line

                                # Don't include header guards
                                if not macro_name.endswith('_H'):
                                    all_defines.append('\n'.join(full_define))
                                    # Comment out the original #define with info
                                    new_content.extend([f"\t//-- moved to arduinoGlue.h // {line}" for line in full_define])
                                    logging.debug(f"\tAdded #define: {macro_name}")
                                else:
                                    new_content.extend(full_define)
                            else:
                                new_content.append(line)
                            i += 1

                        # Write the modified content back to the file
                        with open(file_path, 'w') as f:
                            f.write('\n'.join(new_content))
                        logging.debug(f"\tUpdated {file} with commented out #defines")

        # Insert all defines into arduinoGlue.h after the all_defines_marker
        all_defines_path = os.path.join(glob_pio_include, 'arduinoGlue.h')
        with open(all_defines_path, 'r') as f:
            content = f.read()

        marker_index = content.find(all_defines_marker)
        if marker_index != -1:
            new_content = (content[:marker_index + len(all_defines_marker)] + 
                           '\n' + '\n'.join(all_defines) + 
                           content[marker_index + len(all_defines_marker):])
            
            with open(all_defines_path, 'w') as f:
                f.write(new_content)

        logging.info(f"\tInserted {len(all_defines)} #define statements into {short_path(all_defines_path)}")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError extracting and inserting #define statements: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def add_markers_to_header_file(file_path):
    logging.info("")
    logging.info(f"Processing: add_markers_to_header_file() from: {short_path(file_path)}")

    try:
        with open(file_path, 'r') as file:
            content = file.read()

        markers = [
            convertor_marker,
            all_includes_marker,
        ]

        lines = content.split('\n')
        header_guard_start = -1
        comment_end = -1

        # Find opening header guard
        for i, line in enumerate(lines):
            if line.strip().startswith('#ifndef') or line.strip().startswith('#define'):
                header_guard_start = i
                break

        # Find end of first comment block
        in_multiline_comment = False
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith('//'):
                comment_end = i
            elif stripped_line.startswith('/*'):
                in_multiline_comment = True
            elif stripped_line.endswith('*/') and in_multiline_comment:
                comment_end = i
                in_multiline_comment = False
            elif not in_multiline_comment and stripped_line and comment_end != -1:
                break

        # Determine insertion point
        if header_guard_start != -1:
            insertion_point = header_guard_start + 2  # After both #ifndef and #define
        elif comment_end != -1:
            insertion_point = comment_end + 1
        else:
            insertion_point = 0

        # Insert markers
        for marker in markers:
            if marker not in content:
                lines.insert(insertion_point, marker)
                insertion_point += 1
            if insertion_point < len(lines):
                lines.insert(insertion_point, '')
                insertion_point += 1

        # Join lines back into content
        modified_content = '\n'.join(lines)

        with open(file_path, 'w') as file:
            file.write(modified_content)
                    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError modifying {file_path}: {str(e)}")
        exit()


#------------------------------------------------------------------------------------------------------
def create_new_header_file(ino_name, header_name):
    """Create new header file with basic structure."""
    logging.info("")
    logging.info(f"Processing: create_new_header_file(): {header_name} for [{ino_name}]")

    header_path = os.path.join(glob_pio_include, f"{header_name}")

    try:
        if os.path.exists(header_path):
            logging.info(f"\tHeader file already exists: {header_name}")
            add_markers_to_header_file(header_path)
            return

        base_name = os.path.splitext(header_name)[0]
        header_path = os.path.join(glob_pio_include, f"{header_name}")
        with open(header_path, 'w') as f:
            f.write(f"#ifndef {base_name.upper()}_H\n")
            f.write(f"#define {base_name.upper()}_H\n\n")
            f.write(f"{all_includes_marker}")
            f.write("\n")
            f.write("#include \"arduinoGlue.h\"\n\n")
            f.write(f"{convertor_marker}")
            f.write("\n")
            f.write(f"#endif // {base_name.upper()}_H\n")
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError creating arduinoGlue.h: {str(e)}")
        exit()

    logging.info(f"\tCreated new header file: {header_name}")


#------------------------------------------------------------------------------------------------------
def process_original_header_file(header_path, base_name):
    logging.info(f"Processing: process_original_header_file(): [{base_name}]")
    
    try:
        if os.path.exists(header_path):
            with open(header_path, 'r') as f:
                original_content = f.read()
            
            # Check for existing header guards
            guard_match = re.search(r'#ifndef\s+(\w+_H).*?#define\s+\1', original_content, re.DOTALL)
            has_guards = guard_match is not None

            new_content = original_content

            if not has_guards:
                # Add header guards if they don't exist
                logging.debug(f"\tAdding header guards for {base_name}")
                guard_name = f"{base_name.upper()}_H"
                new_content = f"#ifndef {guard_name}\n#define {guard_name}\n\n{new_content}\n#endif // {guard_name}\n"
            else:
                guard_name = guard_match.group(1)

            # Find the position to insert the all_includes_marker
            if all_includes_marker not in new_content:
                logging.debug(f"\tAdding {all_includes_marker} to {base_name}")
                # Find the first closing comment after the header guard
                comment_end = new_content.find('*/', new_content.find(guard_name)) + 2
                if comment_end > 1:  # If a closing comment was found
                    insert_pos = comment_end
                else:  # If no closing comment, insert after the header guard
                    insert_pos = new_content.find('\n', new_content.find(guard_name)) + 1
                
                new_content = new_content[:insert_pos] + f"\n{all_includes_marker}\n" + new_content[insert_pos:]

            # Check if arduinoGlue.h is already included
            if '#include "arduinoGlue.h"' not in new_content:
                logging.debug(f"\tAdding arduinoGlue.h include to {base_name}")
                # Insert after the convertor_markerloca
                insert_pos = new_content.find('\n', new_content.find(all_includes_marker)) + 1
                new_content = new_content[:insert_pos] + '#include "arduinoGlue.h"\n\n' + new_content[insert_pos:]

            # Only write to the file if changes were made
            if new_content != original_content:
                with open(header_path, 'w') as f:
                    f.write(new_content)
                logging.debug(f"\tUpdated original header file: {short_path(header_path)}")
            else:
                logging.debug(f"\tNo changes needed for: {short_path(header_path)}")
        else:
            logging.debug(f"\tFile not found: {short_path(header_path)}")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()

    return header_path


#------------------------------------------------------------------------------------------------------
def add_local_includes_to_project_header():
    """
    Adds all necessary includes to the project header file.

    This function reads the content of the project header file, identifies existing includes,
    and adds new includes that are not already present. It then writes the modified content
    back to the header file.
    """    
    logging.info("");
    logging.info(f"Processing: add_local_includes_to_project_header(): {glob_project_name}")

    try:
        project_header = os.path.join(glob_pio_include, f"{glob_project_name}.h")
        # Read the content of the source file
        with open(project_header, 'r') as file:
            content = file.read()

        # Remove multi-line comments
        content_without_multiline_comments = re.sub(r'/\*[\s\S]*?\*/', '', content)
        
        # Remove single-line comments
        content_without_comments = re.sub(r'//.*$', '', content_without_multiline_comments, flags=re.MULTILINE)

        # Find all includes that are not commented out
        existing_includes = set(re.findall(r'#include\s*[<"]([^>"]+)[>"]', content_without_comments))

        # Prepare new includes
        list_files_in_directory(glob_pio_include)
        new_includes = []
        for file_name in os.listdir(glob_pio_include):
            logging.debug(f"\tProcessing file: {file_name}")
            header_name = os.path.basename(file_name)  # Get the basename
            if header_name == os.path.basename(project_header):
                logging.info(f"Don't ever include {header_name} into {os.path.basename(project_header)}")
            elif header_name not in existing_includes:
                new_includes.append(f'#include "{header_name}"')

        if not new_includes:
            return   # No new includes to add
        
        logging.debug(f"\tFound {len(new_includes)} new includes: {', '.join(new_includes)}")

        # Find the insertion point
        marker = all_includes_marker
        insertion_point = content.find(marker)
        if insertion_point == -1:
            marker = convertor_marker
            insertion_point = content.find(marker)
            if insertion_point == -1:
                # If neither marker is found, find the end of the header guard
                marker = ""
                header_guard_end = re.search(r'#define\s+\w+_H\s*\n', content)
                if header_guard_end:
                    insertion_point = header_guard_end.end()
                else:
                    logging.info("\tCannot find suitable insertion point")
                    return  

        insertion_point += len(marker)
        # Insert new includes
        before = content[:insertion_point]
        after = content[insertion_point:]
        new_content = before + '\n' + '\n'.join(new_includes) + '\n' + after
        
        # Write the modified content back to the header file
        with open(project_header, 'w') as file:
            file.write(new_content)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def copy_project_files():
    """Copy .ino, .cpp, .c files to glob_pio_src and .h files to glob_pio_include."""
    logging.info("")
    logging.info("Processing: copy_project_files() ..")

    try:
        # Remove the arduinoGlue.h file
        # Check if the file exists
        arduinoGlue_path = os.path.join(glob_pio_include, "arduinoGlue.h")
        if os.path.exists(arduinoGlue_path):
            # Delete the file
            os.remove(arduinoGlue_path)
            logging.info("\t'arduinoGlue.h' has been deleted.")
        else:
          logging.info("\t'arduinoGlue.h' does not (yet) exist.")

        for file in os.listdir(glob_ino_project_folder):
            if file.endswith('.ino'):
                logging.debug(f"\tCopy [{file}] ..")
                shutil.copy2(os.path.join(glob_ino_project_folder, file), glob_pio_src)
            elif file.endswith('.cpp'):
                logging.debug(f"\tCopy [{file}] ..")
                shutil.copy2(os.path.join(glob_ino_project_folder, file), glob_pio_src)
            elif file.endswith('.c'):
                logging.debug(f"\tCopy [{file}] ..")
                shutil.copy2(os.path.join(glob_ino_project_folder, file), glob_pio_src)
            elif file.endswith('.h'):
                logging.debug(f"\tCopy [{file}] ..")
                shutil.copy2(os.path.join(glob_ino_project_folder, file), glob_pio_include)
                logging.info(f"\tProcessing original header file: {file}")
                base_name = os.path.splitext(file)[0]
                header_path = os.path.join(glob_pio_include, f"{base_name}.h")
                process_original_header_file(header_path, base_name)

        if args.debug:
            list_files_in_directory(glob_pio_src)
            list_files_in_directory(glob_pio_include)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()

    logging.debug("\tCopied project files to PlatformIO folders")

#------------------------------------------------------------------------------------------------------
def extract_all_includes_from_file(file_path):
    """
    Scans the file for (not commented out) "#include <..>" statements.
    Removes comments behind the "#include <..>" statement (if any) and adds the statement to an "includes" array.
    Adds a comment after the original include statement and modifies the file directly.

    Args:
    file_path (str): Path to the file to be processed.

    Returns:
    list: List of extracted include statements
    """
    includes = []

    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        modified_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("#include <"):
                include_match = re.match(r'(#include\s*<[^>]+>|#include\s*"[^"]+")', stripped_line)
                if include_match:
                    include_statement = include_match.group(1)
                    includes.append(include_statement)
                    # Remove original comment and add the new comment
                    modified_line = f"//{include_statement:<50}\t\t//-- moved to arduinoGlue.h\n"
                    modified_lines.append(modified_line)
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)

        # Write the modified content back to the file
        with open(file_path, 'w') as file:
            file.writelines(modified_lines)

        logging.info(f"Processed {os.path.basename(file_path)}")
        logging.info(f"Found and modified {len(includes)} include statements")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        return []

    return includes


#------------------------------------------------------------------------------------------------------
def extract_global_variables(file_path):
    """
    Extract global variable definitions from a single .ino, .cpp, or header file.
    Only variables declared outside of all function blocks are considered global.
    """
    logging.info("")
    logging.info(f"Processing: extract_global_variables() from : {os.path.basename(file_path)}")

    global_vars = {}

    # Get the fbase (filename without extension)
    file = os.path.basename(file_path)
    fbase = os.path.splitext(file)[0]

    # Check if there are existing entries in dict_global_variables for this fbase
    if fbase in dict_global_variables:
        global_vars[fbase] = dict_global_variables[fbase]
        logging.info(f"\t[1] Found {len(global_vars[fbase])} existing global variables for {fbase} in dict_global_variables")

    # More flexible type pattern to match any type, including custom types and structs
    type_pattern = r'(?:\w+(?:::\w+)*(?:\s*<[^>]+>)?(?:\s*\*)*)'

    # Updated patterns to catch all types of variables and class instances, including static
    var_pattern = rf'^\s*((?:static|volatile|const)?\s*{type_pattern})\s+((?:[a-zA-Z_]\w*(?:\[.*?\])?(?:\s*=\s*[^,;]+)?\s*,\s*)*[a-zA-Z_]\w*(?:\[.*?\])?(?:\s*=\s*[^,;]+)?)\s*;'
    class_instance_pattern = rf'^\s*((?:static)?\s*{type_pattern})\s+([a-zA-Z_]\w*)(?:\s*\(.*?\))?\s*;'
    func_pattern = rf'^\s*(?:static|volatile|const)?\s*{type_pattern}\s+([a-zA-Z_]\w*)\s*\((.*?)\)'
    struct_pattern = r'^\s*struct\s+([a-zA-Z_]\w*)\s*{'

    keywords = set(['if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
                    'break', 'continue', 'return', 'goto', 'typedef', 'struct', 'enum',
                    'union', 'sizeof', 'volatile', 'register', 'extern', 'inline',
                    'static', 'const', 'auto', 'virtual', 'void', 'class', 'public',
                    'private', 'protected', 'template', 'namespace', 'using', 'friend',
                    'operator', 'try', 'catch', 'throw', 'new', 'delete'])

    control_structures = set(['if', 'else', 'for', 'while', 'do', 'switch', 'case'])

    def is_in_string(line, pos):
        """Check if the given position in the line is inside a string literal."""
        in_single_quote = False
        in_double_quote = False
        escape = False
        for i, char in enumerate(line):
            if i >= pos:
                return in_single_quote or in_double_quote
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
        return False

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        scope_stack = []
        in_struct = False
        current_struct = None
        file_vars = []
        custom_types = set()
        potential_func_start = False
        func_parentheses_count = 0
        in_raw_string = False
        raw_string_delimiter = ''

        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()

            # Skip empty lines and comments
            if not stripped_line or stripped_line.startswith('//'):
                continue

            # Check for raw string literal start
            if not in_raw_string and 'R"' in stripped_line:
                raw_start = stripped_line.index('R"')
                if not is_in_string(stripped_line, raw_start):
                    in_raw_string = True
                    delimiter_end = stripped_line.index('(', raw_start)
                    raw_string_delimiter = stripped_line[raw_start+2:delimiter_end]

            # Check for raw string literal end
            if in_raw_string:
                end_delimiter = ')"' + raw_string_delimiter
                if end_delimiter in stripped_line:
                    in_raw_string = False
                    raw_string_delimiter = ''
                continue  # Skip processing this line if we're in a raw string

            # Check for control structures
            first_word = stripped_line.split()[0] if stripped_line else ''
            if first_word in control_structures:
                scope_stack.append('control')

            # Check for multi-line function declarations
            if potential_func_start:
                func_parentheses_count += stripped_line.count('(') - stripped_line.count(')')
                if func_parentheses_count == 0:
                    if stripped_line.endswith('{'):
                        scope_stack.append('function')
                    potential_func_start = False
                continue

            # Check for struct start
            struct_match = re.search(struct_pattern, stripped_line)
            if struct_match and not scope_stack:
                in_struct = True
                current_struct = struct_match.group(1)
                custom_types.add(current_struct)
                scope_stack.append('struct')

            # Check for function start
            func_match = re.search(func_pattern, stripped_line)
            if func_match and not scope_stack:
                if stripped_line.endswith('{'):
                    scope_stack.append('function')
                else:
                    potential_func_start = True
                    func_parentheses_count = stripped_line.count('(') - stripped_line.count(')')

            # Count braces
            if not potential_func_start:
                open_braces = stripped_line.count('{')
                close_braces = stripped_line.count('}')
                
                for _ in range(open_braces):
                    if not scope_stack or scope_stack[-1] == 'brace':
                        scope_stack.append('brace')
                    
                for _ in range(close_braces):
                    if scope_stack and scope_stack[-1] == 'brace':
                        scope_stack.pop()
                    elif scope_stack:
                        scope_stack.pop()
                        if not scope_stack:
                            in_struct = False
                            current_struct = None

            # Check for variable declarations only at global scope
            if not scope_stack and not stripped_line.startswith('return'):
                var_match = re.search(var_pattern, stripped_line)
                class_instance_match = re.search(class_instance_pattern, stripped_line)
                
                if var_match and not is_in_string(line, var_match.start()):
                    var_type = var_match.group(1).strip()
                    var_declarations = re.findall(r'([a-zA-Z_]\w*(?:\[.*?\])?)(?:\s*=\s*[^,;]+)?', var_match.group(2))
                    for var_name in var_declarations:
                        base_name = var_name.split('[')[0].strip()
                        if base_name.lower() not in keywords and not base_name.isdigit():
                            # Check for pointer in var_type or var_name
                            is_pointer = var_type.endswith('*') or var_name.startswith('*')
                            
                            # Remove asterisk from var_name if it starts with one
                            if var_name.startswith('*'):
                                var_name = var_name.lstrip('*').strip()
                                if not var_type.endswith('*'):
                                    var_type = var_type + '*'
                            
                            file_vars.append((var_type, var_name, None, is_pointer))
                            logging.debug(f"\t[1] Global variable found: [{var_type} {var_name}]")
                            if is_pointer:
                                logging.debug(f"\t\t[1] Pointer variable detected: [{var_type} {var_name}]")
                
                elif class_instance_match and not is_in_string(line, class_instance_match.start()):
                    var_type = class_instance_match.group(1).strip()
                    var_name = class_instance_match.group(2).strip()
                    if var_name.lower() not in keywords and not var_name.isdigit():
                        file_vars.append((var_type, var_name, None, False))
                        logging.debug(f"\t[1] Global class instance found: [{var_type} {var_name}]")

        # Remove duplicate entries
        unique_file_vars = list(set(file_vars))

        # Add new global variables to the existing ones
        if fbase in global_vars:
            global_vars[fbase].extend(unique_file_vars)
        else:
            global_vars[fbase] = unique_file_vars

        if unique_file_vars:
            logging.info(f"\t[1] Processed {os.path.basename(file_path)} successfully. Found {len(unique_file_vars)} new global variables.")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError processing file {file_path}: {str(e)}")
        exit()

    if global_vars[fbase]:
        logging.info(f"\t[1] Total global variables for {fbase}: {len(global_vars[fbase])}")
    else:
        logging.info("\t[1] No global variables found")

    return global_vars

#------------------------------------------------------------------------------------------------------
def extract_constant_pointers(file_path):
    """
    Extract constant pointer array definitions with initializers from a single .ino, .cpp, or header file.
    Only variables declared outside of all function blocks are considered.
    """
    logging.info("")
    logging.info(f"Processing: extract_constant_pointers() from : {os.path.basename(file_path)}")

    try:
        global_vars = {}

        # Get the fbase (filename without extension)
        file = os.path.basename(file_path)
        fbase = os.path.splitext(file)[0]

        # Check if there are existing entries in dict_global_variables for this fbase
        if fbase in dict_global_variables:
            global_vars[fbase] = dict_global_variables[fbase]
            logging.info(f"\t[2] Found {len(global_vars[fbase])} existing global variables for {fbase} in dict_global_variables")

        # Comprehensive list of object types, including String and dict_known_classes
        basic_types = r'uint8_t|int8_t|uint16_t|int16_t|uint32_t|int32_t|uint64_t|int64_t|char|int|float|double|bool|boolean|long|short|unsigned|signed|size_t|void|String|time_t|struct tm'

        # Regular expression to match const char* or const int* declarations
        pattern = rf'const\s+({basic_types})\s*\*\s*(\w+)\s*\[\]\s*{{' + r'\s*("[^"]*"\s*,\s*)*("[^"]*"\s*)\s*}|const\s+int\s*\*\s*(\w+)\s*{\s*\d+\s*(\s*,\s*\d+)*\s*};'
        
        file_vars = []

        with open(file_path, 'r') as file:
            content = file.read()

        # Remove comments
        content = re.sub(r'//.*?\n|/\*.*?\*/', '', content, flags=re.DOTALL)

        # Split content by semicolon to handle each declaration separately
        declarations = content.split(';')
        
        for declaration in declarations:
            # Remove leading and trailing whitespace and check if it's not empty
            declaration = declaration.strip()
            if not declaration:
                continue
            match = re.match(pattern, declaration)
            if match:
                var_type = f"const {match.group(1)}*"
                var_name = match.group(2) or match.group(5)  # Group 2 for array, group 5 for single pointer
                current_function = None
                is_pointer = True
                var_full_name = var_name +"[]"
                file_vars.append((var_type, var_full_name, current_function, is_pointer))
                logging.info(f"\t[2] Constant pointer found: [{var_type} {var_full_name}]")

        # Remove duplicate entries
        unique_file_vars = list(set(file_vars))

        # Add new global variables to the existing ones
        if fbase in global_vars:
            global_vars[fbase].extend(unique_file_vars)
        else:
            global_vars[fbase] = unique_file_vars

        if unique_file_vars:
            logging.info(f"\t[2] Processed {os.path.basename(file_path)} successfully. Found {len(unique_file_vars)} new constant pointers.")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError processing file {file_path}: {str(e)}")

    return global_vars

#------------------------------------------------------------------------------------------------------
def extract_undefined_vars_in_file(file_path):
    """
    Extract all variables that are used in the file but not properly defined.
    Check if the variable is in the global dict_global_variables array.
    If it's in dict_global_variables with a different base-name, add it to the 'undefined_vars' array.
    Variables not found in dict_global_variables or with unknown types are not added to the 'undefined_vars' array.
    
    Args:
    file_path (str): Path to the Arduino file (.ino or .cpp)
    
    Returns:
    dict: Dictionary of undefined variables used in the file, with their line numbers, file names, var_type, var_name, and defined file
    """
    logging.info("===========================")
    logging.info(f"Processing: extract_undefined_vars_in_file() for file: [{os.path.basename(file_path)}]")

    # List of C++ keywords and common Arduino types/functions to exclude
    KEYWORDS_AND_TYPES = set([
        "if", "else", "for", "while", "do", "switch", "case", "default", "break", "continue",
        "return", "goto", "try", "catch", "throw", "true", "false", "null", "const", "static",
        "volatile", "unsigned", "signed", "void", "char", "short", "int", "long", "float",
        "double", "bool", "String", "byte", "word", "boolean", "array", "sizeof", "setup",
        "loop", "HIGH", "LOW", "INPUT", "OUTPUT", "INPUT_PULLUP", "LED_BUILTIN", "serial"
    ])

    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Remove comments
        content = re.sub(r'//.*?\n|/\*.*?\*/', '', content, flags=re.DOTALL)

        undefined_vars = {}
        
        current_file_basename = os.path.splitext(os.path.basename(file_path))[0]
        
        # Find all variable declarations in the file
        declarations = re.findall(r'\b(?:const\s+)?(?:unsigned\s+)?(?:static\s+)?(?:volatile\s+)?\w+\s+([a-zA-Z_]\w*)(?:\s*=|\s*;|\s*\[)', content)
        declared_vars = {var for var in declarations if var not in KEYWORDS_AND_TYPES and not var.isdigit()}
        logging.debug(f"Variables declared in file: {declared_vars}")
        
        # Find all variables used in the file
        used_vars = re.findall(r'\b([a-zA-Z_]\w*)\b', content)
        used_vars = [var for var in used_vars if var not in KEYWORDS_AND_TYPES and not var.isdigit()]
        logging.debug(f"Variables used in file: {set(used_vars)}")
        
        # Identify potentially undefined variables
        for var in set(used_vars) - declared_vars:
            # Check if the variable is in dict_global_variables
            var_found = False
            var_type = 'Unknown'
            defined_in = 'Undefined'
            global_var_name = var
            v_is_pointer = False
            
            for defined_file, file_vars in dict_global_variables.items():
                defined_file_basename = os.path.splitext(os.path.basename(defined_file))[0]
                for v_type, v_name, is_pointer, _ in file_vars:
                    if v_name == var or (not '[' in var and re.match(rf'^{re.escape(var)}\[', v_name)):
                        var_found = True
                        var_type = v_type
                        defined_in = defined_file_basename
                        global_var_name = v_name  # Store the name as found in dict_global_variables
                        v_is_pointer = is_pointer
                        if defined_file_basename == current_file_basename:
                            # Variable is defined in the same file, so it's not undefined
                            if args.debug:
                                logging.info(f"Variable {var} found in global variables of the same file")
                            break
                if var_found:
                    break
            
            if var_found and defined_in != current_file_basename and var_type != 'Unknown':
                # Find the first occurrence of the variable in the file
                match = re.search(r'\b' + re.escape(var) + r'\b', content)
                if match:
                    line_number = content[:match.start()].count('\n') + 1
                    key = f"{global_var_name}+{current_file_basename}"
                    undefined_vars[key] = {
                        'var_type': var_type,
                        'var_is_pointer': v_is_pointer,
                        'var_name': global_var_name,
                        'used_in': current_file_basename,
                        'defined_in': defined_in,
                        'line': line_number
                    }
                    logging.debug(f"Added usage of {global_var_name} to undefined_vars: {undefined_vars[key]}")

            elif not var_found or var_type == 'Unknown':
                logging.debug(f"Variable {var} not found in dict_global_variables or has unknown type, skipping")
    
        logging.debug(f"Final undefined_vars: {undefined_vars}")
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"Error extract_undefined_vars_in_file at line {line_number}: {str(e)}")
        exit()
    
    return undefined_vars

#------------------------------------------------------------------------------------------------------
def extract_prototypes(file_path):
    """
    Extract function prototypes from a given file.
    
    Args:
    file_path (str): Path to the file to be processed.
    
    Returns:
    dict: Dictionary of function prototypes found in the file, with (function name, parameters) as keys and tuples (prototype, file_path, bare_function_name) as values.
    """
    logging.info("")
    logging.info(f"Processing: extract_prototypes() from file: [{os.path.basename(file_path)}]")
    
    prototypes = {}
    
    # Regex pattern for function header
    pattern = r'^\s*(?:static\s+|inline\s+|virtual\s+|explicit\s+|constexpr\s+)*' \
              r'(?:const\s+)?' \
              r'(?:\w+(?:::\w+)*\s+)+' \
              r'[\*&]?\s*' \
              r'(\w+)\s*\(((?:[^()]|\([^()]*\))*)\)\s*{'

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove comments and string literals
        content = re.sub(r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"', '', content, flags=re.DOTALL | re.MULTILINE)
        
        matches = re.finditer(pattern, content, re.MULTILINE)
        
        for match in matches:
            func_name = match.group(1)
            params = match.group(2)
            
            # Skip if the function name starts with "if", "else", "for", "while", etc.
            if func_name.lower() in ['if', 'else', 'for', 'while', 'switch', 'case']:
                continue
            
            # Skip "setup" and "loop" functions in .ino files
            if file_path.lower().endswith('.ino') and func_name in ['setup', 'loop']:
                continue
            
            # Reconstruct the prototype
            prototype = match.group(0).strip()[:-1]  # remove the opening brace
            prototype = ' '.join(prototype.split())  # normalize whitespace
            
            # Use (func_name, params) as the key
            key = (func_name, params.strip())
            prototypes[key] = (prototype, os.path.basename(file_path), func_name)
            
            logging.debug(f"\tExtracted prototype [{prototype}]")
        
        if not prototypes:
            logging.debug(f"\tNo function prototypes found in {os.path.basename(file_path)}")
    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()
    
    return prototypes


#------------------------------------------------------------------------------------------------------
def extract_class_instances(file_path):
    """
    Extract class instance definitions from a single .ino, .cpp, or .h file.
    Includes both global and function-local class instance declarations.
    """
    logging.info("")
    logging.info(f"Processing: extract_class_instances() from: {short_path(file_path)}")

    file  = os.path.basename(file_path)
    fbase = os.path.splitext(file)[0]

    class_instances = {}
    
    # Read already found instances from the global dict_class_instances
    if file_path in dict_class_instances:
        class_instances[file_path] = dict_class_instances[file_path]
    
    # Pattern for class instance declarations
    class_pattern = r'^\s*([A-Z]\w+(?:<.*?>)?)\s+(\w+)(?:\s*\((.*?)\))?\s*;'
    # Pattern for function definitions
    function_pattern = r'^\s*(?:(?:void|int|float|double|char|bool|auto)\s+)?(\w+)\s*\([^)]*\)\s*{'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        file_instances = []
        included_headers = set()
        current_function = None
        
        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # Check for function definition
            func_match = re.search(function_pattern, stripped_line)
            if func_match:
                current_function = func_match.group(1)
            
            # Check for closing brace to exit function context
            if stripped_line == '}' and current_function:
                current_function = None
            
            class_match = re.search(class_pattern, stripped_line)
            if class_match:
                class_type = class_match.group(1).strip()
                instance_name = class_match.group(2).strip()
                constructor_args = class_match.group(3).strip() if class_match.group(3) else ""
                context = f"global" if not current_function else f"in function {current_function}"
                logging.info(f"Match found on line {line_num} ({context}): {class_type} {instance_name}")
                
                # Check if it's a valid class type (starts with uppercase and is either in known_classes or matches the pattern)
                if class_type[0].isupper() and (class_type in dict_known_classes or re.match(r'^[A-Z]\w+$', class_type)):
                    # Check if the class is in dict_singleton_classes values
                    singleton_header = None
                    for header, classes in dict_singleton_classes.items():
                        if class_type in classes:
                            singleton_header = header
                            break
                    
                    if singleton_header:
                        if singleton_header not in included_headers:
                            file_instances.append((singleton_header, "", "singleton", fbase))
                            included_headers.add(singleton_header)
                            logging.info(f"{fbase}: Added include for singleton header {singleton_header} (class {class_type})")
                        logging.info(f"{fbase}: Class {class_type} {instance_name} is a singleton, including header {singleton_header}")
                    else:
                        file_instances.append((class_type, instance_name, constructor_args, fbase))
                        logging.info(f"{fbase}: Added {class_type} {instance_name} ({context})")
                else:
                    logging.info(f"Skipping invalid class type: {class_type}")
        
        # Check global dict_singleton_classes for objects
        for header, classes in dict_singleton_classes.items():
            for class_type in classes:
                if class_type in content and header not in included_headers:
                    logging.info(f"\t\tFound singleton class [{class_type}] in [{header}]")
                    file_instances.append((header, "-", "=", fbase))
                    included_headers.add(header)
                    logging.debug(f"{fbase}: Added include for singleton header {header}")
        
        if file_instances:
            class_instances[file_path] = file_instances
        else:
            logging.info(f"\t>> No class instances found.")
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        return class_instances
    
    if (len(file_instances) > 0):
        logging.info(f"\tExtracted class instances from {os.path.basename(file_path)} -> found: {len(file_instances)}")

    return class_instances

#------------------------------------------------------------------------------------------------------
def update_arduinoglue_with_includes(dict_all_includes):
    logging.info("")
    logging.info("Processing: update_arduinoglue_with_includes()")

    global all_includes_added

    try:
        glue_path = os.path.join(glob_pio_include, "arduinoGlue.h")
        with open(glue_path, "r") as file:
            content = file.read()

        insert_pos = find_marker_position(content, all_includes_marker)
        
        new_content = content[:insert_pos] # + "\n"

        for include in dict_all_includes:
            logging.debug(f"Added:\t{include}")
            new_content += f"{include}\n"
            all_includes_added = True
        new_content += "\n"

        new_content += content[insert_pos:]

        with open(glue_path, "w") as file:
            file.write(new_content)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def update_arduinoglue_with_global_variables(dict_global_variables):
    logging.info("")
    logging.info("Processing: update_arduinoglue_with_global_variables()")

    global extern_variables_added

    try:
        glue_path = os.path.join(glob_pio_include, "arduinoGlue.h")
        with open(glue_path, "r") as file:
            content = file.read()

        insert_pos = find_marker_position(content, extern_variables_marker)
        
        new_content = content[:insert_pos] # + "\n"

        sorted_global_vars = sort_global_vars(dict_global_variables)
        for file_path, vars_list in sorted_global_vars.items():
            if vars_list:  # Only print for files that have global variables
                for var_type, var_name, function, is_pointer in vars_list:
                    var_name += ';'
                    if var_type.startswith("static "):
                        logging.debug(f"\t\t\tFound static variable [{var_type}] (remove \'static\' part)")
                        var_type = var_type.replace("static ", "").strip()  # Remove 'static' and any leading/trailing spaces
                    logging.debug(f"Added:\textern {var_type:<15} {var_name:<35}\t\t//-- from {file_path})")
                    new_content += (f"extern {var_type:<15} {var_name:<35}\t\t//-- from {file_path}\n")
                    extern_variables_added = True
        new_content += "\n"

        new_content += content[insert_pos:]

        with open(glue_path, "w") as file:
            file.write(new_content)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def update_arduinoglue_with_prototypes(dict_prototypes):
    logging.info("")
    logging.info("Processing: update_arduinoglue_with_prototypes()")

    global prototypes_added

    try:
        glue_path = os.path.join(glob_pio_include, "arduinoGlue.h")
        with open(glue_path, "r") as file:
            content = file.read()

        insert_pos = find_marker_position(content, prototypes_marker)
        
        new_content = content[:insert_pos] # + "\n"

        sav_file = ""
        for key, value in dict_prototypes.items():
            func_name, params = key
            prototype, file_name, bare_func_name = value
            if sav_file != file_name:
                sav_file = file_name
                logging.debug(f"Added:\t//-- from {file_name} ----------")
                new_content += (f"//-- from {file_name} -----------\n")
                prototypes_added = True
            prototype_sm = prototype + ';'
            logging.debug(f"Added:\t{prototype_sm}")
            new_content += (f"{prototype_sm:<60}\n")
        new_content += "\n"

        new_content += content[insert_pos:]

        with open(glue_path, "w") as file:
            file.write(new_content)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def remove_unused_markers_from_arduinoGlue():
    logging.info("Processing: remove_unused_markers_from_arduinoGlue()")
    glue_path = os.path.join(glob_pio_include, "arduinoGlue.h")
    logging.info(f"GluePath: {glue_path}")

    try:
        with open(glue_path, 'r') as file:
            content = file.read()

        #debug#logging.info("File content:")
        #debug#logging.info(content)

        original_content = content  # Store original content for comparison

        markers = {
            all_includes_marker: 'all_includes_added',
            struct_union_and_enum_marker: 'struct_union_and_enum_added',
            extern_variables_marker: 'extern_variables_added',
            global_pointer_arrays_marker: 'global_pointer_arrays_added',
            extern_classes_marker: 'extern_classes_added',
            prototypes_marker: 'prototypes_added',
            convertor_marker: 'convertor_added'
        }

        # Create a list of all markers for the regex pattern
        all_markers = '|'.join(re.escape(m) for m in markers.keys())

        for marker, test_var in markers.items():
            logging.debug(f"\tChecking marker: {marker}")
            if not globals().get(test_var, False):
                logging.info(f"\tRemoving unused marker: {marker}")
                # Pattern to match from this marker to the next marker or #endif
                pattern = f'({re.escape(marker)}).*?(?={all_markers}|#endif)'
                #debug#logging.info(f"\tSearch pattern: {pattern}")
                matches = re.findall(pattern, content, flags=re.DOTALL)
                if matches:
                    for match in matches:
                        logging.debug(f"\tFound match: {match}")
                    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
                    if new_content != content:
                        logging.debug(f"\tMarker {marker} successfully removed")
                        content = new_content
                    else:
                        logging.info(f"\tNo change for marker {marker} despite matches")
                else:
                    logging.info(f"\tNo matches found for marker {marker}")

        # Ensure we keep the #endif line
        if '#endif' not in content:
            content += '\n#endif // ARDUINOGLUE_H\n'

        if content != original_content:
            with open(glue_path, 'w') as file:
                file.write(content)
            logging.info("File updated 'arduinoGlue.h'successfully")
        else:
            logging.info("No changes were necessary for 'arduinoGlue.h'")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"An error occurred at line {line_number}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def insert_class_instances_to_header_files(file_name):
    logging.info("")
    logging.info(f"Processing: insert_class_instances_to_header_files() [{os.path.splitext(os.path.basename(file_name))[0]}]")
    
    global dict_class_instances

    try:
        # Generate the corresponding .h file name
        file_base = os.path.basename(file_name)
        header_base = os.path.splitext(file_base)[0] + ".h"
        header_file = os.path.join(glob_pio_include, header_base)
        logging.info(f"\t\tprocessing [{file_base}] and [{header_base}]")
        
        # Check if the .h file exists, if not, create it
        if not os.path.exists(header_file):
            with open(header_file, 'w') as f:
                file_name = os.path.splitext(header_base)[0]
                f.write(f"#ifndef _{file_name.upper()}_H_\n")
                f.write(f"#define _{file_name.upper()}_H_\n\n")
                f.write(f"{all_includes_marker}\n\n")
                f.write(f"#endif // _{file_name.upper()}_H_\n")
            logging.info(f"\tCreated header file: {short_path(header_file)}")
        
        # Read the content of the .h file
        with open(header_file, 'r') as f:
            header_content = f.read()

        # Get the class instances for this file
        file_instances = []
        for file_path, instances in dict_class_instances.items():
            if os.path.split(os.path.basename(file_path))[0] == os.path.split(os.path.basename(header_file))[0]:
                file_instances = instances
                break
        
        logging.info(f"\t\t>> Found {len(file_instances)} class instances for [{file_base}]")

        # Process regular class instances and singleton includes
        includes_to_add = set()
        for instance in file_instances:
            class_name = instance[0]
            logging.info(f"\t\tChecking if {class_name} ...")
            # Check if it's a singleton include (ends with .h)
            if class_name.endswith('.h'):
                include_pattern = rf'#include\s*<{re.escape(class_name)}>\s*(//.*)?$'
                if not re.search(include_pattern, header_content, re.MULTILINE):
                    includes_to_add.add(f'#include <{class_name}>\t\t//== singleton')
                    logging.info(f"\t\tAdding: #include <{class_name}>\t\t//== singleton")
                else:
                    logging.info(f"\t\tSkipping (already exists): #include <{class_name}>")
            else:
                # Check if the class is in dict_singleton_classes
                singleton_header = None
                for header, classes in dict_singleton_classes.items():
                    if class_name in classes:
                        singleton_header = header
                        break
                
                if singleton_header:
                    include_pattern = rf'#include\s*<{re.escape(singleton_header)}>\s*(//.*)?$'
                    if not re.search(include_pattern, header_content, re.MULTILINE):
                        includes_to_add.add(f'#include <{singleton_header}>\t\t//-- singleton')
                        logging.info(f"\t\tAdding: #include <{singleton_header}>\t\t//-- singleton")
                    else:
                        logging.info(f"\t\tSkipping (already exists): #include <{singleton_header}>")
                else:
                    include_pattern = rf'#include\s*<{re.escape(class_name)}\.h>\s*(//.*)?$'
                    if not re.search(include_pattern, header_content, re.MULTILINE):
                        includes_to_add.add(f'#include <{class_name}.h>\t\t//-- class')
                        logging.info(f"\t\tAdding: #include <{class_name}.h>\t\t//-- class")
                    else:
                        logging.info(f"\t\tSkipping (already exists): #include <{class_name}.h>")

        logging.info(f"includes to add: {includes_to_add}")
        # Find the position to insert the new includes and insert them
        insert_pos = find_marker_position(header_content, all_includes_marker)
        if insert_pos != -1:
            new_includes = '\n'.join(includes_to_add)
            logging.info(f"\t\tnew includes: [{new_includes}]")
            updated_content = (
                header_content[:insert_pos] +
                new_includes + '\n' +
                header_content[insert_pos:]
            )
        else:
            updated_content = header_content
            insert_pos = 0
            logging.warning(f"\t\tCould not find marker {all_includes_marker} in {short_path(header_file)}")

        # Write the updated content back to the .h file
        with open(header_file, 'w') as f:
            f.write(updated_content)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"An error occurred at line {line_number}: {str(e)}")
        logging.error(f"An error occurred during conversion: {str(e)}")

    logging.info(f"Finished inserting class instances to header file [{file_base}].")

#------------------------------------------------------------------------------------------------------
def update_header_with_prototypes(header_path, prototypes):
    """Update header file with function prototypes."""
    logging.info()
    logging.info(f"Processing: update_header_with_prototypes() file: {os.path.basename(header_path)}")

    marker_index = header_path.find(platformio_marker)
    if marker_index != -1:
        short_header_path = header_path[marker_index + len(platformio_marker):]
    else:
        short_header_path = header_path

    with open(header_path, 'r+') as f:
        content = f.read()

        # Search for the prototype insertion marker
        insert_start = content.find(f"{prototypes_marker}")
        if insert_start != -1:
            insert_pos = insert_start + len(f"{prototypes_marker}\n")
        else:
            insert_start = -1

        # If marker is not found, search for the last #include statement
        if insert_start == -1:
            include_matches = list(re.finditer(r'#include\s*<[^>]+>', content))
            if include_matches:
                insert_pos = include_matches[-1].end() + 1  # Position after the last #include
            else:
                # If no #include statement, search for header guard
                header_guard_match = re.search(r'#ifndef\s+\w+\s+#define\s+\w+', content, re.MULTILINE)
                if header_guard_match:
                    insert_pos = header_guard_match.end() + 1  # Position after the header guard
                else:
                    # If no header guard, insert at the top of the file
                    insert_pos = 0

        # Gather existing prototypes to avoid duplication
        existing_prototypes = set(re.findall(r'^[^\S\r\n]*(?:extern\s+)?\w[\w\s\*\(\),]*\s*\([^;]*\);', content[insert_pos:], re.MULTILINE))
        prototypes_to_add = set(prototypes) - existing_prototypes

        if prototypes_to_add:
            new_content = (content[:insert_pos] +
                           '\n'.join(sorted(prototypes_to_add)) + '\n\n' +
                           content[insert_pos:])
            f.seek(0)
            f.write(new_content)
            f.truncate()
            logging.info(f"\tAdded {len(prototypes_to_add)} function prototypes to [{os.path.basename(header_path)}]")
            for prototype in prototypes_to_add:
                logging.info(f"  - {prototype}")
        else:
            logging.info(f"\tNo new function prototypes added to [{os.path.basename(header_path)}]")


#------------------------------------------------------------------------------------------------------
def find_undefined_functions_and_update_headers(glob_pio_src, glob_pio_include, function_reference_array):
    """
    Find undefined functions in glob_pio_src files and update corresponding header files.
    """
    NON_FUNCTION_KEYWORDS = {'if', 'else', 'for', 'while', 'switch', 'case', 'default', 'do', 'return', 'break', 'continue'}

    logging.info()
    logging.info("Processing: find_undefined_functions_and_update_headers")

    for file in os.listdir(glob_pio_src):
        if file.endswith('.cpp'):
            file_path = os.path.join(glob_pio_src, file)
            base_name = os.path.splitext(file)[0]
            header_path = os.path.join(glob_pio_include, f"{base_name}.h")

            marker_index = header_path.find(platformio_marker)
            if marker_index != -1:
                short_header_path = header_path[marker_index + len(platformio_marker):]
            else:
                short_header_path = header_path

            with open(file_path, 'r') as f:
                content = f.read()

            # Find all function calls
            function_calls = set(re.findall(r'\b(\w+)\s*\(', content))

            # Find local function definitions
            local_functions = set(re.findall(r'\b\w+[\s\*]+(\w+)\s*\([^)]*\)\s*{', content))

            # Determine which functions are undefined in this file
            undefined_functions = function_calls - local_functions

            # Check which undefined functions are in the function_reference_array
            functions_to_include = [func for func in undefined_functions if func in function_reference_array]
            
            if functions_to_include:
                logging.info(f"\tFunctions to include in {file}:")
                for func in functions_to_include:
                    logging.info(f"\t>> {func} - {function_reference_array[func]}")

                # Update the header file
                with open(header_path, 'r') as f:
                    header_content = f.read()

                new_includes = []
                for func in functions_to_include:
                    include_file = function_reference_array[func]
                    # Ensure we don't include the file in itself
                    if include_file != f"{base_name}.h":
                        include_statement = f'#include "{include_file}\t\t//== by convertor"'
                        if include_statement not in header_content:
                            new_includes.append(include_statement)

                if new_includes:
                    # Find the position to insert new includes
                    marker = extern_classes_marker
                    insert_pos = header_content.find(f"{marker}")
                    if insert_pos == -1:
                        marker = all_includes_marker
                        insert_pos = header_content.find(f"{marker}")
                        if insert_pos == -1:
                            marker = convertor_marker
                            insert_pos = header_content.find(f"{marker}")
                            if insert_pos == -1:
                                marker = ""
                                header_guard_end = re.search(r'#define\s+\w+_H\s*\n', header_content)
                                if header_guard_end:
                                    insert_pos = header_guard_end.end()
                                else:
                                    logging.info("\t\tCannot find suitiblae insertion point")
                                    return  

                    insert_pos += len(f"{marker}\n")
                    updated_content = (
                        header_content[:insert_pos] +
                        '\n'.join(new_includes) + '\n' +
                        header_content[insert_pos:]
                    )

                    # Write the updated content back to the header file
                    with open(header_path, 'w') as f:
                        f.write(updated_content)

                    logging.info(f"\tUpdated {short_header_path} with new includes:")
                    for include in new_includes:
                        logging.info(f"  - {include}")
                else:
                    logging.warning(f"\tCould not find '{all_includes_marker}' in {short_header_path}")
            else:
                logging.info(f"\tNo new includes needed for {short_header_path}")
        else:
            logging.info(f"\tNo undefined functions found in {file} that need to be included")

    logging.info("\tCompleted finding undefined functions and updating headers")

#------------------------------------------------------------------------------------------------------
def process_function_references(glob_pio_src, glob_pio_include):
    logging.info()
    logging.info("Process process_function_references()")

    function_reference_array = {}

    # Collect all function prototypes from header files
    for file in os.listdir(glob_pio_include):
        if file.endswith('.h'):
            with open(os.path.join(glob_pio_include, file), 'r') as f:
                content = f.read()
            prototypes = re.findall(r'^\w+[\s\*]+(\w+)\s*\([^)]*\);', content, re.MULTILINE)
            for func_name in prototypes:
                function_reference_array[func_name] = file

    # Print the function reference array
    logging.info("\tFunction Reference Array:")
    for func, file in function_reference_array.items():
        logging.info(f"{func}: {file}")

    # Process .ino files
    for file in os.listdir(glob_pio_src):
        if file.endswith('.ino') or file.endswith('.cpp'):
            base_name = os.path.splitext(file)[0]
            source_path = os.path.join(glob_pio_src, file)
            header_path = os.path.join(glob_pio_include, f"{base_name}.h")

            with open(source_path, 'r') as f:
                content = f.read()

            # Find all function calls
            function_calls = set(re.findall(r'\b(\w+)\s*\(', content))

            # Find local function definitions
            local_functions = set(re.findall(r'\b\w+[\s\*]+(\w+)\s*\([^)]*\)\s*{', content))

            # Determine which functions need to be included
            functions_to_include = function_calls - local_functions

            headers_to_include = set()
            for func in functions_to_include:
                if func in function_reference_array:
                    headers_to_include.add(function_reference_array[func])
                    insert_include_in_header(header_path, function_reference_array[func])

            # Update the header file with necessary includes
            #aaw#if headers_to_include:
                #aaw#insert_include_in_header(header_path, function_reference_array[func])

    logging.info("\tProcessed function references and updated header files")
    return function_reference_array  # Return the function_reference_array


#------------------------------------------------------------------------------------------------------
def add_guards_and_marker_to_header(file_path):
    logging.info("")
    logging.info(f"Processing: add_guards_and_marker_to_header() file: [{os.path.basename(file_path)}]")
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Replace multiple empty lines with a single empty line
    content = re.sub(r'\n\s*\n', '\n\n', content)
    
    lines = content.splitlines()
    
    # Check for existing header guard
    has_header_guard = False
    if len(lines) >= 2 and lines[0].strip().startswith("#ifndef") and lines[1].strip().startswith("#define"):
        has_header_guard = True
        logging.info("\tHeader guard already present.")
    
    # Add header guard if not present
    if not has_header_guard:
        guard_name = f"{os.path.basename(file_path).upper().replace('.', '_')}_"
        lines.insert(0, f"#ifndef {guard_name}")
        lines.insert(1, f"#define {guard_name}")
        lines.append(f"#endif // {guard_name}")
        logging.info("\tAdded header guard.")
    
    # Find the last #include statement
    last_include_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("#include"):
            last_include_index = i
    
    # Determine where to insert the CONVERTOR marker
    if last_include_index != -1:
        insert_index = last_include_index + 1
        logging.info(f"\tInserting marker after last #include statement (line {insert_index + 1})")
    else:
        # If no #include, insert after header guard or at the beginning
        insert_index = 2 if has_header_guard else 0
        logging.info(f"\tInserting marker at the beginning of the file (line {insert_index + 1})")
    
    # Insert the CONVERTOR marker
    lines.insert(insert_index, "")
    lines.insert(insert_index + 1, convertor_marker)
    lines.insert(insert_index + 2, "")

    modified_content = "\n".join(lines)

    with open(file_path, 'w') as file:
        file.write(modified_content)
    
    logging.info(f"\tFile {os.path.basename(file_path)} has been successfully modified.")

#------------------------------------------------------------------------------------------------------
def insert_header_include_in_cpp(file_path):
    logging.info("")
    logging.info(f"Processing: insert_header_include_in_cpp(): [{os.path.basename(file_path)}]")
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    lines = content.splitlines()
    
    # Generate the include statement
    basename = os.path.splitext(os.path.basename(file_path))[0]
    include_statement = f'#include "{basename}.h"'
    
    # Check if the include statement already exists
    if any(line.strip() == include_statement for line in lines):
        logging.info(f"\tInclude statement '{include_statement}' already exists. No changes made.")
        return
    
    # Find the end of the first comment
    in_multiline_comment = False
    insert_index = 0
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        if in_multiline_comment:
            if "*/" in line:
                insert_index = i + 1
                break
        elif stripped_line.startswith("//"):
            insert_index = i + 1
            break
        elif stripped_line.startswith("/*"):
            in_multiline_comment = True
            if "*/" in line:
                insert_index = i + 1
                break
        elif stripped_line and not stripped_line.startswith("#"):
            # If we've reached a non-empty, non-comment, non-preprocessor line, stop searching
            break
    
    # Insert the include statement
    lines.insert(insert_index, include_statement)
    
    modified_content = "\n".join(lines)
    
    with open(file_path, 'w') as file:
        file.write(modified_content)
    
    logging.info(f"\tInserted '{include_statement}' at line {insert_index + 1}")
    logging.info(f"\tFile {os.path.basename(file_path)} has been successfully modified.")

#------------------------------------------------------------------------------------------------------
def preserve_original_headers():
    """Read and preserve the original content of all existing header files."""
    logging.info("")
    logging.info("Processing: preserve_original_headers() ..")

    original_headers = {}
    for file in os.listdir(glob_pio_include):
        if file.endswith('.h'):
            header_path = os.path.join(glob_pio_include, file)
            with open(header_path, 'r') as f:
                original_headers[file] = f.read()

    return original_headers


#------------------------------------------------------------------------------------------------------
def update_project_header(glob_pio_include, glob_project_name, original_content):
    """Update project header file with includes for all created headers while preserving original content."""
    logging.info("")
    logging.info("Processing: update_project_header() ..")

    project_header_path = os.path.join(glob_pio_include, f"{glob_project_name}.h")

    # Split the original content into sections
    sections = re.split(r'(//==.*?==)', original_content, flags=re.DOTALL)

    new_content = []
    local_includes = []

    # Process each section
    for i, section in enumerate(sections):
        if section.strip() == f"{all_includes_marker}":
            # Add new local includes here
            new_content.append(section + "\n")
            for file in os.listdir(glob_pio_include):
                if file.endswith('.h') and file != f"{glob_project_name}.h":
                    include_line = f'#include "{file}"\n'
                    if include_line not in original_content:
                        new_content.append(include_line)
            new_content.append("\n")
        elif i == 0:  # First section (before any //== markers)
            new_content.append(section)
            # Add system includes if they don't exist
            if "#include <Arduino.h>" not in section:
                new_content.append("#include <Arduino.h>\n")
            if "#include \"arduinoGlue.h\"" not in section:
                new_content.append("#include \"arduinoGlue.h\"\n")
        else:
            new_content.append(section)

    # Write the updated content back to the file
    with open(project_header_path, 'w') as f:
        f.writelines(new_content)

    logging.info(f"\tUpdated project header {glob_project_name}.h while preserving original content")



#------------------------------------------------------------------------------------------------------
def main():
    global glob_ino_project_folder, glob_project_name, glob_pio_folder, glob_pio_src, glob_pio_include
    global args

    args = parse_arguments()
    setup_logging(args.debug)

    logging.info(f"Global project dir is [%s]", args.project_dir)

    # Backup the original project if requested
    #if args.backup:
    #    backup_project(args.project_dir)

    try:
        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 1] Setup the folder structure for a PlatformIO project")
        logging.info("=======================================================================================================")

        set_glob_project_info(args.project_dir)
        logging.info(f"           Project folder: {glob_ino_project_folder}")

        marker = "arduinoIDE2platformIO-convertor"
        logging.info(f"\t        PlatformIO folder: {short_path(glob_pio_folder)}")
        logging.info(f"\t    PlatformIO src folder: {short_path(glob_pio_src)}")
        logging.info(f"\tPlatformIO include folder: {short_path(glob_pio_include)}")

        remove_pio_tree("platformio.ini")

        recreate_pio_folders()

        if not os.path.exists(glob_pio_folder):
            logging.error(f"PlatformIO folder does not exist: {glob_pio_folder}")
            return

        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 2] Copy all .ino, .cpp, .c and .h files from the Arduino project")
        logging.info( "         Copy the data folder (if it excists) from the Arduino project")
        logging.info( "         Create the platformio.ini file")
        logging.info( "         Extract all #define statements from all .ino and .h files")
        logging.info("=======================================================================================================")

        copy_project_files()
        copy_data_folder()
        create_platformio_ini()
        create_arduinoglue_file()
        extract_and_comment_defines()
        move_struct_union_and_enum_declarations()


        search_folders = [glob_pio_src, glob_pio_include]

        list_files_in_directory(glob_pio_src)

        logging.info("")
        logging.info("=======================================================================================================")
        logging.info("[Step 3] Process all '.ino' and 'h' files extracting includes, global variables and ")
        logging.info("         prototypes.. and insert Header Guards in all existing header files")
        logging.info("=======================================================================================================")

        for folder in search_folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(('.h', '.ino')):
                        file_path = os.path.join(root, file)
                        base_name = os.path.basename(file)  # Get the basename without extension
                        logging.info("")
                        logging.debug("-------------------------------------------------------------------------------------------------------")
                        logging.debug(f"Processing file: {short_path(file_path)} basename: [{base_name}]")

                        lib_includes = extract_all_includes_from_file(file_path)
                        if args.debug:
                          print_includes(lib_includes)
                        dict_all_includes.update({include: None for include in lib_includes})
                        global_vars = extract_global_variables(file_path)
                        if args.debug:
                            print_global_vars(global_vars)
                        dict_global_variables.update(global_vars)
                        global_vars = extract_constant_pointers(file_path)
                        if args.debug:
                            print_global_vars(global_vars)
                        dict_global_variables.update(global_vars)
                        prototypes = extract_prototypes(file_path)
                        if args.debug:
                            print_prototypes(prototypes)
                        dict_prototypes.update(prototypes)

                        if file.endswith('.h') and file != "arduinoGlue.h":
                            add_guards_and_marker_to_header(file_path)

        logging.info("")
        logging.info("And now the complete list of #includes:")
        print_includes(dict_all_includes)
        logging.info("And now the complete list of global variables:")
        print_global_vars(dict_global_variables)
        logging.info("And now the complete list of prototypes:")
        print_prototypes(dict_prototypes)

        logging.info("And now add all dict's to arduinoGlue.h:")
        update_arduinoglue_with_includes(dict_all_includes)
        update_arduinoglue_with_global_variables(dict_global_variables)
        update_arduinoglue_with_prototypes(dict_prototypes)

        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 4] Create new header files for all '.ino' files")
        logging.info("=======================================================================================================")

        for filename in os.listdir(glob_pio_src):
            logging.debug(f"Processing file: {os.path.basename(filename)}")
            ino_name    = os.path.basename(filename)
            base_name   = os.path.splitext(ino_name)[0]  # Get the basename without extension
            header_name = ino_name.replace(".ino", ".h")
            if filename.endswith(".ino"):
                create_new_header_file(ino_name, header_name)

        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 5] add all local includes to the 'project_name.ino' file  (insert '#include \"x.h\"' to x.ino)")
        logging.info("=======================================================================================================")

        #-- add all local includes to {project_name}.h
        add_local_includes_to_project_header()

        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 6] rename all '.ino' files to '.cpp'")
        logging.info("=======================================================================================================")

        for filename in os.listdir(glob_pio_src):
            logging.debug(f"Found file: {os.path.basename(filename)}")
            ino_name = os.path.basename(filename)
            base_name = os.path.splitext(ino_name)[0]  # Get the basename without extension
            header_name = ino_name.replace(".ino", ".h")
            if filename.endswith(".ino"):
                ino_path = os.path.join(glob_pio_src, filename)
                cpp_name = ino_name.replace(".ino", ".cpp")
                cpp_path = os.path.join(glob_pio_src, cpp_name)
                rename_file(ino_path, cpp_path)
                insert_header_include_in_cpp(cpp_path)

        remove_unused_markers_from_arduinoGlue()
        
        logging.info("")
        logging.info("*************************************************************")
        logging.info("** Arduino to PlatformIO conversion completed successfully **")
        logging.info("*************************************************************")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        #fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        line_number = exc_tb.tb_lineno
        logging.error(f"An error occurred at line {line_number}: {str(e)}")
        logging.error(f"An error occurred during conversion: {str(e)}")

#======================================================================================================
if __name__ == "__main__":
    main()


#*******************************************************************************************
# MIT License
# 
#  Copyright (c) 2024 Willem Aandewiel
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#  
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#************************************************************************************************
