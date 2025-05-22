#!/bin/bash
# build.sh - Enhanced build script for PyOS

# --- Global Settings and Error Handling ---
# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Enable extended pattern matching features (useful for some advanced checks).
shopt -s extglob

# Define base directory (where build.sh is located)
readonly BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to display error messages and exit
error_exit() {
    local message="$1"
    echo "ERROR: ${message}" >&2 # Output to stderr
    read -p "Press Enter to continue..."
    exit 1
}

# --- Build Flag ---
# Using touch for _isbuilded is fine, but if it's meant as a boolean flag
# just checking for the file's existence (e.g., `[ -f _isbuilded ]`) would work.
# For now, sticking to your intent to write "True" into it.
touch "${BASE_DIR}/_isbuilded" || error_exit "Failed to create _isbuilded file."
echo "True" > "${BASE_DIR}/_isbuilded" || error_exit "Failed to write to _isbuilded file."

# --- Check and Install OpenSSL ---
echo "Checking for openssl..."
if ! command -v openssl &> /dev/null
then
    echo "openssl not found. Installing openssl..."
    echo "Running system update and upgrade first..."
    sudo apt update || error_exit "Failed to run apt update."
    sudo apt upgrade -y || error_exit "Failed to run apt upgrade."
    sudo apt install -y openssl || error_exit "Failed to install openssl. Please ensure you have internet access and correct repository setup."
    echo "openssl installed successfully."
else
    echo "openssl is already installed."
fi

# --- Check and Install Python 'passlib' library ---
echo "Checking for Python 'passlib' library..."
# Check if passlib can be imported by Python
if ! python3 -c "import passlib.hash" &> /dev/null
then
    echo "'passlib' Python library not found. Installing python3-passlib..."
    echo "Running system update and upgrade first (if not already done)..."
    sudo apt update || error_exit "Failed to run apt update for passlib."
    sudo apt upgrade -y || error_exit "Failed to run apt upgrade for passlib."
    sudo apt install -y python3-passlib || error_exit "Failed to install python3-passlib. Please ensure you have internet access and correct repository setup."
    echo "'passlib' installed successfully."
else
    echo "'passlib' Python library is already installed."
fi


# --- Directory Setup ---
echo "Creating core directories..."
mkdir -p "${BASE_DIR}/_packages" || error_exit "Failed to create _packages directory."
mkdir -p "${BASE_DIR}/_system" || error_exit "Failed to create _system directory."
mkdir -p "${BASE_DIR}/_home" || error_exit "Failed to create _home directory."

# --- Home Build Section ---
echo "--- Home Build ---"
cd "${BASE_DIR}/_home" || error_exit "Failed to change to _home directory."

# Function to create user folders
makefolderuser () {
    if [ "$#" -ne 1 ]; then
        echo "Syntax error: makefolderuser requires 1 argument, but '$#' were given."
        return 1
    fi
    local user_dir_name="$1"
    
    echo "Creating home directory for user: '${user_dir_name}'..."
    mkdir -p "${user_dir_name}" || { echo "Failed to create directory for ${user_dir_name}"; return 1; }
    
    # Change into the user's directory to create subdirectories
    cd "${user_dir_name}" || { echo "Failed to change to ${user_dir_name} directory."; return 1; }
    
    mkdir -p "Downloads" || { echo "Failed to create Downloads for ${user_dir_name}"; return 1; }
    mkdir -p "Documents" || { echo "Failed to create Documents for ${user_dir_name}"; return 1; }
    
    # Go back to _home directory
    cd .. || error_exit "Failed to change back from user directory."
    
    return 0
}

# Prompt for username and validate input
username=""
while [ -z "$username" ]; do
    read -p "Please, choose an username (cannot be empty): " username
    if [ -z "$username" ]; then
        echo "Username cannot be empty. Please try again."
    fi
done

# Create user's home folder
makefolderuser "${username}"
if [ "$?" -ne 0 ]; then
    error_exit "Unexpected error occurred while building user '${username}' home directory."
fi

# Create root's home folder (adjust if root's home is typically at /root in your PyOS)
makefolderuser "root"
if [ "$?" -ne 0 ]; then
    error_exit "Unexpected error occurred while building 'root' home directory."
fi

# Go back to base directory
cd "${BASE_DIR}" || error_exit "Failed to change back to base directory."

# --- System Build - Password Management ---
echo "--- System Build - Password Management ---"
cd "${BASE_DIR}/_system" || error_exit "Failed to change to _system directory."

# WARNING: Storing passwords in plain text like this (_passwords file) is HIGHLY INSECURE.
# In a real operating system, passwords are hashed and salted.
# This script proceeds with your requested method, but be aware of the security implications.
touch _passwords || error_exit "Failed to create _passwords file."

password_prompt_loop () {
    local password_matched=false
    while [ "$password_matched" = false ]; do
        read -s -p "Enter a password for user '${username}': " password_var
        echo
        read -s -p "Retype password: " r_password_var
        echo

        if [[ "$password_var" == "$r_password_var" ]]; then
            password_matched=true
            # Hash the password using openssl passwd -6 (SHA512)
            # This is a significant security improvement over plain text.
            # In a real OS, you'd typically use crypt() with a randomly generated salt.
            # Ensure 'openssl' is available on the system where this script runs.
            password=$(openssl passwd -6 "${password_var}")
        else
            echo "Passwords do not match. Please try again."
        fi
    done
}

password_prompt_loop

# Write username and hashed password to _passwords file
# This now stores the SHA512 hash of the password.
printf "{\n%s:%s;\n}\n" "${username}" "${password}" >> _passwords || error_exit "Failed to write password to _passwords file."

# --- New: Create _administrators file ---
echo "Creating _administrators file..."
# This printf command dynamically creates the JSON content for _administrators
# It correctly quotes the username variable's value as a JSON key.
printf '{\n    "%s": "defaultuser",\n    "root": "administrator"\n}\n' "${username}" > _administrators || error_exit "Failed to create _administrators file."

touch _packagesinstalled || error_exit "Failed to create _packagesinstalled file."

# Go back to base directory
cd "${BASE_DIR}" || error_exit "Failed to change back to base directory."

# --- Packages Build - Gum Package Manager ---
echo "--- Packages Build - Gum Package Manager ---"
cd "${BASE_DIR}/_packages" || error_exit "Failed to change to _packages directory."

mkdir -p "gum" || error_exit "Failed to create gum directory."
cd "gum" || error_exit "Failed to change to gum directory."

# Correcting the Python __init__.py filename
touch "__init__.py" || error_exit "Failed to create __init__.py for gum."

# Using a here document for cleaner multi-line Python code
cat << 'PYTHON_INIT' > "__init__.py"
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

# Example usage (for testing, you'd call installpkg from your PyOS)
# if __name__ == "__main__":
#     # This would be a URL to a .tar.gz package
#     # example_package_url = "http://example.com/some_package.tar.gz" 
#     # installpkg(example_package_url)
PYTHON_INIT
# Note the 'PYTHON_INIT' in quotes above to prevent shell variable expansion inside the Python code

# Go back to base directory
cd "${BASE_DIR}" || error_exit "Failed to change back to base directory."

echo "--- All tasks completed successfully! ---"
read -p "Press Enter to continue..."
exit 0 # Indicate successful execution

