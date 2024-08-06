#------------------------------------------------------------
#
#   convert a ArduinoIDE project to a PlatformIO project
#
#   file name : arduinoIDE2platformIO.py   
#
#   by        : Willem Aandewiel
#
#   Version   : v0.7 (06-08-2024)
#
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

args                      = None
glob_project_name         = ""
glob_ino_project_folder   = ""
glob_working_dir          = os.getcwd()
glob_pio_folder           = ""
glob_pio_project_folder   = ""
glob_pio_src              = ""
glob_pio_include          = ""
dict_global_variables     = {}
dict_undefined_vars_used  = {}
dict_prototypes           = {}
dict_class_instances      = {}
dict_includes             = {}
platformio_marker         = "/PlatformIO"
localheaders_marker       = "//== Local Headers =="
externvariables_marker    = "//== Extern Variables =="
externclasses_marker      = "//== Extern Classes =="
prototypes_marker         = "//== Function Prototypes =="
convertor_marker          = "//== Added by Convertor =="

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
      print(f"Keys: {keys}")
      # Iterate over keys and values
      print("Iterating over keys and values:")
      for key, value in dict_global_variables.items():
          print(f"  key[{key}]: value[{value}]")

#------------------------------------------------------------------------------------------------------
def set_glob_project_info(project_dir):
    """
    Get project folder, name, and PlatformIO-related paths.

    Returns:
        tuple: Contains project_folder, glob_project_name, glob_pio_folder, glob_pio_src, glob_pio_include
    """
    global glob_ino_project_folder
    global glob_pio_project_folder
    global glob_working_dir
    global glob_project_name
    global glob_root_folder
    global glob_pio_folder
    global glob_pio_src
    global glob_pio_include

    glob_ino_project_folder = os.path.abspath(glob_working_dir)
    glob_project_name = os.path.basename(glob_ino_project_folder)
    glob_pio_folder = os.path.join(glob_ino_project_folder, "PlatformIO")
    glob_pio_project_folder = os.path.join(glob_pio_folder, glob_project_name)
    glob_pio_src = os.path.join(glob_pio_folder, glob_project_name, "src")
    glob_pio_include = os.path.join(glob_pio_folder, glob_project_name, "include")

    logging.info(f"glob_ino_project_folder: {glob_ino_project_folder}")
    logging.info(f"glob_pio_project_folder: {glob_pio_project_folder}")
    logging.info(f"      glob_project_name: {glob_project_name}")
    logging.info(f"        glob_pio_folder: {glob_pio_folder}")
    logging.info(f"           glob_pio_src: {glob_pio_src}")
    logging.info(f"       glob_pio_include: {glob_pio_include}\n")

    #return glob_ino_project_folder, glob_project_name, glob_pio_folder, glob_pio_src, glob_pio_include

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
            print("--- Global Variables ---")
        for file_path, vars_list in sorted_global_vars.items():
            if vars_list:  # Only print for files that have global variables
                #print(f"\nFile: {file_path}")
                for var_type, var_name, function, is_pointer in vars_list:
                    pointer_str = "*" if is_pointer else " "
                    function_str = function if function else "global scope"
                    var_type_pointer = f"{var_type}{pointer_str}"
                    #print(f"       {var_type:<15} {pointer_str:<1} {var_name:<35} {function_str:<20} (in {file_path})")
                    print(f"       {var_type_pointer:<15} {var_name:<35} {function_str:<20} (in {file_path})")
        
        print("")

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
            print("\n--- Undefined Global Variables ---")
        for key, info in sorted(global_vars_undefined.items(), key=lambda x: (x[1]['var_name'], x[1]['used_in'], x[1]['line'])):
            pointer_str = "*" if info['var_is_pointer'] else ""
            var_type_pointer = f"{info['var_type']}{pointer_str}"
            print(f"  - {var_type_pointer:<15.15} {info['var_name']:<30} (line {info['line']:<4}  in {info['used_in'][:20]:<20}) [{var_type_pointer:<25.25}] (defined in {info['defined_in']})")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def print_functions(functions_dict):
    """
    Print the function prototypes and their source files.
    
    Args:
    functions_dict (dict): Dictionary of function prototypes, with function names as keys and tuples (prototype, file_path) as values.
    """
    try:
      if not functions_dict:
          logging.info("\tNo functions found.")
          return

      print("\n--- Function Prototypes ---")
      for func_name, (prototype, file_path) in functions_dict.items():
          print("       {:<25} {:<35}".format(os.path.basename(file_path), prototype))

      print("")

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

        print("\n--- Class Instances ---")
        for file_path, class_list in class_instances.items():
            if class_list:  # Only print for files that have classes
                for class_type, instance_name, constructor_args, fbase in class_list:
                    parentacedConstructor = "("+constructor_args+")"
                    print(f"       {class_type:<15} {instance_name:<20} {parentacedConstructor:<35} (in {fbase})")
        
        print("")
                                    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"A\tn error occurred at line {line_number}: {str(e)}")
        exit()


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
        
        #print(f"Successfully removed all contents in {full_path} including the folder itself, "
        #      f"and all other contents in {base_path} except {preserve_file}")
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
    # Ensure the main PlatformIO folder exists
    if not os.path.exists(glob_pio_folder):
        os.makedirs(glob_pio_folder)
        logging.info(f"Created PlatformIO folder: {short_path(glob_pio_folder)}")
    logging.info(f"Recreating PlatformIO folder structure: {glob_pio_folder}")

    #last_folder = "ESP_ticker"
    #file_to_preserve = "platformio.ini"

    # Get the current working directory
    current_dir = os.getcwd()
    logging.info(f"\tCurrent working directory: {current_dir}")

    # Construct the full base path
    full_base_path = os.path.join(current_dir, glob_pio_folder, glob_project_name)
    logging.info(f"\t  Full base path: {full_base_path}")
    logging.info(f"\t    glob_pio_src: {glob_pio_src}")
    logging.info(f"\tglob_pio_include: {glob_pio_include}")

    # Recreate src and include folders
    for folder in [glob_pio_src, glob_pio_include]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        logging.info(f"\tmakedirs [{folder}]")
        os.makedirs(folder)
        logging.info(f"\tRecreated folder: [{folder}]")

    logging.info("\tPlatformIO folder structure recreated")

