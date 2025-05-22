# PyOS:
## Description:

An "operating system" on Python. To use it, you must use `build.sh`, which automatically starts whenever installer is running.

For now, only compatible for Debian-based Linux distributions, we will add soon compatibility for other distributions. PS: Don't use Windows build (`build.bat`), as it is out of date and does not build system fully.
## How to build system manually?
### 0. Manual Download and Build (Alternative for Linux)

If you prefer to manually handle the download and extraction, follow these steps:

1. Download the PyOS archive:

```bash
wget https://github.com/Upload-and-View/PyOS/releases/download/first-release/os.tar.xz -O os.tar.xz
```
This command downloads the os.tar.xz file and saves it with the specified name in your current directory.
2. Extract the archive:

```bash
tar -xJf os.tar.xz
```
This command extracts the contents of the .tar.xz file. The -x flag is for extract, -J for XZ compression, and -f to specify the file.

3. Navigate into the extracted directory:
```bash
cd os
```
4. Make the build.sh script executable:
```bash
chmod +x build.sh
```
5. Run the build script:
```bash
./build.sh
```
This will execute the main build process for PyOS. 
  
If you are on Windows, or on other distribution of Linux which is not based off Ubuntu, you might use this method:
### 1. Build main stuff.

Create these folders where the system is installed:

*    `_packages`

*    `_system`

*    `_home`

Go to _home and make your a folder with name of your user you want to have, for example, I would use an user "gg".

Now create inside of it these folders:

*    `Downloads`

*    `Documents`

Now go back to _home and create a folder named "root".

Now create inside of it these folders:

*    `Downloads`

*    `Documents`

### 2. Build stuff that really needs to be in your system.

Before you continue, make sure `openssl` tool is installed or try to use online SHA-512 encoder.

For Ubuntu/Debian:
```bash
sudo apt update && sudo apt upgrade && sudo apt install openssl
```
For Arch Linux and Manjaro:
```bash
sudo pacman -Syu && sudo pacman -S openssl
```
For Fedora/RHEL/CentOS:
```bash
sudo dnf install openssl
```
For openSUSE:
```bash
sudo zypper refresh && sudo zypper install openssl
```
For Windows:

