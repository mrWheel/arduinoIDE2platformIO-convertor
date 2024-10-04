#------------------------------------------------------------
#
#   X-Reference a arduinoGlue.h file
# 
#   file name : crossReference.py   
#
#   by        : Willem Aandewiel
#
#   Version   : v0.79 (07-09-2024)
#
#   Usage: python3 crossReference.py <path to PlatformIO project
#
#   input file : arduinoGlue.h
#   output file: arduinoGlue.h (modified)
#
#   This program tries to determine what extern declared variables
#   are used in the source files. If not used in any other file
#   than the one where the variable is declared it will be commented out.
#
#   It does more-or-less the same for prototype functions
# 
#   It is to the user to remove "not used" variables or prototypes.
#   For prototypes it can me nessesary to move the prototypes to the
#   header file of the .cpp file.
#
#   license   : MIT (see at the bottom of this file)
#------------------------------------------------------------


import sys
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='- %(levelname)s - %(message)s')

def process_extern_variables(arduino_glue_content, src_folder):
    extern_pattern = re.compile(r'extern\s+(\w+)\s+(\w+)')
    extern_vars = extern_pattern.findall(arduino_glue_content)
    
    var_usage = {var: set() for _, var in extern_vars}
    var_source = {var: "" for _, var in extern_vars}
    
    for root, _, files in os.walk(src_folder):
        for file in files:
            if file.endswith('.cpp') or file.endswith('.h'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    for _, var in extern_vars:
                        if re.search(r'\b' + var + r'\b', content):
                            if not var_source[var]:
                                var_source[var] = os.path.splitext(file)[0]
                            else:
                                var_usage[var].add(file)
                except IOError as e:
                    logging.error(f"Error reading {file_path}: {e}")
    
    new_content = []
    is_macro = False
    for line in arduino_glue_content.split('\n'):
        if line.strip().startswith('#define'):
            is_macro = True
        
        if is_macro:
            new_content.append(line)
            is_macro = line.strip().endswith('\\')
        else:
            extern_match = extern_pattern.search(line)
            if extern_match:
                var_type, var_name = extern_match.groups()
                usage = var_usage[var_name]
                source = var_source[var_name]
                if not usage:
                    new_content.append(f"//-- not used {line}")
                else:
                    usage_str = ", ".join(usage)
                    new_content.append(f"//-- used in {usage_str}")
                    if "//--" not in line:
                        new_content.append(f"{line:<70} //-- from {source}")
                    else:
                        new_content.append(line)
            else:
                new_content.append(line)
    
    return "\n".join(new_content), extern_vars, var_usage

def process_prototypes(arduino_glue_content, src_folder):
    prototype_pattern = re.compile(r'(\w+\s+\w+\s*\([^)]*\)\s*;)')
    prototypes = prototype_pattern.findall(arduino_glue_content)
    
    prototype_usage = {p: set() for p in prototypes}
    
    for root, _, files in os.walk(src_folder):
        for file in files:
            if file.endswith('.cpp'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    for prototype in prototypes:
                        func_name = re.search(r'(\w+)\s*\(', prototype).group(1)
                        if re.search(r'\b' + func_name + r'\b', content):
                            if os.path.basename(file_path) != 'arduinoGlue.cpp':
                                prototype_usage[prototype].add(os.path.basename(file_path))
                except IOError as e:
                    logging.error(f"Error reading {file_path}: {e}")
    
    new_content = []
    for line in arduino_glue_content.split('\n'):
        prototype_match = prototype_pattern.search(line)
        if prototype_match:
            prototype = prototype_match.group(1)
            usage = prototype_usage[prototype]
            if not usage:
                new_content.append("//-- not used anywhere")
            else:
                usage_str = ", ".join(usage)
                new_content.append(f"//-- Used in: {usage_str}")
            new_content.append(line)
        else:
            new_content.append(line)
    
    return "\n".join(new_content)

def process_arduino_project(project_path):
    try:
        arduino_glue_path = os.path.join(project_path, 'include', 'arduinoGlue.h')
        temp_path = os.path.join(project_path, 'include', 'modifiedGlue.h')
        src_folder = os.path.join(project_path, 'src')
        
        logging.info(f"arduinoGlue.h: {arduino_glue_path}")
        
        # Read arduinoGlue.h
        try:
            with open(arduino_glue_path, 'r') as f:
                arduino_glue_content = f.read()
        except IOError as e:
            logging.error(f"Error reading arduinoGlue.h: {e}")
            return
        
        # Process extern variables
        arduino_glue_content, extern_vars, var_usage = process_extern_variables(arduino_glue_content, src_folder)
        
        # Process prototypes
        arduino_glue_content = process_prototypes(arduino_glue_content, src_folder)
        
        # Write updated arduinoGlue.h
        try:
            logging.info(f"write to {temp_path}")
            with open(temp_path, 'w') as f:
                f.write(arduino_glue_content)
        except IOError as e:
            logging.error(f"Error writing to arduinoGlue.h: {e}")
            return
        
        # Output results for extern variables
        for var_type, var_name in extern_vars:
            usage = var_usage[var_name]
            if len(usage) > 1:
                usage_str = ", ".join(usage)
                print(f"{var_type} {var_name}  {usage_str}")
        
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python crossReference.py <path_to_platformio_project>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    process_arduino_project(project_path)


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

