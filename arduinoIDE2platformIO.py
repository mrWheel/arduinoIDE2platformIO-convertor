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
        logging.info(f"Recreated folder: {folder}")

    logging.info("PlatformIO folder structure recreated")

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
            logging.info(f"Deleted existing data folder in {pio_folder}")
        except Exception as e:
            logging.error(f"Error deleting existing data folder: {str(e)}")
            return  # Exit the function if we can't delete the existing folder

    # Copy data folder from project folder to pio_folder if it exists
    if os.path.exists(source_data_folder):
        try:
            shutil.copytree(source_data_folder, destination_data_folder)
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
platform = <select platform with "PIO Home" -> Platforms>
board = <select board with "PIO Home" -> Boards>
framework = arduino
board_build.filesystem = <if appropriate>
monitor_speed = 115200
upload_speed = 115200
upload_port = <select port like "/dev/cu.usbserial-3224144">
build_flags =
\t-D DEBUG

lib_ldf_mode = deep+

lib_deps =
\t<select libraries with "PIO Home" -> Libraries

monitor_filters =
  esp8266_exception_decoder
"""
        with open(platformio_ini_path, 'w') as f:
            f.write(platformio_ini_content)
        logging.info(f"Created platformio.ini file at {platformio_ini_path}")
    else:
        logging.info(f"platformio.ini file already exists at {platformio_ini_path}")


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
def extract_and_comment_defines(pio_folder, pio_include):
    """
    Extract all #define statements (including functional and multi-line) from .h, .ino, and .cpp files,
    create allDefines.h, and comment original statements with info.
    """
    all_defines = []
    define_pattern = r'^\s*#define\s+(\w+)(?:\(.*?\))?\s*(.*?)(?:(?=\\\n)|$)'

    logging.info(f"Searching for #define statements in {pio_folder}")

    for root, _, files in os.walk(pio_folder):
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
        f.write("//== Local Headers ==")
        f.write("\n")
        f.write("#include \"allDefines.h\"\n\n")
        f.write("//== Extern Variables ==")
        f.write("\n\n")
        f.write("//== Function Prototypes ==")
        f.write("\n\n")
        f.write(f"#endif // {base_name.upper()}_H\n")
    logging.info(f"Created new header file: {header_path}")

#------------------------------------------------------------------------------------------------------
def create_header_files(pio_src, pio_include, project_name):
    for file in os.listdir(pio_src):
        if file.endswith('.ino') and file != f"{project_name}.ino":
            base_name = os.path.splitext(file)[0]
            header_path = os.path.join(pio_include, f"{base_name}.h")
            process_header_file(header_path, base_name)

    logging.info("Processed regular header files")

#------------------------------------------------------------------------------------------------------
def fix_main_header_file(header_path, project_name):
    with open(header_path, 'r') as f:
        content = f.read()

    # Remove existing header guards if present
    content = re.sub(r'#ifndef.*?_H\s*#define.*?_H', '', content, flags=re.DOTALL)
    content = re.sub(r'#endif.*?_H', '', content, flags=re.DOTALL)

    # Ensure includes are at the top
    includes = re.findall(r'#include.*', content, re.MULTILINE)
    content_without_includes = re.sub(r'#include.*\n', '', content, flags=re.MULTILINE)

    # Reconstruct the file
    new_content = '\n'.join(includes) + '\n\n' if includes else ''
    new_content += content_without_includes.strip() + '\n'

    # Add header guards
    final_content = f"#ifndef {project_name.upper()}_H\n"
    final_content += f"#define {project_name.upper()}_H\n\n"
    final_content += new_content
    final_content += f"\n#endif // {project_name.upper()}_H\n"

    with open(header_path, 'w') as f:
        f.write(final_content)

    logging.info(f"Fixed main header file: {header_path}")

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
    local_headers = re.findall(r'//== Local Headers ==.*?(?=//==|$)', body, re.DOTALL)
    externs = re.findall(r'extern.*?;', body, re.DOTALL)
    prototypes = re.findall(r'^\w+[\s\*]+\w+\s*\([^)]*\);', body, re.MULTILINE)

    # Remove processed items from body
    for item in includes + local_headers + externs + prototypes:
        body = body.replace(item, '')

    # Reconstruct file
    new_content = header + '\n'

    if includes:
        new_content += '\n'.join(includes) + '\n\n'

    new_content += "//== Local Headers ==\n\n"

    if local_headers:
        new_content += local_headers[0].strip() + '\n\n'

    if externs:
        new_content += "//== Extern Variables ==\n" + '\n'.join(externs) + '\n\n'

    if prototypes:
        new_content += "//== Function Prototypes ==\n" + '\n'.join(prototypes) + '\n\n'

    new_content += body.strip() + '\n' + footer

    with open(header_path, 'w') as f:
        f.write(new_content)

    logging.info(f"Processed header file: {header_path}")

#------------------------------------------------------------------------------------------------------
def copy_project_files(project_folder, pio_src, pio_include):
    """Copy .ino files to pio_src and .h files to pio_include."""
    for file in os.listdir(project_folder):
        if file.endswith('.ino'):
            shutil.copy2(os.path.join(project_folder, file), pio_src)
        elif file.endswith('.h'):
            shutil.copy2(os.path.join(project_folder, file), pio_include)
    logging.info("Copied project files to PlatformIO folders")


#------------------------------------------------------------------------------------------------------
def extract_global_vars(pio_src, pio_include, project_name):
    """
    Extract global variable definitions from .ino files and the main project header file.
    Only variables declared outside of all function blocks are considered global.
    """
    global_vars = {}

    # Comprehensive list of object types, including String
    types = r'(?:uint8_t|int8_t|uint16_t|int16_t|uint32_t|int32_t|uint64_t|int64_t|char|int|float|double|bool|long|short|unsigned|signed|size_t|void|String)'

    var_pattern = rf'^\s*((?:static|volatile|const)?\s*{types}(?:\s*\*)*)\s+((?:\w+(?:\[.*?\])?(?:\s*=\s*[^,;]+)?\s*,\s*)*\w+(?:\[.*?\])?(?:\s*=\s*[^,;]+)?)\s*;'
    func_pattern = rf'^\s*(?:static|volatile|const)?\s*(?:{types})(?:\s*\*)*\s+(\w+)\s*\((.*?)\)'

    keywords = set(['if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
                    'break', 'continue', 'return', 'goto', 'typedef', 'struct', 'enum',
                    'union', 'sizeof', 'volatile', 'register', 'extern', 'inline'])

    files_to_process = [f for f in os.listdir(pio_src) if f.endswith('.ino') or f.endswith('.cpp')]
    main_ino = f"{project_name}.ino"
    if main_ino not in files_to_process and os.path.exists(os.path.join(pio_src, main_ino)):
        files_to_process.append(main_ino)

    # Add the main project header file
    main_header = f"{project_name}.h"
    main_header_path = os.path.join(pio_include, main_header)
    if os.path.exists(main_header_path):
        files_to_process.append(main_header)

    for file in files_to_process:
        if file.endswith(('.ino', '.cpp')):
            file_path = os.path.join(pio_src, file)
        else:  # It's the main header file
            file_path = main_header_path

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
                                file_vars.append((var_type, var_name, file))  # Note: added file name here
                                logging.debug(f"Found global variable in {file}:{line_num}: {var_type} {var_name}")

            global_vars[file] = file_vars
            logging.info(f"Processed {file} successfully. Found {len(file_vars)} global variables.")

        except Exception as e:
            logging.error(f"Error processing file {file}: {str(e)}")
            logging.error(traceback.format_exc())

    logging.info("Extracted all global variables")
    return global_vars

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
    
    for file in files_to_process:
        if file.endswith(('.ino', '.cpp')):
            file_path = os.path.join(pio_src, file)
        else: # It's a header file
            file_path = os.path.join(pio_include, file)
            
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
                            logging.debug(f"Found class instance in {file}:{line_num}: {class_type} {instance_name}({constructor_args})")
                        else:
                            logging.debug(f"Possible class instance (not added) in {file}:{line_num}: {class_type} {instance_name}")
                            
                            if file_instances:
                                class_instances[file] = file_instances
                                logging.info(f"Processed {file} successfully. Found {len(file_instances)} class instances.")
                            else:
                                logging.info(f"Processed {file} successfully. No class instances found.")
                                    
        except Exception as e:
            logging.error(f"Error processing file {file}: {str(e)}")
            logging.error(traceback.format_exc())
              
            logging.info("Extracted all class instances")
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
    with open(header_path, 'r+') as f:
        content = f.read()
        insert_pos = content.find("//== Extern Variables ==")
        if insert_pos == -1:
            logging.warning(f"Could not find Extern Variables marker in {header_path}")
            return
        insert_pos += len("//== Extern Variables ==\n")

        existing_declarations = set(content[insert_pos:].split('\n'))
        declarations_to_add = new_declarations - existing_declarations

        if declarations_to_add:
            new_content = (content[:insert_pos] +
                           '\n'.join(sorted(declarations_to_add)) + '\n\n' +
                           content[insert_pos:])
            f.seek(0)
            f.write(new_content)
            f.truncate()
            logging.info(f"Added {len(declarations_to_add)} extern declarations to {header_path}")
        else:
            logging.info(f"No new extern declarations added to {header_path}")

#------------------------------------------------------------------------------------------------------
def update_header_with_externs(pio_include, global_vars, class_instances, used_vars_by_file):
    """Update header files with extern declarations for used global variables and class instances."""
    global_extern_declarations = set()

    # Process global variables
    all_globals = [(var_type, var_name, defining_file) 
                   for file, vars in global_vars.items() 
                   for var_type, var_name, defining_file in vars]

    # Process class instances
    all_instances = [(class_type, instance_name, defining_file) 
                     for file, instances in class_instances.items() 
                     for class_type, instance_name, _, defining_file in instances]

    # Combine globals and class instances
    all_declarations = all_globals + all_instances

    # Create extern declarations for each file
    for file, used_vars in used_vars_by_file.items():
        new_extern_declarations = set()
        for var_type, var_name, defining_file in all_declarations:
            if var_name in used_vars and defining_file != file:
                if (var_type, var_name) in all_globals:
                    extern_decl = f"extern {var_type} {var_name};"
                else:
                    extern_decl = f"extern {var_type} {var_name};"
                new_extern_declarations.add(extern_decl)
                global_extern_declarations.add(extern_decl)

        if new_extern_declarations:
            header_path = os.path.join(pio_include, f"{os.path.splitext(file)[0]}.h")
            add_extern_declarations(header_path, new_extern_declarations)

    logging.info(f"Processed extern declarations for all files")

# Example usage:
# update_header_with_externs(pio_include, global_vars, class_instances, used_vars_by_file)
#------------------------------------------------------------------------------------------------------
def extract_prototypes(content):
    """Extract function prototypes from the given content."""
    # Remove comments
    content = remove_comments(content)

    # Comprehensive list of object types, including String
    types = r'(?:uint8_t|int8_t|uint16_t|int16_t|uint32_t|int32_t|uint64_t|int64_t|char|int|float|double|bool|long|short|unsigned|signed|size_t|void|String)'

    func_def_pattern = rf'\b(?:static|volatile|const)?\s*({types})(?:\s*\*)?\s+(\w+)\s*\([^)]*\)\s*{{'

    func_defs = re.finditer(func_def_pattern, content, re.MULTILINE)

    prototypes = []
    for match in func_defs:
        full_match = match.group(0)
        return_type = match.group(1)
        func_name = match.group(2)
        prototype = full_match[:-1].strip() + ";"
        prototypes.append(prototype)
        logging.debug(f"Found function: {return_type} {func_name}")

    return prototypes


#------------------------------------------------------------------------------------------------------
def update_header_with_prototypes(header_path, prototypes):
    """Update header file with function prototypes."""
    with open(header_path, 'r+') as f:
        content = f.read()
        insert_pos = content.find("//== Function Prototypes ==") + len("//== Function Prototypes ==\n")
        new_prototypes = []
        for proto in prototypes:
            if proto not in content:
                new_prototypes.append(proto)
                logging.debug(f"Adding Prototype to {header_path}: {proto}")

        if new_prototypes:
            new_content = (content[:insert_pos] +
                           '\n'.join(new_prototypes) + '\n\n' +
                           content[insert_pos:])
            f.seek(0)
            f.write(new_content)
            f.truncate()
    logging.info(f"Updated header {header_path} with {len(new_prototypes)} new Function Prototypes")

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
    print("Function Reference Array:")
    for func, file in function_reference_array.items():
        print(f"{func}: {file}")

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

            # Update the header file with necessary includes
            if headers_to_include:
                with open(header_path, 'r') as f:
                    header_content = f.readlines()

                local_headers_pos = next((i for i, line in enumerate(header_content) if "//== Local Headers ==" in line), -1)
                if local_headers_pos != -1:
                    insert_pos = local_headers_pos + 1
                    new_includes = [f'#include "{header}"\n' for header in headers_to_include if header != f"{base_name}.h"]
                    header_content[insert_pos:insert_pos] = new_includes

                    with open(header_path, 'w') as f:
                        f.writelines(header_content)

                    logging.info(f"Updated {header_path} with new includes: {', '.join(new_includes)}")

    logging.info("Processed function references and updated header files")

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
        base_name = os.path.splitext(file)[0]
        header_path = os.path.join(pio_include, f"{base_name}.h")
        source_path = os.path.join(pio_src, file)

        logging.info(f"Processing file: {source_path}, header_path {header_path}")

        # Create the header file if it doesn't exist
        create_header_file(header_path, base_name)

        with open(source_path, 'r') as f:
            content = f.read()

        content_no_comments = remove_comments_preserve_strings(content)

        used_vars = set(re.findall(r'\b(\w+)\b', content_no_comments))
        used_vars_by_file[file] = used_vars
        logging.debug(f"Used vars in {file}: {used_vars}")

        prototypes = extract_prototypes(content_no_comments)
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
    update_header_with_externs(pio_include, global_vars, class_instances, used_vars_by_file)

    logging.info("Processed .ino files: renamed, updated headers, and converted to .cpp")

#------------------------------------------------------------------------------------------------------
def preserve_original_header(pio_include, project_name):
    """Read and preserve the original content of the project header file."""
    project_header_path = os.path.join(pio_include, f"{project_name}.h")
    with open(project_header_path, 'r') as f:
        return f.read()

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
        if section.strip() == "//== Local Headers ==":
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
        else:
            new_content.append(section)

    # Write the updated content back to the file
    with open(project_header_path, 'w') as f:
        f.writelines(new_content)

    logging.info(f"Updated project header {project_name}.h while preserving original content")


#------------------------------------------------------------------------------------------------------
def print_global_vars(global_vars):
    """Print the dictionary of global variables."""
    print("Global Variables:")
    for file, vars in global_vars.items():
        print(f"In file {file}:")
        for var_type, var_name, defining_file in vars:
            print(f"  {var_type} {var_name} (defined in {defining_file})")

#------------------------------------------------------------------------------------------------------
def print_class_instances(class_instances):
    """Print the dictionary of class instances."""
    print("\nClass instances:")
    for file, instances in class_instances.items():
        print(f"In file {file}:")
        for class_type, instance_name, constructor_args, defining_file in instances:
            print(f"  {class_type} {instance_name}({constructor_args}) (defined in {defining_file})")

#------------------------------------------------------------------------------------------------------
def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert Arduino project to PlatformIO structure.")
    parser.add_argument("--project_dir", default=os.getcwd(), help="Path to the project directory")
    parser.add_argument("--backup", action="store_true", help="Create a backup of original files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


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

        logging.info(f"Project folder: {project_folder}")
        logging.info(f"PlatformIO folder: {pio_folder}")
        logging.info(f"PlatformIO src folder: {pio_src}")
        logging.info(f"PlatformIO include folder: {pio_include}\n")

        recreate_pio_folders(pio_folder, pio_src, pio_include)

        if not os.path.exists(pio_folder):
            logging.error(f"PlatformIO folder does not exist: {pio_folder}")
            return

        copy_project_files(project_folder, pio_src, pio_include)
        copy_data_folder(project_folder, pio_folder)
        create_platformio_ini(pio_folder)
        extract_and_comment_defines(pio_folder, pio_include)
        create_header_files(pio_src, pio_include, project_name)

        original_header_content = preserve_original_header(pio_include, project_name)
        #logging.info(f"original {project_name}.h:\n{original_header_content}\n\n")

        global_vars = extract_global_vars(pio_src, pio_include, project_name)
        class_instances = extract_class_instances(pio_src, pio_include, project_name)
        logging.debug(f"Extracted global vars: {global_vars}")
        print_global_vars(global_vars)
        logging.debug(f"Extracted class instances: {class_instances}")
        print_class_instances(class_instances)

        process_ino_files(pio_src, pio_include, project_name, global_vars, class_instances)

        process_function_references(pio_src, pio_include)

        # Process the main project header file last
        ##original_header_content = preserve_original_header(pio_include, project_name)
        #logging.info(f"original {project_name}.h:\n{original_header_content}\n\n")
        update_project_header(pio_include, project_name, original_header_content)
        main_header_path = os.path.join(pio_include, f"{project_name}.h")
        fix_main_header_file(main_header_path, project_name)

        logging.info("Arduino to PlatformIO conversion completed successfully")

    except Exception as e:
        logging.error(f"An error occurred during conversion: {str(e)}")
        logging.error(traceback.format_exc())
        print(f"An error occurred. Please check the log for details.")


#======================================================================================================
if __name__ == "__main__":
    main()
  
