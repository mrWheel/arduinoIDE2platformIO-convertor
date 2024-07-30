#------------------------------------------------------------
#
#   convert a ArduinoIDE project to a PlatformIO project
#
#   file name : arduinoIDE2platformIO.py   
#
#   by        : Willem Aandewiel
#
#   Version   : v0.5 (27-07-2024)
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

global_extern_declarations = set()
platformio_marker       = "/PlatformIO"
localheaders_marker     = "//== Local Headers =="
externvariables_marker  = "//== Extern Variables =="
prototypes_marker       = "//== Function Prototypes =="

#------------------------------------------------------------------------------------------------------
def setup_logging():
    """Set up logging configuration."""
    #logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

#------------------------------------------------------------------------------------------------------
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Convert Arduino project to PlatformIO structure.")
    parser.add_argument("--project_dir", default=os.getcwd(), help="Path to the project directory")
    parser.add_argument("--backup", action="store_true", help="Create a backup of original files")
    return parser.parse_args()

#------------------------------------------------------------------------------------------------------
def backup_project(project_folder):
    """Create a backup of the project folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = f"{project_folder}_backup_{timestamp}"
    shutil.copytree(project_folder, backup_folder)
    logging.info(f"Project backup created at: {backup_folder}")

#------------------------------------------------------------------------------------------------------
def get_project_info(project_dir):
    """
    Get project folder, name, and PlatformIO-related paths.

    Returns:
        tuple: Contains project_folder, project_name, pio_folder, pio_src, pio_include
    """
    project_folder = os.path.abspath(project_dir)
    project_name = os.path.basename(project_folder)
    pio_folder = os.path.join(project_folder, "PlatformIO", project_name)
    pio_src = os.path.join(pio_folder, "src")
    pio_include = os.path.join(pio_folder, "include")
    return project_folder, project_name, pio_folder, pio_src, pio_include

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
        
        marker_index = directory_path.find(platformio_marker)
        if marker_index != -1:
            part_of_path = directory_path[marker_index + len(platformio_marker):]
            logging.info(f"Files in directory '{part_of_path}':")
        else:
            logging.info(f"Files in the directory '{directory_path}':")

        if files:
            for file in files:
                logging.info(f"- {file}")
        else:
            logging.info("No files found in this directory.")
    except FileNotFoundError:
        logging.error(f"Error: Directory '{directory_path}' not found.")
    except PermissionError:
        logging.error(f"Error: Permission denied to access directory '{directory_path}'.")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

#------------------------------------------------------------------------------------------------------
def recreate_pio_folders(pio_folder, pio_src, pio_include):
    """Create or recreate PlatformIO folder structure."""
    # Ensure the main PlatformIO folder exists
    if not os.path.exists(pio_folder):
        os.makedirs(pio_folder)
        logging.info(f"Created PlatformIO folder: {pio_folder}")

    # Recreate src and include folders
    for folder in [pio_src, pio_include]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder)
        marker = "testProject"
        marker_index = folder.find(marker)
        if marker_index != -1:
            part_of_path = folder[marker_index + len(marker):]
            logging.info(f"Recreated folder [{part_of_path}]")
        else:
          logging.info(f"Recreated folder: [{folder}]")

    logging.info("PlatformIO folder structure recreated")

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

    marker = "testProject"
    marker_index = header_path.find(marker)
    if marker_index != -1:
        part_of_path = header_path[marker_index + len(marker):]
        logging.info(f"Updated {part_of_path} with new includes: {text}")
    else:
        logging.info(f"Updated {header_path} with new includes: {text}")




#------------------------------------------------------------------------------------------------------
def copy_data_folder(project_folder, pio_folder):
    """
    Delete existing data folder in pio_folder if it exists,
    then copy the data folder from the project folder to the PlatformIO folder if it exists.
    """
    source_data_folder = os.path.join(project_folder, 'data')
    destination_data_folder = os.path.join(pio_folder, 'data')

    # Delete existing data folder in pio_folder if it exists
    if os.path.exists(destination_data_folder):
        try:
            shutil.rmtree(destination_data_folder)
            marker = "testProject"
            marker_index = pio_folder.find(marker)
            if marker_index != -1:
                part_of_path = pio_folder[marker_index + len(marker):]
                logging.info(f"Deleted existing data folder in '{part_of_path}':")
            else:
                logging.info(f"Deleted existing data folder in {pio_folder}")

        except Exception as e:
            logging.error(f"Error deleting existing data folder: {str(e)}")
            return  # Exit the function if we can't delete the existing folder

    # Copy data folder from project folder to pio_folder if it exists
    if os.path.exists(source_data_folder):
        try:
            shutil.copytree(source_data_folder, destination_data_folder)
            marker = "testProject"
            marker1_index = source_data_folder.find(marker)
            marker2_index = destination_data_folder.find(marker)
            if marker1_index != -1:
                part_of_path1 = source_data_folder[marker_index + len(marker):]
                part_of_path2 = destination_data_folder[marker_index + len(marker):]
                logging.info(f"Copied data folder from {part_of_path1} to {part_of_path2}")
            else:
                logging.info(f"Copied data folder from {source_data_folder} to {destination_data_folder}")

        except Exception as e:
            logging.error(f"Error copying data folder: {str(e)}")
    else:
        logging.info("No data folder found in the project folder")

#------------------------------------------------------------------------------------------------------
def create_platformio_ini(pio_folder):
    """Create a platformio.ini file if it doesn't exist."""
    platformio_ini_path = os.path.join(pio_folder, 'platformio.ini')
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
            marker = "testProject"
            marker_index = platformio_ini_path.find(marker)
            if marker_index != -1:
                part_of_path = platformio_ini_content[marker_index + len(marker):]
                logging.info(f"Created platformio.ini file at {part_of_path}")
            else:
                logging.info(f"Created platformio.ini file at {platformio_ini_path}")
    else:
        marker = "testProject"
        marker_index = platformio_ini_path.find(marker)
        if marker_index != -1:
            part_of_path = platformio_ini_path[marker_index + len(marker):]
            logging.info(f"platformio.ini file already exists at [{part_of_path}]")
        else:
            logging.info(f"platformio.ini file already exists at [{platformio_ini_path}]")