#------------------------------------------------------------------------------------------------------
def insert_include_in_header(header_path, text):
    include_statement = f'#include "{text}"\n'

    marker_index = header_path.find(platformio_marker)
    if marker_index != -1:
        part_of_path = header_path[marker_index + len({platformio_marker}):]
        logging.info(f"Updating {part_of_path} with new includes: {text}")
    else:
        logging.info(f"Updating {header_path} with new includes: {text}")

    # Read the header file
    with open(header_path, 'r') as file:
        lines = file.readlines()
    
    # Check if the include statement already exists
    for line in lines:
        if include_statement.strip() in line.strip():
            return  # The include statement already exists
    
    # Look for "==local includes=="
    for i, line in enumerate(lines):
        if "==local includes==" in line:
            lines.insert(i + 1, include_statement)
            break
    else:
        # Look for any "#include " statement
        for i, line in enumerate(lines):
            if line.startswith('#include "'):
                lines.insert(i + 1, include_statement)
                break
        else:
            # Insert at the top of the file
            lines.insert(0, include_statement)
    
    # Write the modified lines back to the file
    with open(header_path, 'w') as file:
        file.writelines(lines)

    logging.info(f"\tUpdated {short_path(header_path)} with new includes: [{text}]")




#------------------------------------------------------------------------------------------------------
def copy_data_folder():
    """
    Delete existing data folder in glob_pio_folder if it exists,
    then copy the data folder from the project folder to the PlatformIO folder if it exists.
    """
    logging.info("");
    source_data_folder = os.path.join(glob_ino_project_folder, 'data')
    destination_data_folder = os.path.join(glob_pio_folder, glob_project_name, 'data')

    # Delete existing data folder in glob_pio_folder if it exists
    if os.path.exists(destination_data_folder):
        try:
            shutil.rmtree(destination_data_folder)
            logging.info(f"\tDeleted existing data folder in {short_path(glob_pio_folder)}")

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
            logging.info("\tCopy data folder ")
            logging.info(f"\t>> from: {short_path(source_data_folder)}")
            logging.info(f"\t>>   to: {short_path(destination_data_folder)}")
            shutil.copytree(source_data_folder, destination_data_folder)
            logging.info(f"\tCopied data folder from {short_path(source_data_folder)} to {short_path(destination_data_folder)}")

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
    logging.info(f"Processing create _platformio_ini() if it doesn't exist in [{short_path(glob_pio_project_folder)}]")
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
#board_build.partitions = min_spiffs.csv
#board_build.filesystem = SPIFFS

;-- esp8266
#platform = espressif8266
#board = esp12e
#board_build.filesystem = LittleFS

;-- attiny85
#platform = atmelavr
#board = attiny85
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

framework = arduino
board_build.filesystem = LittleFS
monitor_speed = 115200
upload_speed = 115200
upload_port = <select port like "/dev/cu.usbserial-3224144">
build_flags =
\t-D DEBUG

lib_ldf_mode = deep+

lib_deps =
;\t<select libraries with "PIO Home" -> Libraries

