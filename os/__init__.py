#!/usr/bin/env python3
#    PyOS, an "operating system" running on Python.
#    Copyright (C) 2025 Muser
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
import sys, shlex
from pathlib import Path
import os
import getpass
import socket
import re # NEW: Import the regex module for variable expansion
import importlib # NEW: Import importlib for dynamic package loading
import subprocess # NEW: Import subprocess for launching GUI apps

# --- Check and import passlib ---
try:
    from passlib.hash import sha512_crypt
except ImportError:
    print("Error: The 'passlib' Python library is not installed.", file=sys.stderr)
    print("Please install it using pip:", file=sys.stderr)
    print("  pip install passlib", file=sys.stderr)
    print("If you are on Ubuntu/Debian, you might also try:", file=sys.stderr)
    print("  sudo apt install python3-passlib", file=sys.stderr)
    sys.exit(1)
# --- End passlib check ---

# Add the _packages directory to sys.path so gum and other packages can be imported
curr_dir = Path(__file__).resolve().parent
packages_dir = curr_dir / "_packages"
if str(packages_dir) not in sys.path:
    sys.path.append(str(packages_dir))

# --- Package Manager Check and Import ---
# This function checks if the 'gum' package manager can be imported.
def checkforpackagemanager():
    try:
        # Attempt to import gum. This will succeed if _packages/gum/__init__.py exists
        # and is correctly set up.
        import gum 
        return 0 # Success
    except ModuleNotFoundError:
        print("E: package manager 'gum' not found. Ensure it's built correctly in _packages/gum.", file=sys.stderr)
        return 1 # Failure

# Import gum after sys.path is updated and checkforpackagemanager is defined
import gum 
# --- End Package Manager Check and Import ---

# --- Global dictionary to store dynamically loaded package commands ---
_package_commands = {} # Maps command_name -> function_to_handle_command

# --- Function to register package commands ---
def register_package_command(command_name, handler_func):
    """
    Registers a command from an installed package.
    command_name: The string command (e.g., "calc").
    handler_func: The Python function that handles this command.
    """
    if command_name in _package_commands:
        print(f"Warning: Command '{command_name}' from package is already registered. Overwriting.", file=sys.stderr)
    _package_commands[command_name] = handler_func
    # print(f"Registered package command: {command_name}") # Optional debug

# --- Function to load commands from installed packages ---
def load_package_commands():
    """
    Scans the _packages directory, imports Python packages, and calls their
    'register_shell_commands' function to register new commands with PyOS.
    """
    packages_root_dir = curr_dir / "_packages" # Use the global curr_dir
    
    if not packages_root_dir.is_dir():
        print(f"Warning: Package root directory '{packages_root_dir}' not found. No external commands will be loaded.", file=sys.stderr)
        return

    # Ensure the root package directory is in sys.path (already done above, but good to be explicit)
    if str(packages_root_dir) not in sys.path:
        sys.path.insert(0, str(packages_root_dir)) # Insert at the beginning to prioritize packages

    for item in packages_root_dir.iterdir():
        # Check if it's a directory and contains an __init__.py (i.e., a Python package)
        if item.is_dir() and (item / "__init__.py").is_file(): 
            module_name = item.name # Get the directory name (e.g., 'calculator')
            try:
                # Dynamically import the package's __init__.py as a module
                package_module = importlib.import_module(module_name)
                
                # Check if the package has a specific function to register its commands
                # We'll expect a function named 'register_shell_commands' in its __init__.py
                if hasattr(package_module, 'register_shell_commands') and callable(package_module.register_shell_commands):
                    # Call this function, passing our shell's registration mechanism
                    package_module.register_shell_commands(register_package_command)
                    # print(f"Loaded commands from package: {module_name}") # Optional debug
                # else:
                    # print(f"Info: Package '{module_name}' has no 'register_shell_commands' function. Skipping command registration.", file=sys.stderr)

            except Exception as e:
                print(f"Error loading commands from package '{module_name}': {e}", file=sys.stderr)

# Call load_package_commands after sys.path is set up and gum is imported
load_package_commands()
# --- End NEW: Package Command System ---


def checkforbuild():
    """
    Checks if the '_isbuilded' file exists in the same directory as the script
    AND if its content is exactly "True".
    Returns True if both conditions are met, False otherwise.
    """
    # Get the directory of the current script file
    curr_dir = Path(__file__).resolve().parent
    
    # Construct the path to the _isbuilded file
    build_flag_file = curr_dir / "_isbuilded"
    
    # First, check if the file exists
    if not build_flag_file.is_file():
        return False # File doesn't exist, so it's not built

    # If the file exists, try to read its content
    try:
        # Use the full path to open the file to avoid issues if the current working directory changes
        with open(build_flag_file, 'r') as f: # Open in read mode ('r')
            content = f.read().strip() # .strip() removes any leading/trailing whitespace (like newlines)
        
        # Check if the content is exactly "True"
        is_content_true = (content == "True")
        
        # Return True only if the file exists AND its content is "True"
        return is_content_true

    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error reading _isbuilded file: {e}", file=sys.stderr)
        return False