#------------------------------------------------------------------------------------------------------
def remove_comments(content):
    """Remove C and C++ style comments from the content."""
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " "  # note: a space and not an empty string
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, content)

#------------------------------------------------------------------------------------------------------
def remove_comments_preserve_strings(content):
    """Remove C and C++ style comments from the content while preserving string literals."""
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " "
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|("(?:\\.|[^"\\])*")|\'(?:\\.|[^\\\'])*\'',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, content)

#------------------------------------------------------------------------------------------------------
#def remove_comments(content):
#    """Remove comments from the content."""
#    content = re.sub(r'//.*', '', content)  # Remove single-line comments
#    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)  # Remove multi-line comments
#    return content

def extract_and_comment_defines(pio_folder, pio_include):
    """
    Extract all #define statements (including functional and multi-line) from .h, .ino, and .cpp files,
    create allDefines.h, and comment original statements with info.
    """
    all_defines = []
    define_pattern = r'^\s*#define\s+(\w+)(?:\(.*?\))?\s*(.*?)(?:(?=\\\n)|$)'

    marker = "testProject"
    marker_index = pio_folder.find(marker)
    if marker_index != -1:
        part_of_path = pio_folder[marker_index + len(marker):]
        logging.info(f"Searching for #define statements in {part_of_path}")
    else:
        logging.info(f"Searching for #define statements in {pio_folder}")

    # Only search within pio_src and pio_include folders
    search_folders = [os.path.join(pio_folder, 'pio_src'), pio_include]

    for folder in search_folders:
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(('.h', '.ino', '.cpp')):
                    file_path = os.path.join(root, file)
                    logging.debug(f"Processing file: {file_path}")
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
                                    new_content.extend([f"//-- moved to allDefines.h // {line}" for line in full_define])
                                    logging.debug(f"Added #define: {macro_name}")
                                else:
                                    new_content.extend(full_define)
                            else:
                                new_content.append(line)
                            i += 1

                        # Write the modified content back to the file
                        with open(file_path, 'w') as f:
                            f.write('\n'.join(new_content))
                        logging.debug(f"Updated {file} with commented out #defines")

                    except Exception as e:
                        logging.error(f"Error processing file {file}: {str(e)}")

    # Create allDefines.h with all macros
    all_defines_path = os.path.join(pio_include, 'allDefines.h')
    logging.info(f"Creating allDefines.h with {len(all_defines)} macros")
    try:
        with open(all_defines_path, 'w') as f:
            f.write("#ifndef ALLDEFINES_H\n#define ALLDEFINES_H\n\n")
            for macro_name, macro_value in all_defines:
                f.write(f"{macro_value}\n\n")
            f.write("#endif // ALLDEFINES_H\n")

        marker_index = all_defines_path.find(marker)
        if marker_index != -1:
            part_of_path = all_defines_path[marker_index + len(marker):]
            logging.info(f"Creating allDefines.h in {part_of_path}")
        else:
            logging.info(f"Successfully created {all_defines_path}")

    except Exception as e:
        logging.error(f"Error creating allDefines.h: {str(e)}")

    logging.info(f"Extracted {len(all_defines)} #define statements")

#------------------------------------------------------------------------------------------------------
def create_header_file(header_path, base_name):
    """Create a new header file with basic structure."""
    
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

    marker_index = header_path.find(platformio_marker)
    if marker_index != -1:
        part1_path = header_path[marker_index + len(platformio_marker):]
        logging.info(f"Created new header file: [{part1_path}]")
    else:
        logging.info(f"Created new header file: {header_path}")

#------------------------------------------------------------------------------------------------------
def create_header_files(pio_src, pio_include, project_name):
    """Create all header files with basic structure."""
    for file in os.listdir(pio_src):
        #if file.endswith('.ino') and file != f"{project_name}.ino":
        if file.endswith('.ino'):
            base_name = os.path.splitext(file)[0]
            header_path = os.path.join(pio_include, f"{base_name}.h")
            process_header_file(header_path, base_name)

    logging.info("Processed regular header files")

