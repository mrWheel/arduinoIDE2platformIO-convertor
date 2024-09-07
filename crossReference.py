import sys
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_arduino_project(project_path):
    try:
        arduino_glue_path = os.path.join(project_path, 'include', 'arduinoGlue.h')
        temp_path = os.path.join(project_path, 'include', 'tempGlue.h')
        src_folder = os.path.join(project_path, 'src')
        
        logging.info(f"arduinoGlue.h: {arduino_glue_path}")
        
        # Read arduinoGlue.h
        try:
            with open(arduino_glue_path, 'r') as f:
                arduino_glue_content = f.read()
        except IOError as e:
            logging.error(f"Error reading arduinoGlue.h: {e}")
            return
        
        # Find all extern declarations
        extern_pattern = re.compile(r'extern\s+(\w+)\s+(\w+)')
        extern_vars = extern_pattern.findall(arduino_glue_content)
        
        # Process src files
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
        
        # Update arduinoGlue.h
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
                        # Preserve original formatting and add source only if not already present
                        if "//--" not in line:
                            new_content.append(f"{line:<70} //-- from {source}")
                        else:
                            new_content.append(line)
                else:
                    new_content.append(line)
        
        # Write updated arduinoGlue.h
        try:
            logging.info(f"write to {temp_path}")
            with open(temp_path, 'w') as f:
                f.write("\n".join(new_content))
        except IOError as e:
            logging.error(f"Error writing to arduinoGlue.h: {e}")
            return
        
        # Output results
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