def get_stored_passwords(passwords_file_path):
    """
    Reads the _passwords file and parses its custom format.
    Returns a dictionary of {username: hashed_password}.
    It will store all valid entries found, and the last entry for a given username
    will overwrite previous ones, effectively getting the "latest" password.
    """
    stored_data = {}
    if not Path(passwords_file_path).is_file():
        return stored_data # Return empty if file doesn't exist

    try:
        with open(passwords_file_path, 'r') as f:
            lines = f.readlines()
            for line in lines: # Iterate through lines normally
                line = line.strip()
                # Look for lines that contain ':' and are not just '{' or '}'
                if ':' in line and not line.startswith('{') and not line.endswith('}'):
                    content = line.strip(';') # Remove trailing semicolon if present
                    key, value = content.split(':', 1)
                    stored_data[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error reading or parsing _passwords file: {e}", file=sys.stderr)
        return {}
    return stored_data

def verify_password(username_input, password_input):
    """
    Verifies a user's plain-text password against the stored hashed password.
    This now uses Python's 'passlib' library for proper salt handling and verification.
    """
    curr_dir = Path(__file__).resolve().parent
    passwords_file_path = curr_dir / "_system" / "_passwords"

    stored_passwords = get_stored_passwords(passwords_file_path)

    if username_input not in stored_passwords:
        print(f"User '{username_input}' not found.")
        return False

    stored_hash = stored_passwords[username_input]

    try:
        # Use passlib's sha512_crypt.verify method
        # This handles the salt extraction and comparison internally.
        if sha512_crypt.verify(password_input, stored_hash):
            return True
        else:
            return False
    except Exception as e:
        print(f"An unexpected error occurred during password verification with passlib: {e}", file=sys.stderr)
        return False

# ANSI color codes
COLOR_BLUE = "\033[94m"    # Directories
COLOR_GREEN = "\033[92m"   # Executables
COLOR_RESET = "\033[0m"    # Reset to default

def list_content_colored(path="."):
    """
    Lists directories first, then files, with colors.
    - Directories are blue.
    - Executable files are green.
    - Other files are default color.
    """
    target_path = Path(path)

    if not target_path.exists():
        print(f"Error: '{path}' does not exist.")
        return
    if not target_path.is_dir():
        print(f"Error: '{path}' is not a directory.")
        return

    directories = []
    files = []

    for item in target_path.iterdir():
        if item.is_dir():
            directories.append(item)
        else:
            files.append(item)

    # Sort alphabetically
    directories.sort()
    files.sort()

    # Print directories in blue
    for d in directories:
        print(f"{COLOR_BLUE}{d.name}{COLOR_RESET}/") # Add / for directories

    # Print files with appropriate color
    for f in files:
        if f.is_file():
            if os.access(f, os.X_OK): # Check if executable
                print(f"{COLOR_GREEN}{f.name}{COLOR_RESET}")
            else:
                print(f"{f.name}")
        # Handle other types if necessary (e.g., symlinks, though not explicitly requested)

def change_directory(path):
    """
    Changes the current working directory of the PyOS.
    """
    try:
        os.chdir(path)
        print(f"Changed directory to: {os.getcwd()}")
    except FileNotFoundError:
        print(f"Error: Directory '{path}' not found.")
    except NotADirectoryError:
        print(f"Error: '{path}' is not a directory.")
    except Exception as e:
        print(f"An unexpected error occurred while changing directory: {e}", file=sys.stderr)

# --- New File and Directory Operations ---

def read_file(filepath):
    """
    Reads and prints the content of a file.
    """
    target_path = Path(filepath)
    try:
        if not target_path.exists():
            print(f"Error: File '{filepath}' not found.")
            return
        if target_path.is_dir():
            print(f"Error: '{filepath}' is a directory, not a file.")
            return
        
        content = target_path.read_text()
        print(content)
    except PermissionError:
        print(f"Error: Permission denied to read '{filepath}'.")
    except Exception as e:
        print(f"An unexpected error occurred while reading '{filepath}': {e}", file=sys.stderr)

def make_file(filepath, content=""):
    """
    Creates a new file with optional content.
    """
    target_path = Path(filepath)
    try:
        if target_path.exists():
            print(f"Error: File '{filepath}' already exists. Use a different name or 'rmfile' first.")
            return
        
        # Ensure parent directories exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        target_path.write_text(content)
        print(f"File '{filepath}' created.")
    except PermissionError:
        print(f"Error: Permission denied to create '{filepath}'.")
    except Exception as e:
        print(f"An unexpected error occurred while creating '{filepath}': {e}", file=sys.stderr)

def remove_file(filepath):
    """
    Deletes a specified file.
    """
    target_path = Path(filepath)
    try:
        if not target_path.exists():
            print(f"Error: File '{filepath}' not found.")
            return
        if target_path.is_dir():
            print(f"Error: '{filepath}' is a directory. Use 'rmdir' instead.")
            return
        
        target_path.unlink() # Deletes the file
        print(f"File '{filepath}' deleted.")
    except PermissionError:
        print(f"Error: Permission denied to delete '{filepath}'.")
    except Exception as e:
        print(f"An unexpected error occurred while deleting '{filepath}': {e}", file=sys.stderr)

def make_directory(dirpath):
    """
    Creates a new directory.
    """
    target_path = Path(dirpath)
    try:
        target_path.mkdir(parents=True, exist_ok=True) # Creates dir and any necessary parents
        print(f"Directory '{dirpath}' created.")
    except PermissionError:
        print(f"Error: Permission denied to create directory '{dirpath}'.")
    except FileExistsError: # Should be caught by exist_ok=True, but good for explicit check
        print(f"Error: Directory '{dirpath}' already exists.")
    except Exception as e:
        print(f"An unexpected error occurred while creating directory '{dirpath}': {e}", file=sys.stderr)

def remove_directory(dirpath):
    """
    Deletes an empty directory.
    """
    target_path = Path(dirpath)
    try:
        if not target_path.exists():
            print(f"Error: Directory '{dirpath}' not found.")
            return
        if not target_path.is_dir():
            print(f"Error: '{dirpath}' is a file. Use 'rmfile' instead.")
            return
        
        target_path.rmdir() # Deletes only if empty
        print(f"Directory '{dirpath}' deleted.")
    except OSError as e: # Catches errors like Directory not empty
        if "Directory not empty" in str(e):
            print(f"Error: Directory '{dirpath}' is not empty. Cannot delete with 'rmdir'.")
        else:
            print(f"An OS error occurred while deleting directory '{dirpath}': {e}", file=sys.stderr)
    except PermissionError:
        print(f"Error: Permission denied to delete directory '{dirpath}'.")
    except Exception as e:
        print(f"An unexpected error occurred while deleting directory '{dirpath}': {e}", file=sys.stderr)

# --- End New File and Directory Operations ---

# --- Global dictionary to store shell variables ---
_shell_variables = {}

def expand_variables(input_string):
    """
    Replaces @(varname) with actual variable values from _shell_variables.
    If a variable is not found, it's replaced with an empty string and a warning is printed.
    """
    def replace_var(match):
        var_name = match.group(1) # The content inside the parentheses
        if var_name in _shell_variables:
            return _shell_variables[var_name]
        else:
            print(f"Warning: Variable '{var_name}' not found. Replacing with empty string.", file=sys.stderr)
            return "" # Replace with empty string if variable is not defined
    
    # Use re.sub to find all @(varname) patterns and replace them
    # \w+ matches one or more word characters (alphanumeric + underscore)
    return re.sub(r'@\((\w+)\)', replace_var, input_string)


def emulate(promptline):
    # --- Pre-process the input for variable expansion ---
    processed_promptline = expand_variables(promptline)
    
    tokens = shlex.split(processed_promptline)
    if not tokens:
        return
    command = tokens[0]
    args = tokens[1:]

    # Example usage of verify_password within your emulate function or a login loop
    if command == "login":
        if len(args) == 2:
            user_to_login = args[0]
            pass_to_check = args[1]
            if verify_password(user_to_login, pass_to_check):
                print(f"Login successful for user: {user_to_login}")
                # Here you would set the current logged-in user session
            else:
                print("Login failed: Incorrect username or password.")
        else:
            print("Usage: login <username> <password>")
    # --- 'let' command for variable assignment ---
    elif command == "let":
        if len(args) == 1 and "=" in args[0]:
            var_assignment = args[0].split('=', 1) # Split only on the first '='
            var_name = var_assignment[0].strip()
            var_value = var_assignment[1].strip()
            _shell_variables[var_name] = var_value
            print(f"Variable '{var_name}' set to '{var_value}'")
        else:
            print("Usage: let <varname>=<value>")
    # --- 'vars' command to show current variables ---
    elif command == "vars":
        if _shell_variables:
            print("Current shell variables:")
            for var, val in _shell_variables.items():
                print(f"  {var}='{val}'")
        else:
            print("No shell variables currently set.")
    # --- Existing Commands ---
    elif command == "lc": # New 'lc' command
        if len(args) == 0:
            list_content_colored(os.getcwd()) # List current directory
        elif len(args) == 1:
            list_content_colored(args[0]) # List specified directory
        else:
            print("Usage: lc [directory]")
    elif command == "cd": # New 'cd' command
        if len(args) == 1:
            change_directory(args[0])
        else:
            print("Usage: cd <directory>")
    elif command == "about": # New 'about' command with updated message
        print("PyOS V1.1")
        print("Copyright (C) 2025 Muser") # Using your provided copyright info
        print("This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.")
        print("This is free software, and you are welcome to redistribute it")
        print("under certain conditions; type `show c' for details.")
    elif command == "show": # New 'show' command to handle 'c' and 'w'
        if len(args) == 1:
            subcommand = args[0]
            if subcommand == "c":
                print("PyOS is free software: you can redistribute it and/or modify")
                print("it under the terms of the GNU General Public License as published by")
                print("the Free Software Foundation, either version 3 of the License, or")
                print("(at your option) any later version.")
                print("")
                print("You should have received a copy of the GNU General Public License")
                print("along with this program. If not, see <https://www.gnu.org/licenses/>.")
            elif subcommand == "w":
                # Full warranty disclaimer as provided
                print("IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.")
            else:
                print("Usage: show <c|w>")
        else:
            print("Usage: show <c|w>")
    # --- File and Directory Commands ---
    elif command == "readfile":
        if len(args) == 1:
            read_file(args[0])
        else:
            print("Usage: readfile <filepath>")
    elif command == "mkfile":
        if len(args) == 1:
            make_file(args[0]) # Create empty file
        elif len(args) == 2:
            make_file(args[0], args[1]) # Create file with content
        else:
            print("Usage: mkfile <filepath> [content]")
    elif command == "rmfile":
        if len(args) == 1:
            remove_file(args[0])
        else:
            print("Usage: rmfile <filepath>")
    elif command == "mkdir":
        if len(args) == 1:
            make_directory(args[0])
        else:
            print("Usage: mkdir <directory_path>")
    elif command == "echo":
        if args and args[0] == "-e": # Added 'args and' for robustness against empty 'args'
            myargs = args[1:]
            newargs = []
            for arg in myargs:
                arg = arg.replace("\\e", "\033")
                arg = arg.replace("\\n", "\n")
                arg = arg.replace("\\t", "\t") 
                arg = arg.replace("\\r", "\r") 
                arg = arg.replace("\\\\", "\\")
                newargs.append(arg)
            print(" ".join(newargs))
        else:
            print(" ".join(args))
    elif command == "rmdir":
        if len(args) == 1:
            remove_directory(args[0])
        else:
            print("Usage: rmdir <directory_path>")
    # --- End File and Directory Commands ---
    elif command == "gum": # Command for gum package manager
        if len(args) == 1:
            if checkforpackagemanager() == 1:
                print("Gum not properly installed.")
            else:
                gum.installpkg(args[0])
        else:
            print("Usage: gum <package_url>")
    elif command == "pwd":
        print(os.getcwd())
    # --- Check for package commands before 'Unknown command' ---
    elif command in _package_commands:
        _package_commands[command](args) # Call the registered package handler
    # --- End NEW package command check ---
    else: # This 'else' block will now only be reached if it's NOT an internal or package command
        print(f"Unknown command: {command}")

# Example of how you might use it in a main loop
if __name__ == "__main__":
    if not checkforbuild():
        print("PyOS is not built. Please run build.sh first.")
        sys.exit(1)

    print("PyOS is built. You can now use internal commands like 'login', 'lc', 'cd', 'about', 'show', 'readfile', 'mkfile', 'rmfile', 'mkdir', 'rmdir', 'gum', 'let', 'vars'.") # Updated help message
    print("Commands from installed packages are also available.") # Optional message
    while True:
        try:
            # Updated prompt line to include current working directory
            user_input = input(f"PyOS: {getpass.getuser()}@{socket.gethostname()} {os.getcwd()} $ ").strip()
            if user_input.lower() == "exit":
                break
            emulate(user_input)
        except EOFError: # Handle Ctrl+D
            break
        except KeyboardInterrupt: # Handle Ctrl+C
            print("\nExiting PyOS.") # Nicer exit message
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)