#------------------------------------------------------------------------------------------------------
def fix_header_file(header_path, project_name, original_header_content):
    # Determine the corresponding .cpp or .ino file
    src_dir = os.path.join(os.path.dirname(os.path.dirname(header_path)), 'src')
    base_name = os.path.splitext(os.path.basename(header_path))[0]
    source_file = f"{base_name}.cpp"
    if not os.path.exists(os.path.join(src_dir, source_file)):
        source_file = f"{base_name}.ino"
    
    source_file_path = os.path.join(src_dir, source_file)
    prototypes = []
    
    if os.path.exists(source_file_path):
        with open(source_file_path, 'r') as f:
            file_content = f.read()
        prototypes = extract_prototypes(file_content, source_file)
        # Filter out setup() and loop()
        prototypes = [p for p in prototypes if not p.startswith(('void setup', 'void loop'))]
        logging.info(f"Extracted {len(prototypes)} prototypes from {source_file}")
        for proto in prototypes:
            logging.info(f"  Prototype: {proto}")
    else:
        logging.warning(f"Source file {source_file} not found for {header_path}")

    # If original_header_content is None, read the content from the file
    if original_header_content is None:
        try:
            with open(header_path, 'r') as f:
                original_header_content = f.read()
        except FileNotFoundError:
            logging.error(f"Header file not found: {header_path}")
            return
        except IOError as e:
            logging.error(f"Error reading header file {header_path}: {str(e)}")
            return

    # Prepare the new prototype section
    new_prototype_section = f"{prototypes_marker}\n"
    for prototype in prototypes:
        new_prototype_section += f"{prototype}\n"
    new_prototype_section += "\n"

    # Find the position to insert or replace prototypes in the original content
    prototype_start = original_header_content.find(prototypes_marker)
    if prototype_start != -1:
        # If marker exists, find the end of the prototype section
        prototype_end = original_header_content.find('\n\n', prototype_start)
        if prototype_end == -1:
            prototype_end = len(original_header_content)
        
        # Replace the old prototype section with the new one
        new_content = (original_header_content[:prototype_start] + 
                       new_prototype_section + 
                       original_header_content[prototype_end:])
    else:
        # If marker doesn't exist, insert prototypes after includes
        include_pos = original_header_content.rfind('#include')
        if include_pos != -1:
            insert_pos = original_header_content.find('\n', include_pos) + 1
        else:
            insert_pos = 0
        
        new_content = (original_header_content[:insert_pos] + 
                       "\n" + new_prototype_section + 
                       original_header_content[insert_pos:])

    # Compress multiple empty lines to a single empty line
    new_content = re.sub(r'\n\s*\n', '\n\n', new_content)

    # Write the updated content back to the file
    with open(header_path, 'w') as f:
        f.write(new_content)

    logging.info(f"Fixed header file: {header_path}")
    logging.info(f"Final number of prototypes added: {len(prototypes)}")
    
    # Log the actual prototypes added
    logging.info("Prototypes added:")
    for proto in prototypes:
        logging.info(f"  {proto}")
        
#------------------------------------------------------------------------------------------------------
def process_header_files(pio_include, project_name):
    for file in os.listdir(pio_include):
        if file.endswith('.h'):
            header_path = os.path.join(pio_include, file)
            if file == f"{project_name}.h":
                original_content = preserve_original_header(pio_include, project_name)
            else:
                with open(header_path, 'r') as f:
                    original_content = f.read()
            fix_header_file(header_path, project_name, original_content)


#------------------------------------------------------------------------------------------------------
def process_header_file(header_path, base_name):
    if os.path.exists(header_path):
        with open(header_path, 'r') as f:
            content = f.read()
        # Check for existing header guards
        has_guards = re.search(r'#ifndef\s+\w+_H.*?#define\s+\w+_H', content, re.DOTALL) is not None

        if not has_guards:
            # Add header guards if they don't exist
            content = f"#ifndef {base_name.upper()}_H\n#define {base_name.upper()}_H\n\n{content}\n#endif // {base_name.upper()}_H\n"
        
        # Check if allDefines.h is already included
        if '#include "allDefines.h"' not in content:
            # Add the include after Arduino.h if it exists, otherwise at the start of the guard
            if '#include <Arduino.h>' in content:
                content = content.replace('#include <Arduino.h>', '#include <Arduino.h>\n#include "allDefines.h"')
            else:
                insert_pos = content.find('\n', content.find('#define')) + 1
                content = content[:insert_pos] + '#include "allDefines.h"\n\n' + content[insert_pos:]
    else:
        # Create new file with header guards
        content = f"#ifndef {base_name.upper()}_H\n#define {base_name.upper()}_H\n\n#include <Arduino.h>\n#include \"allDefines.h\"\n\n#endif // {base_name.upper()}_H\n"

    # Extract sections
    guard_start = re.search(r'#ifndef\s+\w+_H.*?#define\s+\w+_H', content, re.DOTALL)
    guard_end = content.rfind('#endif')

    if guard_start and guard_end != -1:
        header = content[:guard_start.end()]
        body = content[guard_start.end():guard_end]
        footer = content[guard_end:]
    else:
        return  # If we can't find guards, don't modify the file

    # Process body
    includes = re.findall(r'#include.*', body)
    #local_headers = re.findall(r'//== Local Headers ==.*?(?=//==|$)', body, re.DOTALL)
    local_headers = re.findall(r'{localheaders_marker}.*?(?=//==|$)', body, re.DOTALL)
    externs = re.findall(r'extern.*?;', body, re.DOTALL)
    prototypes = re.findall(r'^\w+[\s\*]+\w+\s*\([^)]*\);', body, re.MULTILINE)

    # Remove processed items from body
    for item in includes + local_headers + externs + prototypes:
        body = body.replace(item, '')

    # Reconstruct file
    new_content = header + '\n'

    if includes:
        new_content += '\n'.join(includes) + '\n\n'

    #new_content += "//== Local Headers ==\n\n"
    new_content += f"{localheaders_marker}\n\n"

    if local_headers:
        new_content += local_headers[0].strip() + '\n\n'

    if externs:
        #new_content += "//== Extern Variables ==\n" + '\n'.join(externs) + '\n\n'
        new_content += f"{externvariables_marker}\n" + '\n'.join(externs) + '\n\n'

    if prototypes:
        #new_content += "//== Function Prototypes ==\n" + '\n'.join(prototypes) + '\n\n'
        new_content += f"{prototypes_marker}\n" + '\n'.join(prototypes) + '\n\n'

    new_content += body.strip() + '\n' + footer

    with open(header_path, 'w') as f:
        f.write(new_content)

    nrIncludes = len(includes)
    nrLocalHeaders = len(local_headers)
    nrExterns = len(externs)
    nrPrototypes = len(prototypes)
    marker = "testProject"
    marker_index = header_path.find(marker)
    if marker_index != -1:
        part_of_path = header_path[marker_index + len(marker):]
        logging.info(f"Processed header file: [{part_of_path}]")
    else:
        logging.info(f"Processed header file: [{header_path}]")

    logging.info("\t includes found      [" + str(nrIncludes)  +"]")