monitor_filters =
;-- esp8266
#  esp8266_exception_decoder
"""
        with open(platformio_ini_path, 'w') as f:
            f.write(platformio_ini_content)
            logging.info(f"\tCreated platformio.ini file at {short_path(platformio_ini_path)}")

    else:  
        logging.info(f"\tplatformio.ini file already exists at [{short_path(platformio_ini_path)}]")


#------------------------------------------------------------------------------------------------------
def extract_and_comment_defines():
    """
    Extract all #define statements (including functional and multi-line) from .h, .ino, and .cpp files,
    create allDefines.h, and comment original statements with info.
    """
    logging.info("")
    all_defines = []
    define_pattern = r'^\s*#define\s+(\w+)(?:\(.*?\))?\s*(.*?)(?:(?=\\\n)|$)'

    logging.info(f"Searching for #define statements in {short_path(glob_pio_folder)}")

    # Only search within glob_pio_src and glob_pio_include folders
    #search_folders = [os.path.join(glob_pio_folder, 'glob_pio_src'), glob_pio_include]
    search_folders = [glob_pio_src, glob_pio_include]

    for folder in search_folders:
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(('.h', '.ino')):
                    file_path = os.path.join(root, file)
                    logging.info(f"\tProcessing file: {short_path(file_path)}")
                    try:
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
                                    new_content.extend([f"\t//-- moved to allDefines.h // {line}" for line in full_define])
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

                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        #fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        line_number = exc_tb.tb_lineno
                        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
                        logging.error(f"\tError processing file {file}: {str(e)}")
                        exit()

    # Create allDefines.h with all macros
    all_defines_path = os.path.join(glob_pio_include, 'allDefines.h')
    logging.info(f"\tCreating allDefines.h with {len(all_defines)} macros")
    try:
        with open(all_defines_path, 'w') as f:
            f.write("#ifndef ALLDEFINES_H\n#define ALLDEFINES_H\n\n")
            for macro_name, macro_value in all_defines:
                f.write(f"{macro_value}\n\n")
            f.write("#endif // ALLDEFINES_H\n")

        logging.info(f"\tSuccessfully created {short_path(all_defines_path)}")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        #fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError creating allDefines.h: {str(e)}")
        exit()

    logging.info(f"\tExtracted {len(all_defines)} #define statements")

#------------------------------------------------------------------------------------------------------
def create_new_header_file(ino_name, header_name):
    """Create new header file with basic structure."""
    logging.info("")
    logging.info(f"Processing create_new_header_file(): {header_name} for [{ino_name}]")

    header_path = os.path.join(glob_pio_include, f"{header_name}")

    if os.path.exists(header_path):
        logging.info(f"\tHeader file already exists: {header_name}")
        return

    base_name = os.path.splitext(header_name)[0]
    header_path = os.path.join(glob_pio_include, f"{header_name}")
    with open(header_path, 'w') as f:
        f.write(f"#ifndef {base_name.upper()}_H\n")
        f.write(f"#define {base_name.upper()}_H\n\n")
        f.write("#include <Arduino.h>\n\n")
        f.write(f"{localheaders_marker}")
        f.write("\n")
        f.write("#include \"allDefines.h\"\n\n")
        f.write(f"{externvariables_marker}")
        f.write("\n\n")
        f.write(f"{prototypes_marker}")
        f.write("\n\n")
        f.write(f"#endif // {base_name.upper()}_H\n")

    logging.info(f"\tCreated new header file: {header_name}")


#------------------------------------------------------------------------------------------------------
def process_original_header_file(header_path, base_name):
    logging.info(f"Processing process_original_header_file(): [{base_name}]")
    
    if os.path.exists(header_path):
        with open(header_path, 'r') as f:
            original_content = f.read()
        
        # Check for existing header guards
        has_guards = re.search(r'#ifndef\s+\w+_H.*?#define\s+\w+_H', original_content, re.DOTALL) is not None

        prefix = ""
        suffix = ""

        if not has_guards:
            # Prepare header guards if they don't exist
            logging.info(f"\tPreparing header guards for {base_name}")
            guard_name = f"{base_name.upper()}_H"
            prefix = f"#ifndef {guard_name}\n#define {guard_name}\n\n"
            suffix = f"\n#endif // {guard_name}\n"
        
        # Check if allDefines.h is already included
        if '#include "allDefines.h"' not in original_content:
            # Prepare the include statement
            logging.info(f"\tPreparing to add allDefines.h include to {base_name}")
            prefix += '#include "allDefines.h"\n\n'

        # Combine original content with additions
        if prefix or suffix:
            new_content = prefix + original_content + suffix
            
            # Only write to the file if changes were made
            with open(header_path, 'w') as f:
                f.write(new_content)
            logging.info(f"\tUpdated original header file: {short_path(header_path)}")
        else:
            logging.info(f"\tNo changes needed for: {short_path(header_path)}")
    else:
        logging.info(f"\tFile not found: {short_path(header_path)}")

    return header_path

#------------------------------------------------------------------------------------------------------
def insert_external_variables(base_name):
    logging.info("")
    logging.info(f"Processing insert_external_variables() in file: [{os.path.splitext(base_name)[0]}]")
    
    # Get the full path of the file under test
    base_used_in  = os.path.splitext(base_name)[0]
    header_name   = base_used_in + ".h"
    header_path   = os.path.join(glob_pio_include, header_name)
    
    try:
        # Select undefined variables used in the file under test
        selected_vars = []
        for var_name, info in dict_undefined_vars_used.items():
            #logging.info(f"\tChecking: [{info['var_type']:<10}\t {var_name:<30}]\t (Used in {info['used_in']}), \tDefined in [{info['defined_in']}]")
            if info['used_in'] == base_used_in and info['defined_in'] != base_used_in:
                logging.info(f"\tfound: {info['var_type']:<10} \t{info['var_name']:<30} (defined in {info['defined_in']})")
                var_name_base = info['var_name']
                var_type = info['var_type']
                defined_in = info['defined_in']
                selected_vars.append((var_type, var_name_base, defined_in))
        
        if not selected_vars:
            logging.info(f"\tNo undefined variables found for {base_name}")
            return
        
        # Read the content of the file under test
        with open(header_path, 'r') as file:
            file_content = file.read()
        
        # Find the position of the externvariables_marker
        marker = externvariables_marker
        marker_pos = file_content.find(marker)
        if marker_pos == -1:
            logging.info(f"\tExternvariables marker not found in {base_name}")
            marker = convertor_marker
            marker_pos = file_content.find(marker)
            if marker_pos == -1:
                logging.info(f"\tConvertor marker not found in {base_name}")
                return
        
        # Insert the external variable declarations after the marker
        insert_pos = marker_pos + len(marker) + 1  # +1 for the newline
        extern_vars_text = "\n".join(f"extern {var_type:<10} {var_name_base+';':<30} \t//-- from {defined_in}" for var_type, var_name_base, defined_in in selected_vars) + "\n"
        
        new_content = (
            file_content[:insert_pos] +
            extern_vars_text +
            file_content[insert_pos:]
        )
        
        # Write the modified content back to the file under test
        with open(header_path, 'w') as file:
            file.write(new_content)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError processing file {header_path}: {str(e)}")
        exit()
    
    logging.info(f"\tInserted {len(selected_vars)} external variable declarations into {base_name}")

#------------------------------------------------------------------------------------------------------
def insert_prototypes(base_name):
    logging.info("")
    logging.info(f"Processing insert_prototypes() in file: [{base_name}]")
    
    # Get the full path of the file under test
    header_name = os.path.splitext(base_name)[0] + ".h"
    file_path = os.path.join(glob_pio_include, header_name)
    
    try:
        # Select prototypes from the file under test and ensure they end with a semicolon
        selected_prototypes = [
            (prototype + ';' if not prototype.strip().endswith(';') else prototype)
            for func_name, (prototype, src_file_path) in dict_prototypes.items()
            if os.path.basename(os.path.splitext(src_file_path)[0]) == os.path.basename(base_name)
        ]
        
        # Read the content of the file under test
        with open(file_path, 'r') as file:
            file_content = file.read()
        
        # Find the position of the prototype_marker
        marker = prototypes_marker
        marker_pos = file_content.find(marker)
        if marker_pos == -1:
            logging.info(f"\tPrototype marker not found in {base_name}")
            marker = convertor_marker
            marker_pos = file_content.find(marker)
            if marker_pos == -1:
                logging.info(f"\tConvertor marker not found in {base_name}")
                return
        
        # Insert the prototypes after the marker
        insert_pos = marker_pos + len(marker) + 1  # +1 for the newline
        prototypes_text = "\n".join(selected_prototypes) + "\n"
        
        new_content = (
            file_content[:insert_pos] +
            prototypes_text +
            file_content[insert_pos:]
        )
        
        # Write the modified content back to the file under test
        with open(file_path, 'w') as file:
            file.write(new_content)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError processing file {file_path}: {str(e)}")
        exit()

    logging.info(f"\tInserted {len(selected_prototypes)} prototypes into {base_name}")

#------------------------------------------------------------------------------------------------------
def insert_local_includes(base_name):
    global args

    logging.info("")
    logging.info(f"Processing insert_local_includes() for file: [{base_name}]")
    
    # Get the full path of the file under test and its header
    src_file_path = os.path.join(glob_pio_src, base_name)
    header_name = os.path.splitext(base_name)[0] + ".h"
    header_file_path = os.path.join(glob_pio_include, f"{header_name}")
    
    try:
        # Read the content of the source file
        with open(src_file_path, 'r') as file:
            src_content = file.read()
        
        # Extract function names from the source file (both definitions and calls)
        # This pattern looks for function definitions
        definition_pattern = r'^\s*(void|int|bool|char|String|float|double|long|unsigned|static|size_t|if)\s+(\w+)\s*\([^\)]*\)\s*(?:\{|$)'
        # This pattern looks for function calls
        call_pattern = r'\b(\w+)\s*\([^\)]*\)'
        
        # Find all function definitions and calls
        definitions = set(re.findall(definition_pattern, src_content, re.MULTILINE))
        calls = set(re.findall(call_pattern, src_content))
        
        # Combine definitions and calls, removing duplicates
        local_functions = set(func for _, func in definitions).union(calls)
        
        if args.debug:
            # Print local functions (both defined and called)
            print(f"Local functions (defined and called): {', '.join(sorted(local_functions))}")
        
        # Read the content of the header file
        with open(header_file_path, 'r') as file:
            header_content = file.read()
        
        # Find existing includes
        existing_includes = set(re.findall(r'#include\s*"([^"]+)"', header_content))
        
        # Collect includes for functions found in dict_prototypes
        includes = {}
        for func_name in local_functions:
            if func_name in dict_prototypes:
                defined_in, file_path = dict_prototypes[func_name]
                if file_path != base_name:  # Skip if defined in the same file
                    include_file = os.path.splitext(file_path)[0] + ".h"
                    if include_file not in existing_includes:  # Check if include already exists
                        include_line = f'#include "{include_file}"'
                        if include_line not in includes:
                            includes[include_line] = []
                        includes[include_line].append(func_name)
        
        if not includes:
            logging.info(f"\tNo new function includes needed for {base_name}")
            return
        
        # Find the position of the local_headers_marker
        marker = '#include "allDefines.h"'
        marker_pos = header_content.find(marker)
        if marker_pos == -1:
            marker = localheaders_marker
            marker_pos = header_content.find(marker)
            if marker_pos == -1:
                logging.info(f"\tLocal headers marker not found in {os.path.basename(header_file_path)}")
                marker = convertor_marker
                marker_pos = header_content.find(marker)
                if marker_pos == -1:
                    logging.info(f"\tConvertor marker not found in {os.path.basename(header_file_path)}")
                    return
        
        # Insert the includes after the marker
        insert_pos = marker_pos + len(marker) + 1  # +1 for the newline
        includes_text = ""
        for include, functions in sorted(includes.items()):
            logging.info(f"\t{include:<30} ({', '.join(functions)})")
            functions_str = ", ".join(sorted(functions))
            includes_text += f"//-- {functions_str}\n{include}\n"
        
        new_content = (
            header_content[:insert_pos] +
            includes_text +
            header_content[insert_pos:]
        )
        
        # Write the modified content back to the header file
        with open(header_file_path, 'w') as file:
            file.write(new_content)
    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError processing file [{base_name}]: {str(e)}")
        exit()

    logging.info(f"\tInserted {len(includes)} new function includes into {os.path.basename(header_file_path)}")

#------------------------------------------------------------------------------------------------------
def add_all_includes():
    logging.info("");
    logging.info(f"Processing add_all_includes(): {glob_project_name}")

    try:
        project_header = os.path.join(glob_pio_include, f"{glob_project_name}.h")
        # Read the content of the source file
        with open(project_header, 'r') as file:
            content = file.read()

        # Create a set of existing includes
        existing_includes = set(re.findall(r'#include\s*[<"]([^>"]+)[>"]', content))

        # Prepare new includes
        new_includes = []
        for file_name in os.listdir(glob_pio_include):
            logging.debug(f"\tProcessing file: {file_name}")
            header_name = os.path.basename(file_name)  # Get the basename
            if header_name not in existing_includes:
                new_includes.append(f'#include "{header_name}"')

        if not new_includes:
            return   # No new includes to add
        
        logging.debug(f"\tFound {len(new_includes)} new includes: {', '.join(new_includes)}")

        # Find the insertion point
        marker = localheaders_marker
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
                    logging.info("\tCannot find suitiblae insertion point")
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
        #logging.error(f"\tError processing file {file_path}: {str(e)}")
        exit()

#------------------------------------------------------------------------------------------------------
def copy_project_files():
    """Copy .ino files to glob_pio_src and .h files to glob_pio_include."""
    logging.info("")
    logging.info("Processing copy_project_files() ..")

    # Check if the file exists
    allDefines_path = os.path.join(glob_pio_include, "allDefines.h")
    if os.path.exists(allDefines_path):
        # Delete the file
        os.remove(allDefines_path)
        logging.info("\t'allDefines.h' has been deleted.")
    else:
       logging.info("\t'allDefines.h' does not (yet) exist.")

    for file in os.listdir(glob_ino_project_folder):
        if file.endswith('.ino'):
            logging.info(f"Copy [{file}] ..")
            shutil.copy2(os.path.join(glob_ino_project_folder, file), glob_pio_src)
        elif file.endswith('.h'):
            shutil.copy2(os.path.join(glob_ino_project_folder, file), glob_pio_include)
            #if file.endswith('.h') and file != f"{glob_project_name}.h":
            logging.info(f"Copy [{file}] ..")
            logging.info(f"\tProcessing original header file: {file}")
            base_name = os.path.splitext(file)[0]
            header_path = os.path.join(glob_pio_include, f"{base_name}.h")
            process_original_header_file(header_path, base_name)

    list_files_in_directory(glob_pio_src)
    list_files_in_directory(glob_pio_include)
    logging.info("\tCopied project files to PlatformIO folders")


#------------------------------------------------------------------------------------------------------
def extract_global_variables(file_path):
    """
    Extract global variable definitions from a single .ino, .cpp, or header file.
    Only variables declared outside of all function blocks are considered global.
    """
    logging.info("")
    logging.info(f"Processing extract_global_variables() from : {os.path.basename(file_path)}")

    global_vars = {}

    # Get the fbase (filename without extension)
    file = os.path.basename(file_path)
    fbase = os.path.splitext(file)[0]

    # Check if there are existing entries in dict_global_variables for this fbase
    if fbase in dict_global_variables:
        global_vars[fbase] = dict_global_variables[fbase]
        logging.info(f"\tFound existing global variables for {fbase} in dict_global_variables")

    # Comprehensive list of object types, including String
    types = r'(?:uint8_t|int8_t|uint16_t|int16_t|uint32_t|int32_t|uint64_t|int64_t|char|int|float|double|bool|boolean|long|short|unsigned|signed|size_t|void|String|time_t|struct tm)'

    var_pattern = rf'^\s*((?:static|volatile|const)?\s*{types}(?:\s*\*)*)\s+((?:\w+(?:\[.*?\])?(?:\s*=\s*[^,;]+)?\s*,\s*)*\w+(?:\[.*?\])?(?:\s*=\s*[^,;]+)?)\s*;'
    func_pattern = rf'^\s*(?:static|volatile|const)?\s*(?:{types})(?:\s*\*)*\s+(\w+)\s*\((.*?)\)'

    keywords = set(['if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
                    'break', 'continue', 'return', 'goto', 'typedef', 'struct', 'enum',
                    'union', 'sizeof', 'volatile', 'register', 'extern', 'inline'])

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        brace_level = 0
        in_function = False
        current_function = None
        file_vars = []

        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()

            # Check for function start
            func_match = re.search(func_pattern, stripped_line)
            if func_match and not in_function:
                in_function = True
                current_function = func_match.group(1)

            # Count braces
            brace_level += stripped_line.count('{') - stripped_line.count('}')

            # Check for function end
            if brace_level == 0:
                in_function = False
                current_function = None

            # Check for variable declarations only at global scope
            if not in_function and brace_level == 0:
                var_match = re.search(var_pattern, stripped_line)
                if var_match:
                    var_type = var_match.group(1).strip()
                    var_declarations = re.findall(r'([a-zA-Z]\w*(?:\[.*?\])?)(?:\s*=\s*[^,;]+)?', var_match.group(2))
                    for var_name in var_declarations:
                        base_name = var_name.split('[')[0].strip()
                        if base_name not in keywords:
                            # Check for pointer in var_type or var_name
                            is_pointer = var_type.endswith('*') or var_name.startswith('*')
                            
                            # Remove asterisk from var_type if it ends with one
                            if var_type.endswith('*'):
                                var_type = var_type.rstrip('*').strip()
                            
                            # Remove asterisk from var_name if it starts with one
                            if var_name.startswith('*'):
                                var_name = var_name.lstrip('*').strip()
                            
                            file_vars.append((var_type, var_name, current_function, is_pointer))
                            logging.info(f"\tGlobal variable found: [{var_type} {var_name}]")
                            if is_pointer:
                                logging.info(f"\t\tPointer variable detected: [{var_type} {var_name}]")

        # Remove duplicate entries
        unique_file_vars = list(set(file_vars))

        # Add new global variables to the existing ones
        if fbase in global_vars:
            global_vars[fbase].extend(unique_file_vars)
        else:
            global_vars[fbase] = unique_file_vars

        if unique_file_vars:
            logging.info(f"\tProcessed {os.path.basename(file_path)} successfully. Found {len(unique_file_vars)} new global variables.")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        logging.error(f"\tError processing file {file_path}: {str(e)}")
        exit()

    if global_vars[fbase]:
        logging.info(f"\tTotal global variables for {fbase}: {len(global_vars[fbase])}")
    else:
        logging.info("\t>> No global variables found")

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
    logging.info(f"Processing extract_undefined_vars_in_file() for file: [{os.path.basename(file_path)}]")

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
                    if args.debug:
                        logging.info(f"Added usage of {global_var_name} to undefined_vars: {undefined_vars[key]}")
                    #else:
                    #    logging.info(f"Added usage of {global_var_name} to undefined_vars")
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
    dict: Dictionary of function prototypes found in the file, with function names as keys and tuples (prototype, file_path) as values.
    """
    logging.info("")
    logging.info(f"Processing extract_prototypes() from file: [{os.path.basename(file_path)}]")
    
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
            
            prototypes[func_name] = (prototype, os.path.basename(file_path))
            logging.debug(f"\tExtracted prototype from [{os.path.basename(file_path)}]: {prototype}")
        
        if not prototypes:
            logging.info(f"\tNo function prototypes found in {os.path.basename(file_path)}")
    
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
    Only global class instance declarations are considered.
    """
    logging.info("")
    logging.info(f"Processing extract_class_instances() from: {short_path(file_path)}")

    file  = os.path.basename(file_path)
    fbase = os.path.splitext(file)[0]

    class_instances = {}
    
    # Read already found instances from the global dict_class_instances
    if file_path in dict_class_instances:
        class_instances[file_path] = dict_class_instances[file_path]
    
    # Pattern for class instance declarations
    class_pattern = r'^\s*([A-Z]\w+(?:<.*?>)?)\s+(\w+)(?:\s*\((.*?)\))?\s*;'

    # Extended list of known classes
    known_classes = [
        'WiFiServer', 'ESP8266WebServer', 'WiFiClient', 'WebServer',
        'File', 'FSInfo', 'WiFiManager', 'Timezone', 'DNSServer',
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
    # Common class suffixes
    common_suffixes = ['Client', 'Server', 'Class', 'Manager', 'Handler', 'Controller', 
                       'Service', 'Factory', 'Builder', 'Driver', 'Adapter', 'Wrapper'
    ]

    
    # List of standard C types to exclude
    standard_types = ['int', 'bool', 'char', 'float', 'double', 'void', 'unsigned', 'signed',
                      'short', 'long', 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
                      'int8_t', 'int16_t', 'int32_t', 'int64_t', 'size_t', 'wchar_t',
                      'byte', 'word', 'String', 'string', 'auto', 'const', 'volatile'
    ]
   
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        file_instances = []
        brace_level = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # Skip lines inside function bodies or class definitions
            brace_level += stripped_line.count('{') - stripped_line.count('}')
            if brace_level > 0:
                continue
            
            class_match = re.search(class_pattern, stripped_line)
            if class_match:
                class_type = class_match.group(1).strip()
                instance_name = class_match.group(2).strip()
                constructor_args = class_match.group(3).strip() if class_match.group(3) else ""
                
                # Check if it's a valid class type (starts with uppercase and is either in known_classes or matches the pattern)
                if class_type[0].isupper() and (class_type in known_classes or re.match(r'^[A-Z]\w+$', class_type)):
                    file_instances.append((class_type, instance_name, constructor_args, fbase))
                    logging.info(f"{fbase}: {class_type} {instance_name}")
                else:
                    logging.debug(f"\tNot a class instance (not added) in {fbase}:{line_num}: {class_type} {instance_name}")
        
        if file_instances:
            class_instances[file_path] = file_instances
            logging.info(f"\t>> Found {len(file_instances)} class instances.")
        else:
            logging.info(f"\t>> No class instances found.")
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"\tAn error occurred at line {line_number}: {str(e)}")
        exit()
    
    if (len(file_instances) > 0):
        logging.info(f"\tExtracted class instances from {os.path.basename(file_path)} -> found: {len(file_instances)}")

    return class_instances

#------------------------------------------------------------------------------------------------------
def remove_comments(code):
    # Remove single-line comments
    code = re.sub(r'//.*', '', code)
    # Remove multi-line comments
    code = re.sub(r'/\*[\s\S]*?\*/', '', code)
    return code

#------------------------------------------------------------------------------------------------------
def insert_class_instances_to_header_files(base_name):
    logging.info("")
    logging.info(f"Processing insert_class_instances_to_header_files(): {base_name}")

    # Get the full path of the file under test and its header
    src_path = os.path.join(glob_pio_src, base_name) + '.ino'
    header_name = os.path.splitext(base_name)[0] + ".h"
    include_path = os.path.join(glob_pio_include, f"{header_name}")

    try:
        with open(src_path, 'r') as file:
            content = file.read()
        
        content_without_comments = remove_comments(content)

        # Split the content into words
        words = re.findall(r'\b\w+\b', content_without_comments)

        # Check all words against dict_class_instances
        new_declarations = []
        new_includes = []
        for word in words:
            for file_path, class_list in dict_class_instances.items():
                for cls_type, cls_instance, constructor_args, fbase in class_list:
                    if word == cls_instance:
                        # Skip if the class is defined in the same file as the one being tested
                        if fbase == base_name:
                            logging.info(f"Skipping [{cls_instance}] as it's defined in the same file: [{fbase}:{base_name}]")
                            continue
                        
                        logging.info(f"Hit found: [{cls_instance}] from {fbase} used in {base_name}")
                        if constructor_args:
                            declaration = f"extern {cls_type} {cls_instance}({constructor_args}); \t//-- {fbase}"
                        else:
                            declaration = f"extern {cls_type} {cls_instance}; \t//-- {fbase}"
                        new_declarations.append(declaration)
                        new_includes.append(f"#include <{cls_type}.h>  \t//-- added by convertor")
                        break
                if new_declarations and new_declarations[-1].startswith(f"{cls_type} {cls_instance}"):
                    break

        # Remove duplicates while preserving order
        new_declarations = list(dict.fromkeys(new_declarations))
        new_includes = list(dict.fromkeys(new_includes))

        with open(include_path, 'r') as file:
            content = file.read()

        # Find the appropriate insertion point for declarations
        insert_index = -1
        if externclasses_marker in content:
            insert_index = content.find(externclasses_marker) + len(externclasses_marker)
        elif externvariables_marker in content:
            insert_index = content.find(externvariables_marker) + len(externvariables_marker)
        elif convertor_marker in content:
            insert_index = content.find(convertor_marker) + len(convertor_marker)
        else:
            # Look for header guards
            header_guard_end = content.find("#endif")
            if header_guard_end != -1:
                # Insert after the header guard start and an empty line
                insert_index = content.find("\n", content.find("#define")) + 1
            else:
                # If no header guard, insert at the top
                insert_index = 0

        # Insert the new declarations
        if new_declarations:
            insert_text = "\n" + "\n".join(new_declarations) + "\n"
            if insert_index == 0:
                new_content = insert_text + content
            else:
                new_content = content[:insert_index] + insert_text + content[insert_index:]
        else:
            new_content = content

        # Find the appropriate insertion point for includes
        include_index = -1
        if "#include <Arduino.h>" in new_content:
            include_index = new_content.find("#include <Arduino.h>") + len("#include <Arduino.h>")
        else:
            last_system_include = new_content.rfind('#include <')
            last_user_include = new_content.rfind('#include "')
            if last_system_include > last_user_include:
                include_index = new_content.find('\n', last_system_include) + 1
            elif last_user_include > -1:
                include_index = new_content.find('\n', last_user_include) + 1
            else:
                # If no includes found, insert after header guard with one empty line
                header_guard_end = new_content.find("#define")
                if header_guard_end != -1:
                    include_index = new_content.find('\n', header_guard_end) + 1
                else:
                    include_index = 0

        # Insert the new includes
        if new_includes:
            include_text = "\n".join(new_includes) + "\n"
            new_content = new_content[:include_index] + "\n" + include_text + new_content[include_index:]

        # Write the updated content back to the file
        with open(include_path, 'w') as file:
            file.write(new_content)
            
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        logging.error(f"An error occurred at line {line_number}: {str(e)}")
        logging.error(f"An error occurred during conversion: {str(e)}")

#------------------------------------------------------------------------------------------------------
def update_header_with_prototypes(header_path, prototypes):
    """Update header file with function prototypes."""
    logging.info()
    logging.info(f"Processing update_header_with_prototypes() file: {os.path.basename(header_path)}")

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
    logging.info("Processing find_undefined_functions_and_update_headers")

    for file in os.listdir(glob_pio_src):
        if file.endswith('.cpp'):
            file_path = os.path.join(glob_pio_src, file)
            base_name = os.path.splitext(file)[0]
            header_path = os.path.join(glob_pio_include, f"{base_name}.h")

            marker = "testProject"
            marker_index = header_path.find(marker)
            if marker_index != -1:
                short_header_path = header_path[marker_index + len(marker):]
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
                        include_statement = f'#include "{include_file}"'
                        if include_statement not in header_content:
                            new_includes.append(include_statement)

                if new_includes:
                    # Find the position to insert new includes
                    #insert_pos = header_content.find("//== Local Headers ==")
                    insert_pos = header_content.find(f"{localheaders_marker}")
                    if insert_pos != -1:
                        #insert_pos += len("//== Local Headers ==\n")
                        insert_pos += len(f"{localheaders_marker}\n")
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
                        logging.warning(f"\tCould not find '{localheaders_marker}' in {short_header_path}")
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
def process_ino_files(glob_pio_src, glob_pio_include, glob_project_name, global_vars, class_instances):
    global global_extern_declarations
    global_extern_declarations = set()  # Reset global extern declarations

    logging.info("")
    logging.debug(f"Processing process_ino_files(): {global_vars}")

    main_ino = f"{glob_project_name}.ino"
    #aaw#main_ino_path = os.path.join(glob_pio_src, main_ino)

    files_to_process = [f for f in os.listdir(glob_pio_src) if f.endswith('.ino')]
    #if main_ino not in files_to_process and os.path.exists(main_ino_path):
    #    files_to_process.append(main_ino)

    used_vars_by_file = {}

    for file in files_to_process:
        logging.info("..")
        base_name = os.path.splitext(file)[0]
        header_path = os.path.join(glob_pio_include, f"{base_name}.h")
        source_path = os.path.join(glob_pio_src, file)

        logging.info(f"\tProcessing file: {short_path(source_path)}, header_path {short_path(header_path)}")

        # Create the header file if it doesn't exist
        create_header_file(header_path, base_name)

        with open(source_path, 'r') as f:
            content = f.read()

        #content_no_comments = remove_comments_preserve_strings(content)

        #used_vars = set(re.findall(r'\b(\w+)\b', content_no_comments))
        used_vars = set(re.findall(r'\b(\w+)\b', content))
        used_vars_by_file[file] = used_vars
        logging.debug(f"\tUsed vars in {file}: {used_vars}")

        #prototypes = extract_prototypes(content_no_comments, file)
        prototypes = extract_prototypes(content, file)
        logging.info(f"\tFound {len(prototypes)} prototypes in {file}")

        update_header_with_prototypes(header_path, prototypes)

        # Add include statement for the corresponding header
        include_statement = f'#include "{base_name}.h"'
        if include_statement not in content:
            content = f'{include_statement}\n\n{content}'

        # Write the updated content back to the file
        new_file_path = os.path.join(glob_pio_src, f"{base_name}.cpp")
        with open(new_file_path, 'w') as f:
            f.write(content)

        # Remove the original .ino file
        os.remove(source_path)

    # Now that we have processed all files and collected used_vars_by_file, we can update headers with externs
    update_header_with_externs(global_vars, class_instances, used_vars_by_file)

    logging.info("\tProcessed .ino files: renamed, updated headers, and converted to .cpp")


#------------------------------------------------------------------------------------------------------
def add_guards_and_marker_to_header(file_path):
    logging.info("")
    logging.info(f"Processing add_guards_and_marker_to_header() file: [{os.path.basename(file_path)}]")
    
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
    logging.info(f"Processing insert_header_include_in_cpp(): [{os.path.basename(file_path)}]")
    
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
    logging.info("Processing preserve_original_headers() ..")

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
    logging.info("Processing update_project_header() ..")

    project_header_path = os.path.join(glob_pio_include, f"{glob_project_name}.h")

    # Split the original content into sections
    sections = re.split(r'(//==.*?==)', original_content, flags=re.DOTALL)

    new_content = []
    local_includes = []

    # Process each section
    for i, section in enumerate(sections):
        if section.strip() == f"{localheaders_marker}":
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
            if "#include \"allDefines.h\"" not in section:
                new_content.append("#include \"allDefines.h\"\n")
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

    if args.backup:
        backup_project(args.project_dir)

    try:
        #glob_ino_project_folder, glob_project_name, glob_pio_folder, glob_pio_src, glob_pio_include = 
        set_glob_project_info(args.project_dir)
        logging.info(f"           Project folder: {glob_ino_project_folder}")

        marker = "arduinoIDE2platformIO-convertor"
        logging.info(f"        PlatformIO folder: {short_path(glob_pio_folder)}")
        logging.info(f"    PlatformIO src folder: {short_path(glob_pio_src)}")
        logging.info(f"PlatformIO include folder: {short_path(glob_pio_include)}\n")


        remove_pio_tree("platformio.ini")

        recreate_pio_folders()

        if not os.path.exists(glob_pio_folder):
            logging.error(f"PlatformIO folder does not exist: {glob_pio_folder}")
            return

        copy_project_files()
        copy_data_folder()
        create_platformio_ini()
        extract_and_comment_defines()

        search_folders = [glob_pio_src, glob_pio_include]

        list_files_in_directory(glob_pio_src)

        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 1] Process all '.ino' and 'h' files")
        logging.info("=======================================================================================================")

        for folder in search_folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(('.h', '.ino')):
                        file_path = os.path.join(root, file)
                        #base_name = os.path.splitext(file)[0]  # Get the basename without extension
                        base_name = os.path.basename(file)  # Get the basename without extension
                        logging.info("")
                        logging.info("-------------------------------------------------------------------------------------------------------")
                        logging.info(f"Processing file: {short_path(file_path)} basename: [{base_name}]")

                        global_vars = extract_global_variables(file_path)
                        if args.debug:
                            print_global_vars(global_vars)
                        dict_global_variables.update(global_vars)
                        class_instances = extract_class_instances(file_path)
                        if args.debug:
                            print_class_instances(class_instances)
                        dict_class_instances.update(class_instances)
                        prototypes = extract_prototypes(file_path)
                        if args.debug:
                            print_functions(prototypes)
                        dict_prototypes.update(prototypes)
                        if file.endswith('.h') and file != "allDefines.h":
                            add_guards_and_marker_to_header(file_path)

        logging.info("And now the complete list of global variables:")
        print_global_vars(dict_global_variables)
        logging.info("And now the complete list of class instances:")
        print_class_instances(dict_class_instances)
        logging.info("And now the complete list of prototypes:")
        print_functions(dict_prototypes)

        search_folders = [glob_pio_src, glob_pio_include]
        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 2] Search for undefined variables")
        logging.info("=======================================================================================================")

        for folder in search_folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(('.h', '.ino')):
                        file_path = os.path.join(root, file)
                        base_name = os.path.splitext(file)[0]  # Get the basename without extension
                        global_vars_undefined = extract_undefined_vars_in_file(file_path)
                        print_global_vars_undefined(global_vars_undefined)
                        dict_undefined_vars_used.update(global_vars_undefined)

        logging.info("")
        logging.info("And now the complete list of undefined variables:")
        print_global_vars_undefined(dict_undefined_vars_used)

        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 3] Create new header files for all '.ino' files")
        logging.info("=======================================================================================================")

        for filename in os.listdir(glob_pio_src):
            #logging.debug(f"Processing file: {filename}")
            ino_name = os.path.basename(filename)
            base_name = os.path.splitext(ino_name)[0]  # Get the basename without extension
            header_name = ino_name.replace(".ino", ".h")
            if filename.endswith(".ino"):
                create_new_header_file(ino_name, header_name)
                insert_prototypes(base_name)
                insert_external_variables(base_name)
                insert_local_includes(ino_name)

        add_all_includes()
        
        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 4] Check all '.ino' and '.h' files")
        logging.info(f"         Look for class instances used but not defined.")
        logging.info("=======================================================================================================")

        for filename in os.listdir(glob_pio_src):
            logging.debug(f"\tProcessing filename: {filename}")
            ino_name = os.path.basename(filename)
            logging.info(f"\t\tProcessing ino_file: {ino_name}")
            base_name = os.path.splitext(ino_name)[0]  # Get the basename without extension
            logging.info(f"\t\t\tbase_name: {base_name}")
            insert_class_instances_to_header_files(base_name)

        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 5] insert an #include for all '.h' files in {glob_project_name}.h")
        logging.info("=======================================================================================================")

        for filename in os.listdir(glob_pio_src):
            logging.debug(f"\tProcessing filename: {filename}")


        logging.info("")
        logging.info("=======================================================================================================")
        logging.info(f"[Step 5] rename all '.ino' files to '.cpp'")
        logging.info("=======================================================================================================")

        for filename in os.listdir(glob_pio_src):
            logging.debug(f"Found file: {filename}")
            ino_name = os.path.basename(filename)
            base_name = os.path.splitext(ino_name)[0]  # Get the basename without extension
            header_name = ino_name.replace(".ino", ".h")
            if filename.endswith(".ino"):
                ino_path = os.path.join(glob_pio_src, filename)
                cpp_name = ino_name.replace(".ino", ".cpp")
                cpp_path = os.path.join(glob_pio_src, cpp_name)
                rename_file(ino_path, cpp_path)
                insert_header_include_in_cpp(cpp_path)

        logging.info("Arduino to PlatformIO conversion completed successfully")

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        #fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        line_number = exc_tb.tb_lineno
        logging.error(f"An error occurred at line {line_number}: {str(e)}")
        logging.error(f"An error occurred during conversion: {str(e)}")

#======================================================================================================
if __name__ == "__main__":
    main()