1. Download chocolatey [https://chocolatey.org/install](https://chocolatey.org/install)
    
2. Use this command AS ADMINISTRATOR:
```batchfile
choco install openssl
```
For macOS:

1. Install Homebrew (if you don't have it):
```bash
/bin/bash -c "$(curl -fsSL [https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh](https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh))"
```

2. Install openssl:

```bash
brew install openssl
```
Also, ensure the '`passlib`' Python library is installed:

For Ubuntu/Debian:
```bash
sudo apt install python3-passlib
```
For Arch Linux and Manjaro:
```bash
sudo pacman -S python-passlib
```
For Fedora/RHEL/CentOS:
```bash
sudo dnf install python3-passlib
```
For openSUSE:
```bash
sudo zypper refresh && sudo zypper install python3-passlib
```
For Windows:
```batchfile
pip install passlib
```
(Ensure Python and pip are installed and in PATH)

For macOS:
```bash
pip install passlib
```
(Ensure Python and pip are installed and in PATH, consider using 'pip3' if you have multiple Python versions or a virtual environment)

Go back to root directory where system is installed
Now go to _system
Make a file named _passwords
Edit it so it would look like this:
```json
{
"yourusername":"yourpasswordhash",
}
```
Where yourusername is your user name, and yourpasswordhash is hash of password you got using this command:
```bash
print($(openssl passwd -6 "$yourpasswordhere")
```
Where yourpasswordhere is your password you want to add to user.

Now, make a file named _administrators, make so it would look like this:
```json
{
    "yourusername": "defaultuser",
    "root": "administrator"
}
```
You can change `defaultuser` to `administrator` or vice versa, just leave on root account `administrator`.

Done!
### 3. Build stuff that you probably will not need.

Go to root directory, and then to `_packages` directory.

Make in `_packages` directory "`gum`" directory (a package manager)

Go to "`gum`" folder, and make `__init__.py`

Edit the `__init__.py` so it would look like this:
```python
import requests
import tarfile
import os

def installpkg(pkglink):
    print(f"Downloading package from: {pkglink}")
    try:
        response = requests.get(pkglink, stream=True)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        # Determine package name from URL or make a temp file
        # For simplicity, let's assume pkglink ends with /package.tar.gz
        temp_file_name = pkglink.split('/')[-1]
        if not temp_file_name.endswith('.tar.gz'):
            temp_file_name = "temp_package.tar.gz" # Fallback if URL doesn't suggest name

        with open(temp_file_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded '{temp_file_name}'. Extracting...")

        with tarfile.open(temp_file_name, "r:gz") as tar:
            # Assume description.txt is at the root of the tar file
            pkg_name = "unknown_package"
            try:
                desc_file = tar.extractfile('desc.txt')
                if desc_file:
                    desc_content = desc_file.read().decode('utf-8')
                    # Parse desc_content for package name (e.g., "Name: MyPackage")
                    for line in desc_content.splitlines():
                        if line.startswith("Name:"):
                            pkg_name = line.split(":", 1)[1].strip()
                            break
            except KeyError:
                print("Warning: desc.txt not found in package. Using default name.")

            pkg_install_path = os.path.join(os.getcwd(), pkg_name) # Install in current dir for now
            os.makedirs(pkg_install_path, exist_ok=True)
            tar.extractall(path=pkg_install_path)
            print(f"Package '{pkg_name}' extracted to '{pkg_install_path}'")

            # Check for pkg.py and make it __init__.py
            pkg_py_path_in_tar = os.path.join(pkg_name, 'pkg.py') # Assumes pkg.py is inside pkg_name folder
            pkg_py_path_after_extract = os.path.join(pkg_install_path, 'pkg.py')
            init_py_path = os.path.join(pkg_install_path, '__init__.py')

            if os.path.exists(pkg_py_path_after_extract):
                print(f"Renaming pkg.py to __init__.py in {pkg_install_path}")
                os.rename(pkg_py_path_after_extract, init_py_path)
            else:
                print("Warning: pkg.py not found in extracted package.")

        os.remove(temp_file_name) # Clean up the downloaded tar.gz
        print(f"Installation of '{pkg_name}' complete.")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading package: {e}")
    except tarfile.ReadError as e:
        print(f"Error extracting package: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during installation: {e}")
```
### 4. Build other needed things.

Go to root directory, and make a file named __init__.py

Make so it would look like this:

```python
#!/usr/bin/env python3
#    PyOS, an "operating system" running on Python.
#    Copyright (C) 2025  Muser
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
from passlib.hash import sha512_crypt # Added: Modern password hashing/verification library

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

# Add the _packages directory to sys.path so gum can be imported
curr_dir = Path(__file__).resolve().parent
packages_dir = curr_dir / "_packages"
if str(packages_dir) not in sys.path:
    sys.path.append(str(packages_dir))

# --- Package Manager Check and Import ---
# This function checks if the 'gum' package manager can be imported.
# It's defined here because it needs to be accessible before the main loop.
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
# This is done here so that `gum` is available for use in `emulate`
import gum 
# --- End Package Manager Check and Import ---


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
        # print(f"Debug: Build flag file not found at {build_flag_file}") # Optional debug print
        return False # File doesn't exist, so it's not built

    # If the file exists, try to read its content
    try:
        # Use the full path to open the file to avoid issues if the current working directory changes
        with open(build_flag_file, 'r') as f: # Open in read mode ('r')
            content = f.read().strip() # .strip() removes any leading/trailing whitespace (like newlines)
        
        # Check if the content is exactly "True"
        is_content_true = (content == "True")
        # print(f"Debug: File content '{content}' matches 'True': {is_content_true}") # Optional debug print
        
        # Return True only if the file exists AND its content is "True"
        return is_content_true

    except FileNotFoundError:
        # This case should ideally be caught by build_flag_file.is_file()
        # but is good practice for robustness in file operations.
        # print(f"Debug: File not found during open, despite is_file() check: {build_flag_file}") # Optional debug print
        return False
    except Exception as e:
        # Catch any other potential errors during file reading (e.g., permission issues)
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
    print(f"DEBUG: Checking password file at: {passwords_file_path}", file=sys.stderr) # DEBUG
    if not Path(passwords_file_path).is_file():
        print(f"DEBUG: Password file not found: {passwords_file_path}", file=sys.stderr) # DEBUG
        return stored_data # Return empty if file doesn't exist

    try:
        with open(passwords_file_path, 'r') as f:
            lines = f.readlines()
            for line in lines: # Iterate through lines normally
                line = line.strip()
                print(f"DEBUG: Reading line (for parsing): '{line}'", file=sys.stderr) # DEBUG
                # Look for lines that contain ':' and are not just '{' or '}'
                if ':' in line and not line.startswith('{') and not line.endswith('}'):
                    content = line.strip(';') # Remove trailing semicolon if present
                    print(f"DEBUG: Parsed content: '{content}'", file=sys.stderr) # DEBUG
                    key, value = content.split(':', 1)
                    stored_data[key.strip()] = value.strip()
                    print(f"DEBUG: Added to stored_data: '{key.strip()}': '{value.strip()}'", file=sys.stderr) # DEBUG
    except Exception as e:
        print(f"Error reading or parsing _passwords file: {e}", file=sys.stderr)
        return {}
    print(f"DEBUG: Final stored_data: {stored_data}", file=sys.stderr) # DEBUG
    return stored_data

# Removed hash_password_for_comparison as it's no longer needed for verification in Python

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
    print(f"DEBUG: Stored hash for '{username_input}': '{stored_hash}'", file=sys.stderr) # DEBUG

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


def emulate(promptline):
    tokens = shlex.split(promptline)
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
        print("PyOS V1.0")
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
    elif command == "rmdir":
        if len(args) == 1:
            remove_directory(args[0])
        else:
            print("Usage: rmdir <directory_path>")
    # --- End File and Directory Commands ---
    elif command == "gum": # New command for gum package manager
        if len(args) == 1:
            if checkforpackagemanager() == 1:
                print("Gum not properly installed.")
            else:
                gum.installpkg(args[0])
        else:
            print("Usage: gum <package_url>")
    else:
        print(f"Unknown command: {command}")

# Example of how you might use it in a main loop
if __name__ == "__main__":
    if not checkforbuild():
        print("PyOS is not built. Please run build.sh first.")
        sys.exit(1)

    print("PyOS is built. You can now use commands like 'login', 'lc', 'cd', 'about', 'show', 'readfile', 'mkfile', 'rmfile', 'mkdir', 'rmdir', 'gum'.")
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
            break
        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)


```
Done! All steps done!
Credits:

Thanks to: Muser (me)  
Thanks to AI features for enhancing code.