#------------------------------------------------------------------------------------------------------
def process_original_header_file(header_path, base_name):
    
    logging.info(f"Processing original header base_name: {base_name}")
    
    if os.path.exists(header_path):
        with open(header_path, 'r') as f:
            content = f.read()
        # Check for existing header guards
        has_guards = re.search(r'#ifndef\s+\w+_H.*?#define\s+\w+_H', content, re.DOTALL) is not None

        if not has_guards:
            # Add header guards if they don't exist
            content = f"#ifndef {base_name.upper()}_H\n#define {base_name.upper()}_H\n\n{content}\n#endif // {base_name.upper()}_H\n"
        
        # Check if allDefines.h is already included
        if '#include "allDefines.h"' not in content:
            # Add the include after Arduino.h if it exists, otherwise at the start of the guard
            if '#include <Arduino.h>' in content:
                content = content.replace('#include <Arduino.h>', '#include <Arduino.h>\n#include "allDefines.h"')
            else:
                insert_pos = content.find('\n', content.find('#define')) + 1
                content = content[:insert_pos] + '#include "allDefines.h"\n\n' + content[insert_pos:]
    else:
        # Create new file with header guards
        content = f"#ifndef {base_name.upper()}_H\n#define {base_name.upper()}_H\n\n#include <Arduino.h>\n#include \"allDefines.h\"\n\n#endif // {base_name.upper()}_H\n"

    # Extract sections
    guard_start = re.search(r'#ifndef\s+\w+_H.*?#define\s+\w+_H', content, re.DOTALL)
    guard_end = content.rfind('#endif')

    if guard_start and guard_end != -1:
        header = content[:guard_start.end()]
        body = content[guard_start.end():guard_end]
        footer = content[guard_end:]
    else:
        return  # If we can't find guards, don't modify the file

    # Process body
    includes = re.findall(r'#include.*', body)
    #local_headers = re.findall(r'//== Local Headers ==.*?(?=//==|$)', body, re.DOTALL)
    local_headers = re.findall(r'{localheaders_marker}.*?(?=//==|$)', body, re.DOTALL)
    externs = re.findall(r'extern.*?;', body, re.DOTALL)
    prototypes = re.findall(r'^\w+[\s\*]+\w+\s*\([^)]*\);', body, re.MULTILINE)

    # Remove processed items from body
    for item in includes + local_headers + externs + prototypes:
        body = body.replace(item, '')

    # Reconstruct file
    new_content = header + '\n'

    if includes:
        new_content += '\n'.join(includes) + '\n\n'

    #new_content += "//== Local Headers ==\n\n"

    #if local_headers:
    #    new_content += local_headers[0].strip() + '\n\n'

    #if externs:
    #    new_content += "//== Extern Variables ==\n" + '\n'.join(externs) + '\n\n'

    #if prototypes:
    #    new_content += "//== Function Prototypes ==\n" + '\n'.join(prototypes) + '\n\n'

    new_content += body.strip() + '\n' + footer

    with open(header_path, 'w') as f:
        f.write(new_content)

    marker_index = header_path.find(platformio_marker)
    if marker_index != -1:
        part_of_path = header_path[marker_index + len({platformio_marker}) -1:]
        logging.info(f"Processed original header file: {part_of_path}")
    else:
        logging.info(f"Processed original header file: {header_path}")

#------------------------------------------------------------------------------------------------------
def copy_project_files(project_folder, pio_src, pio_include, project_name):
    """Copy .ino files to pio_src and .h files to pio_include."""

    # Check if the file exists
    allDefines_path = os.path.join(pio_include, "allDefines.h")
    if os.path.exists(allDefines_path):
        # Delete the file
        os.remove(allDefines_path)
        logging.info("'allDefines.h' has been deleted.")
    else:
       logging.info("'allDefines.h' does not (yet) exist.")
    
    logging.info("Start copying project files to PlatformIO folders")

    for file in os.listdir(project_folder):
        if file.endswith('.ino'):
            shutil.copy2(os.path.join(project_folder, file), pio_src)
        elif file.endswith('.h'):
            shutil.copy2(os.path.join(project_folder, file), pio_include)
            if file.endswith('.h') and file != f"{project_name}.h":
                  logging.info(f"Processing original header file: {file}")
                  base_name = os.path.splitext(file)[0]
                  header_path = os.path.join(pio_include, f"{base_name}.h")
                  process_original_header_file(header_path, base_name)

    list_files_in_directory(pio_include)
    logging.info("Copied project files to PlatformIO folders")


#------------------------------------------------------------------------------------------------------
def extract_global_vars(pio_src, pio_include, project_name):
    """
    Extract global variable definitions from .ino files, .cpp files, and header files.
    Only variables declared outside of all function blocks are considered global.
    """
    global_vars = {}
    used_vars_by_file = {}

    # Comprehensive list of object types, including String
    types = r'(?:uint8_t|int8_t|uint16_t|int16_t|uint32_t|int32_t|uint64_t|int64_t|char|int|float|double|bool|boolean|long|short|unsigned|signed|size_t|void|String|time_t|struct tm)'

    var_pattern = rf'^\s*((?:static|volatile|const)?\s*{types}(?:\s*\*)*)\s+((?:\w+(?:\[.*?\])?(?:\s*=\s*[^,;]+)?\s*,\s*)*\w+(?:\[.*?\])?(?:\s*=\s*[^,;]+)?)\s*;'
    func_pattern = rf'^\s*(?:static|volatile|const)?\s*(?:{types})(?:\s*\*)*\s+(\w+)\s*\((.*?)\)'

    keywords = set(['if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
                    'break', 'continue', 'return', 'goto', 'typedef', 'struct', 'enum',
                    'union', 'sizeof', 'volatile', 'register', 'extern', 'inline'])

    files_to_process = [f for f in os.listdir(pio_src) if f.endswith(('.ino', '.cpp'))]
    files_to_process += [f for f in os.listdir(pio_include) if f.endswith('.h')]

    for file in files_to_process:
        if file.endswith(('.ino', '.cpp')):
            file_path = os.path.join(pio_src, file)
        else:  # It's a header file
            file_path = os.path.join(pio_include, file)

        logging.info("")
        marker_index = file_path.find(platformio_marker)
        if marker_index != -1:
            part_of_path = file_path[marker_index + len({platformio_marker}) -1:]
            logging.info(f"Processing file for global variables: {part_of_path}")
        else:
            logging.info(f"Processing file for global variables: {file_path}")

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Remove comments while preserving string literals
            content = remove_comments_preserve_strings(content)

            lines = content.split('\n')
            brace_level = 0
            in_function = False
            file_vars = []
            used_vars = set()

            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()

                # Check for function start
                if re.search(func_pattern, stripped_line) and not in_function:
                    in_function = True

                # Count braces
                brace_level += stripped_line.count('{') - stripped_line.count('}')

                # Check for function end
                if brace_level == 0:
                    in_function = False

                # Check for variable declarations only at global scope
                if not in_function and brace_level == 0:
                    var_match = re.search(var_pattern, stripped_line)
                    if var_match:
                        var_type = var_match.group(1).strip()
                        var_declarations = re.findall(r'([a-zA-Z]\w*(?:\[.*?\])?)(?:\s*=\s*[^,;]+)?', var_match.group(2))
                        for var_name in var_declarations:
                            base_name = var_name.split('[')[0].strip()
                            if base_name not in keywords:
                                file_vars.append((var_type, var_name, file))
                                logging.info(f"Global variable found in {file}: {var_type} {var_name}")

                # Collect all used variables
                used_vars.update(re.findall(r'\b(\w+)\b', stripped_line))

            global_vars[file] = file_vars
            used_vars_by_file[file] = used_vars
            #logging.info(f"Processed {file} successfully. Found {len(file_vars)} global variables.")

        except Exception as e:
            logging.error(f"Error processing file {file}: {str(e)}")
            logging.error(traceback.format_exc())

    logging.info("Extracted all global variables\n")
    return global_vars, used_vars_by_file

#------------------------------------------------------------------------------------------------------
def extract_class_instances(pio_src, pio_include, project_name):
    """
    Extract class instance definitions from .ino, .cpp, and .h files.
    Only global class instance declarations are considered.
    """
    class_instances = {}
    
    # Enhanced pattern for class instance declarations
    class_pattern = r'^\s*((?:const\s+)?(?:\w+::)*\w+(?:<.*?>)?)\s+(\w+)\s*(?:\((.*?)\))?\s*;'
    
    # Extended list of known classes
    known_classes = [
        'WiFiServer', 'ESP8266WebServer', 'ESP8266HTTPUpdateServer', 'WiFiClient',
        'File', 'FSInfo', 'WiFiManager', 'Timezone', 'DNSServer', 'ESP8266WebServer',
        'ESP8266mDNS', 'ArduinoOTA', 'PubSubClient', 'NTPClient', 'Ticker',
        'ESP8266HTTPClient', 'WebSocketsServer', 'AsyncWebServer', 'AsyncWebSocket',
        'SPIFFSConfig', 'HTTPClient', 'WiFiUDP', 'ESP8266WiFiMulti', 'ESP8266SSDP',
        'ESP8266HTTPUpdateServer', 'ESP8266WebServer', 'ESP8266mDNS'
    ]
    
    # Common class suffixes
    common_suffixes = ['Client', 'Server', 'Class', 'Manager', 'Handler', 'Controller', 'Service', 'Factory', 'Builder']
    
    files_to_process = [f for f in os.listdir(pio_src) if f.endswith(('.ino', '.cpp'))]
    files_to_process += [f for f in os.listdir(pio_include) if f.endswith('.h')]
    
    total_instances = 0  # Counter for total class instances
    
    for file in files_to_process:
        if file.endswith(('.ino', '.cpp')):
            file_path = os.path.join(pio_src, file)
        else: # It's a header file
            file_path = os.path.join(pio_include, file)
            
        marker_index = file_path.find(platformio_marker)
        if marker_index != -1:
            part_of_path = file_path[marker_index + len(platformio_marker):]
            logging.info(f"Processing file for class instances: {part_of_path}")
        else:
            logging.info(f"Processing file for class instances: {file_path}")

        try:
            with open(file_path, 'r') as f:
                content = f.read()
                    
            # Remove comments while preserving string literals
            content = remove_comments_preserve_strings(content)
                    
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
                        
                    # Check if it's a known class, ends with a common class suffix, or contains 'class'
                    is_class_instance = (
                        class_type in known_classes or
                        any(class_type.endswith(suffix) for suffix in common_suffixes) or
                        'class' in class_type.lower() or
                        re.search(r'\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)*', class_type) # CamelCase check
                    )
                        
                    if is_class_instance:
                        file_instances.append((class_type, instance_name, constructor_args, file))
                        logging.info(f"{file}: {class_type} {instance_name}")
                    else:
                        logging.debug(f"Possible class instance (not added) in {file}:{line_num}: {class_type} {instance_name}")
                            
            if file_instances:
                class_instances[file] = file_instances
                total_instances += len(file_instances)
                #logging.info(f"Processed {file} successfully. Found {len(file_instances)} class instances.")
                logging.info(f">> Found {len(file_instances)} class instances.")
            else:
                #logging.info(f"Processed {file} successfully. No class instances found.")
                logging.info(f">> No class instances found.")
                                    
        except Exception as e:
            logging.error(f"Error processing file {file}: {str(e)}")
            logging.error(traceback.format_exc())
              
    logging.info(f"Extracted all class instances. Total number of class instances found: {total_instances}")
    return class_instances

#------------------------------------------------------------------------------------------------------
def create_extern_declaration(var_type, var_name):
    """Create an extern declaration for a global variable."""
    var_name = var_name.split('=')[0].strip()  # Remove any initialization

    if '[' in var_name:
        var_name = var_name.split('[')[0] + '[]'  # Keep array notation but remove size

    var_type = var_type.replace('static', '').strip()  # Remove 'static' if present

    return f"extern {var_type} {var_name};"


#------------------------------------------------------------------------------------------------------
def add_extern_declarations(header_path, new_declarations):
    """Add extern declarations to a header file under the Extern Variables marker."""
    marker_index = header_path.find(platformio_marker)
    if marker_index != -1:
        short_header_path = header_path[marker_index + len(platformio_marker):]
    else:
        short_header_path = header_path

    with open(header_path, 'r+') as f:
        content = f.read()
        insert_pos = content.find(f"{externvariables_marker}")
        if insert_pos == -1:
            logging.warning(f"Could not find Extern Variables marker in {short_header_path}")
            return
        insert_pos += len(f"{externvariables_marker}\n")

        existing_declarations = set(content[insert_pos:].split('\n'))
        declarations_to_add = new_declarations - existing_declarations

        if declarations_to_add:
            new_content = (content[:insert_pos] +
                           '\n'.join(sorted(declarations_to_add)) + '\n\n' +
                           content[insert_pos:])
            f.seek(0)
            f.write(new_content)
            f.truncate()
            logging.info(f"Added {len(declarations_to_add)} extern declarations to [{short_header_path}]")
        else:
            logging.info(f"No new extern declarations added to [{short_header_path}]")

#------------------------------------------------------------------------------------------------------
def update_header_with_externs(pio_include, global_vars, class_instances, used_vars_by_file, project_name):
    main_header = f"{project_name}.h"
    main_header_content = preserve_original_header(pio_include, main_header)
    main_header_vars = set(re.findall(r'\b(\w+)\s*(?:=|;)', main_header_content))

    for file, used_vars in used_vars_by_file.items():
        header_path = os.path.join(pio_include, f"{os.path.splitext(file)[0]}.h")
        new_extern_declarations = set()
        new_includes = set()

        for defining_file, vars_in_file in global_vars.items():
            for var_type, var_name, _ in vars_in_file:
                if var_name in used_vars and defining_file != file:
                    # Skip adding extern for variables already declared in main header
                    if file == main_header and var_name in main_header_vars:
                        continue
                    extern_decl = f"extern {var_type} {var_name};"
                    new_extern_declarations.add(extern_decl)
                    
                    # Add include for the defining file's header
                    defining_header = os.path.splitext(defining_file)[0] + '.h'
                    if defining_header != os.path.basename(file):
                        new_includes.add(f'#include "{defining_header}"')

        # Process class instances
        for defining_file, instances in class_instances.items():
            for class_type, instance_name, _, _ in instances:
                if instance_name in used_vars and defining_file != file:
                    # Skip adding extern for instances already declared in main header
                    if file == main_header and instance_name in main_header_vars:
                        continue
                    extern_decl = f"extern {class_type} {instance_name};"
                    new_extern_declarations.add(extern_decl)
                    
                    # Add include for the defining file's header
                    defining_header = os.path.splitext(defining_file)[0] + '.h'
                    if defining_header != os.path.basename(file):
                        new_includes.add(f'#include "{defining_header}"')

        if new_extern_declarations or new_includes:
            update_header_file(header_path, new_extern_declarations, new_includes, file == main_header)

    logging.info(f"Processed extern declarations for all files")


#------------------------------------------------------------------------------------------------------
def update_header_file(header_path, new_extern_declarations, new_includes, is_main_header):
    with open(header_path, 'r+') as f:
        content = f.read()
        
        if is_main_header:
            # For main header, only add new includes
            if new_includes:
                include_pos = content.find(f"{localheaders_marker}")
                if include_pos != -1:
                    include_pos += len(f"{localheaders_marker}\n")
                    content = content[:include_pos] + '\n'.join(new_includes) + '\n' + content[include_pos:]
        else:
            # For other headers, add both includes and extern declarations
            if new_includes:
                include_pos = content.find(f"{localheaders_marker}")
                if include_pos != -1:
                    include_pos += len(f"{localheaders_marker}\n")
                    content = content[:include_pos] + '\n'.join(new_includes) + '\n' + content[include_pos:]
            
            if new_extern_declarations:
                extern_pos = content.find(f"{externvariables_marker}")
                if extern_pos != -1:
                    extern_pos += len(f"{externvariables_marker}\n")
                    content = content[:extern_pos] + '\n'.join(new_extern_declarations) + '\n' + content[extern_pos:]
        
        f.seek(0)
        f.write(content)
        f.truncate()

    logging.info(f"Updated header file: {os.path.basename(header_path)}")
    if new_includes:
        for include in new_includes:
            logging.info(f">> Added include: {include}")
    if new_extern_declarations and not is_main_header:
        for declaration in new_extern_declarations:
            logging.info(f">> Added declaration: {declaration}")
            
#------------------------------------------------------------------------------------------------------
def update_header_with_prototypes(header_path, prototypes):
    """Update header file with function prototypes."""
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
            logging.info(f"Added {len(prototypes_to_add)} function prototypes to [{short_header_path}]")
            for prototype in prototypes_to_add:
                logging.info(f"  - {prototype}")
        else:
            logging.info(f"No new function prototypes added to [{short_header_path}]")

#------------------------------------------------------------------------------------------------------
def extract_prototypes(content, file_name):
    # Remove comments and preprocess the content
    content = remove_comments(content)
    
    # Function definition pattern
    pattern = r'^\s*((?:static\s+)?(?:inline\s+)?(?:virtual\s+)?\w+(?:\s+\w+)*\s+[\*&]?\s*\w+\s*\([^)]*\))\s*(?:(?:const|override|final|noexcept)?\s*)*(?=\s*\{)'

    # Find all matches
    matches = re.finditer(pattern, content, re.MULTILINE)

    prototypes = []
    for match in matches:
        # Extract the function signature
        prototype = match.group(1).strip() + ';'
        
        # Ensure it's not a control structure
        if not re.match(r'\s*(if|else|for|while|switch|case|default)\s*\(', prototype):
            # Check if it's not inside a function (i.e., it's at the global scope)
            start_pos = match.start()
            preceding_text = content[:start_pos]
            if preceding_text.count('{') == preceding_text.count('}'):
                prototypes.append(prototype)
                logging.info(f"Extracted from {file_name}: {prototype}")

    return prototypes

#------------------------------------------------------------------------------------------------------
def find_undefined_functions_and_update_headers(pio_src, pio_include, function_reference_array):
    """
    Find undefined functions in pio_src files and update corresponding header files.
    """
    NON_FUNCTION_KEYWORDS = {'if', 'else', 'for', 'while', 'switch', 'case', 'default', 'do', 'return', 'break', 'continue'}

    logging.info("Starting to find undefined functions and update headers")

    for file in os.listdir(pio_src):
        if file.endswith('.cpp'):
            file_path = os.path.join(pio_src, file)
            base_name = os.path.splitext(file)[0]
            header_path = os.path.join(pio_include, f"{base_name}.h")

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
                logging.info(f"Functions to include in {file}:")
                for func in functions_to_include:
                    logging.info(f"  - {func} - {function_reference_array[func]}")

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

                        logging.info(f"Updated {short_header_path} with new includes:")
                        for include in new_includes:
                            logging.info(f"  - {include}")
                    else:
                        logging.warning(f"Could not find '{localheaders_marker}' in {short_header_path}")
                else:
                    logging.info(f"No new includes needed for {short_header_path}")
            else:
                logging.info(f"No undefined functions found in {file} that need to be included")

    logging.info("Completed finding undefined functions and updating headers")

#------------------------------------------------------------------------------------------------------
def process_function_references(pio_src, pio_include):
    function_reference_array = {}

    # Collect all function prototypes from header files
    for file in os.listdir(pio_include):
        if file.endswith('.h'):
            with open(os.path.join(pio_include, file), 'r') as f:
                content = f.read()
            prototypes = re.findall(r'^\w+[\s\*]+(\w+)\s*\([^)]*\);', content, re.MULTILINE)
            for func_name in prototypes:
                function_reference_array[func_name] = file

    # Print the function reference array
    logging.info("Function Reference Array:")
    for func, file in function_reference_array.items():
        logging.info(f"{func}: {file}")

    # Process .ino files
    for file in os.listdir(pio_src):
        if file.endswith('.ino') or file.endswith('.cpp'):
            base_name = os.path.splitext(file)[0]
            source_path = os.path.join(pio_src, file)
            header_path = os.path.join(pio_include, f"{base_name}.h")

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

    logging.info("Processed function references and updated header files")
    return function_reference_array  # Return the function_reference_array

#------------------------------------------------------------------------------------------------------
def process_ino_files(pio_src, pio_include, project_name, global_vars, class_instances):
    global global_extern_declarations
    global_extern_declarations = set()  # Reset global extern declarations

    logging.debug(f"Global vars at start of process_ino_files: {global_vars}")

    main_ino = f"{project_name}.ino"
    main_ino_path = os.path.join(pio_src, main_ino)

    files_to_process = [f for f in os.listdir(pio_src) if f.endswith('.ino')]
    if main_ino not in files_to_process and os.path.exists(main_ino_path):
        files_to_process.append(main_ino)

    used_vars_by_file = {}

    for file in files_to_process:
        logging.info("..")
        base_name = os.path.splitext(file)[0]
        header_path = os.path.join(pio_include, f"{base_name}.h")
        source_path = os.path.join(pio_src, file)

        marker1_index = source_path.find(platformio_marker)
        marker2_index = header_path.find(platformio_marker)
        if marker1_index != -1:
            part1_path = source_path[marker1_index + len(platformio_marker):]
            part2_path = header_path[marker2_index + len(platformio_marker):]
            logging.info(f"Processing file: [{part1_path}], header_path [{part2_path}]")
        else:
            logging.info(f"Processing file: {source_path}, header_path {header_path}")

        # Create the header file if it doesn't exist
        create_header_file(header_path, base_name)

        with open(source_path, 'r') as f:
            content = f.read()

        content_no_comments = remove_comments_preserve_strings(content)

        used_vars = set(re.findall(r'\b(\w+)\b', content_no_comments))
        used_vars_by_file[file] = used_vars
        logging.debug(f"Used vars in {file}: {used_vars}")

        prototypes = extract_prototypes(content_no_comments, file)
        logging.info(f"Found {len(prototypes)} prototypes in {file}")

        update_header_with_prototypes(header_path, prototypes)

        # Add include statement for the corresponding header
        include_statement = f'#include "{base_name}.h"'
        if include_statement not in content:
            content = f'{include_statement}\n\n{content}'

        # Write the updated content back to the file
        new_file_path = os.path.join(pio_src, f"{base_name}.cpp")
        with open(new_file_path, 'w') as f:
            f.write(content)

        # Remove the original .ino file
        os.remove(source_path)

    # Now that we have processed all files and collected used_vars_by_file, we can update headers with externs
    update_header_with_externs(pio_include, global_vars, class_instances, used_vars_by_file, project_name)

    logging.info("Processed .ino files: renamed, updated headers, and converted to .cpp")


#------------------------------------------------------------------------------------------------------
def preserve_original_headers(pio_include):
    """Read and preserve the original content of all existing header files."""
    original_headers = {}
    for file in os.listdir(pio_include):
        if file.endswith('.h'):
            header_path = os.path.join(pio_include, file)
            with open(header_path, 'r') as f:
                original_headers[file] = f.read()

    return original_headers

#------------------------------------------------------------------------------------------------------
def preserve_original_header(pio_include, file_name):
    """Read and preserve the original content of a specific header file."""
    header_path = os.path.join(pio_include, file_name)
    if os.path.exists(header_path):
        with open(header_path, 'r') as f:
            return f.read()
        
    return None

#------------------------------------------------------------------------------------------------------
def update_project_header(pio_include, project_name, original_content):
    """Update project header file with includes for all created headers while preserving original content."""
    project_header_path = os.path.join(pio_include, f"{project_name}.h")

    # Split the original content into sections
    sections = re.split(r'(//==.*?==)', original_content, flags=re.DOTALL)

    new_content = []
    local_includes = []

    # Process each section
    for i, section in enumerate(sections):
        if section.strip() == f"{localheaders_marker}":
            # Add new local includes here
            new_content.append(section + "\n")
            for file in os.listdir(pio_include):
                if file.endswith('.h') and file != f"{project_name}.h":
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

    logging.info(f"Updated project header {project_name}.h while preserving original content")


#------------------------------------------------------------------------------------------------------
def print_global_vars(global_vars):
    """Print the dictionary of global variables."""
    logging.info("Global Variables:")
    for file, vars in global_vars.items():
        logging.info(f"In file {file}:")
        for var_type, var_name, defining_file in vars:
            logging.info(f"  {var_type} {var_name} (defined in {defining_file})")

#------------------------------------------------------------------------------------------------------
def print_used_vars(used_vars_by_file):
    """Print the dictionary of used variables."""
    logging.info("Used Variables:")
    for file, vars in used_vars_by_file.items():
        logging.info(f"In file {file}:")
        for var_name in vars:
            logging.info(f"  {var_name}")

#------------------------------------------------------------------------------------------------------
def print_vars(global_vars, used_vars_by_file):
    """Print both global and used variables."""
    print_global_vars(global_vars)
    print_used_vars(used_vars_by_file)

#------------------------------------------------------------------------------------------------------
def print_class_instances(class_instances):
    """Print the dictionary of class instances."""
    print("\nClass instances:")
    for file, instances in class_instances.items():
        print(f"In file {file}:")
        for class_type, instance_name, constructor_args, defining_file in instances:
            print(f"  {class_type} {instance_name}({constructor_args}) (defined in {defining_file})")


#------------------------------------------------------------------------------------------------------
def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

#------------------------------------------------------------------------------------------------------
def main():
    setup_logging()
    args = parse_arguments()

    if args.backup:
        backup_project(args.project_dir)

    try:
        project_folder, project_name, pio_folder, pio_src, pio_include = get_project_info(args.project_dir)
        marker = "arduinoIDE2platformIO-convertor"
        logging.info(f"Project folder: {project_folder}")

        marker_index = pio_folder.find(marker)
        if marker_index != -1:
            part_of_path = pio_folder[marker_index + len(marker):]
            logging.info(f"PlatformIO folder: {part_of_path}")
        else:
            logging.info(f"PlatformIO folder: {pio_folder}")

        marker_index = pio_src.find(marker)
        if marker_index != -1:
            part_of_path = pio_src[marker_index + len(marker):]
            logging.info(f"PlatformIO src folder: {part_of_path}")
        else:
            logging.info(f"PlatformIO src folder: {pio_src}")
  
        marker_index = pio_include.find(marker)
        if marker_index != -1:
            part_of_path = pio_include[marker_index + len(marker):]
            logging.info(f"PlatformIO include folder: {part_of_path}")
        else: 
            logging.info(f"PlatformIO include folder: {pio_include}\n")

        recreate_pio_folders(pio_folder, pio_src, pio_include)

        if not os.path.exists(pio_folder):
            logging.error(f"PlatformIO folder does not exist: {pio_folder}")
            return

        copy_project_files(project_folder, pio_src, pio_include, project_name)
        copy_data_folder(project_folder, pio_folder)
        create_platformio_ini(pio_folder)
        extract_and_comment_defines(pio_folder, pio_include)
        create_header_files(pio_src, pio_include, project_name)

        original_headers = preserve_original_headers(pio_include)

        logging.info("Extracting global variables:")
        global_vars, used_vars_by_file = extract_global_vars(pio_src, pio_include, project_name)

        class_instances = extract_class_instances(pio_src, pio_include, project_name)
        if len(class_instances) == 0:
            logging.info(f"No class instances extracted")
        else:
            logging.info(f"Extracted class instances:")
            for file, instances in class_instances.items():
                for class_type, instance_name, _, _ in instances:
                    logging.info(f">> {file}: {class_type} {instance_name}")

        process_ino_files(pio_src, pio_include, project_name, global_vars, class_instances)

        # Update headers with externs, passing the project_name
        update_header_with_externs(pio_include, global_vars, class_instances, used_vars_by_file, project_name)

        function_reference_array = process_function_references(pio_src, pio_include)

        find_undefined_functions_and_update_headers(pio_src, pio_include, function_reference_array)

        main_header_path = os.path.join(pio_include, f"{project_name}.h")
        process_header_files(pio_include, project_name)

        logging.info("Arduino to PlatformIO conversion completed successfully")

    except Exception as e:
        logging.error(f"An error occurred during conversion: {str(e)}")
        logging.error(traceback.format_exc())
        print(f"An error occurred. Please check the log for details.")

#======================================================================================================
if __name__ == "__main__":
    main()
