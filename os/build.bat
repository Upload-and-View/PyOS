@echo off
REM build.bat - Enhanced build script for PyOS (Batch version) - Modified for local directory

REM --- Global Settings and Error Handling ---
REM Set current directory to the location of the batch file
pushd "%~dp0"
if %errorlevel% neq 0 (
    echo ERROR: Could not change to script directory.
    exit /b 1
)

REM Exit immediately if a command exits with a non-zero status.  (Less robust than Bash's set -e)
REM Treat unset variables as an error when substituting. (Not directly equivalent in Batch)

REM Function to display error messages and exit
:error_exit
    echo ERROR: %~1
    pause
    popd
    exit /b 1

REM --- Build Flag ---
REM Create _isbuilded file in the script's directory
echo Creating _isbuilded file...
type nul > _isbuilded || call :error_exit "Failed to create _isbuilded file."
echo True > _isbuilded || call :error_exit "Failed to write to _isbuilded file."

REM --- Directory Setup ---
echo Creating core directories...
REM Create directories relative to the script's directory
if not exist "_packages" md "_packages" || call :error_exit "Failed to create _packages directory."
if not exist "_system" md "_system" || call :error_exit "Failed to create _system directory."
if not exist "_home" md "_home" || call :error_exit "Failed to create _home directory."

REM --- Home Build Section ---
echo --- Home Build ---
cd "_home" || call :error_exit "Failed to change to _home directory."

REM Function to create user folders (Batch subroutine)
:makefolderuser
    if "%~1"=="" (
        echo Syntax error: makefolderuser requires 1 argument, but none were given.
        exit /b 1
    )
    set "user_dir_name=%~1"
    
    echo Creating home directory for user: '%user_dir_name%'...
    if not exist "%user_dir_name%" md "%user_dir_name%" || (echo Failed to create directory for %user_dir_name% && exit /b 1)
    
    REM Change into the user's directory to create subdirectories
    cd "%user_dir_name%" || (echo Failed to change to %user_dir_name% directory. && exit /b 1)
    
    if not exist "Downloads" md "Downloads" || (echo Failed to create Downloads for %user_dir_name% && exit /b 1)
    if not exist "Documents" md "Documents" || (echo Failed to create Documents for %user_dir_name% && exit /b 1)
    
    REM Go back to _home directory
    cd .. || call :error_exit "Failed to change back from user directory."
    
    exit /b 0

REM Prompt for username and validate input
set "username="
:get_username_loop
    set /p "username=Please, choose an username (cannot be empty): "
    if "%username%"=="" (
        echo Username cannot be empty. Please try again.
        goto :get_username_loop
    )
goto :end_get_username_loop
:end_get_username_loop

REM Call the subroutine to create user's home folder
call :makefolderuser "%username%"
if %ERRORLEVEL% NEQ 0 (
    call :error_exit "Unexpected error occurred while building user '%username%' home directory."
)

REM Create root's home folder (adjust if root's home is typically at C:\root for your PyOS concept)
call :makefolderuser "root"
if %ERRORLEVEL% NEQ 0 (
    call :error_exit "Unexpected error occurred while building 'root' home directory."
)

REM Go back to base directory
cd "%~dp0" || call :error_exit "Failed to change back to base directory."

REM --- System Build - Password Management ---
echo --- System Build - Password Management ---
cd "_system" || call :error_exit "Failed to change to _system directory."

REM WARNING: Storing passwords in plain text like this (_passwords file) is HIGHLY INSECURE.
REM In a real operating system, passwords are hashed and salted.
REM This script proceeds with your requested method, but be aware of the security implications.
type nul > _passwords || call :error_exit "Failed to create _passwords file."

REM Password prompt loop (Batch doesn't have silent input like 'read -s')
:password_prompt_loop
    set "password_var="
    set "r_password_var="
    set /p "password_var=Enter a password for user '%username%': "
    echo.
    set /p "r_password_var=Retype password: "
    echo.

    if not "%password_var%"=="%r_password_var%" (
        echo Passwords do not match. Please try again.
        goto :password_prompt_loop
    )
    REM Assign to the global 'password' variable
    set "password_final=%password_var%"
goto :end_password_prompt_loop

REM Write username and password to _passwords file
REM Using your requested format, but again, be mindful of plain text passwords.
echo { >> _passwords || call :error_exit "Failed to write to _passwords file."
echo %username%:%password_final%; >> _passwords || call :error_exit "Failed to write to _passwords file."
echo } >> _passwords || call :error_exit "Failed to write to _passwords file."

type nul > _packagesinstalled || call :error_exit "Failed to create _packagesinstalled file."

REM Go back to base directory
cd "%~dp0" || call :error_exit "Failed to change back to base directory."

REM --- Packages Build - Gum Package Manager ---
echo --- Packages Build - Gum Package Manager ---
cd "_packages" || call :error_exit "Failed to change to _packages directory."

if not exist "gum" md "gum" || call :error_exit "Failed to create gum directory."
cd "gum" || call :error_exit "Failed to change to gum directory."

REM Correcting the Python __init__.py filename
type nul > "__init__.py" || call :error_exit "Failed to create __init__.py for gum."

REM Multi-line Python code using ECHO commands
(
echo import requests
echo import tarfile
echo import os
echo.
echo def installpkg(pkglink):
echo     print(f"Downloading package from: {pkglink}")
echo     try:
echo         response = requests.get(pkglink, stream=True)
echo         response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
echo.
echo         # Determine package name from URL or make a temp file
echo         # For simplicity, let's assume pkglink ends with /package.tar.gz
echo         temp_file_name = pkglink.split('/')[-1]
echo         if not temp_file_name.endswith('.tar.gz'):
echo              temp_file_name = "temp_package.tar.gz" # Fallback if URL doesn't suggest name
echo.
echo         with open(temp_file_name, 'wb') as f:
echo             for chunk in response.iter_content(chunk_size=8192):
echo                 f.write(chunk)
echo.
echo         print(f"Downloaded '{temp_file_name}'. Extracting...")
echo.
echo         with tarfile.open(temp_file_name, "r:gz") as tar:
echo             # Assume description.txt is at the root of the tar file
echo             pkg_name = "unknown_package"
echo             try:
echo                 desc_file = tar.extractfile('desc.txt')
echo                 if desc_file:
echo                     desc_content = desc_file.read().decode('utf-8')
echo                     # Parse desc_content for package name (e.g., "Name: MyPackage")
echo                     for line in desc_content.splitlines():
echo                         if line.startswith("Name:"):
echo                             pkg_name = line.split(":", 1)[1].strip()
echo                             break
echo             except KeyError:
echo                 print("Warning: desc.txt not found in package. Using default name.")
echo.
echo             pkg_install_path = os.path.join(os.getcwd(), pkg_name) # Install in current dir for now
echo             os.makedirs(pkg_install_path, exist_ok=True)
echo             tar.extractall(path=pkg_install_path)
echo             print(f"Package '{pkg_name}' extracted to '{pkg_install_path}'")
echo.
echo             # Check for pkg.py and make it __init__.py
echo             pkg_py_path_in_tar = os.path.join(pkg_name, 'pkg.py') # Assumes pkg.py is inside pkg_name folder
echo             pkg_py_path_after_extract = os.path.join(pkg_install_path, 'pkg.py')
echo             init_py_path = os.path.join(pkg_install_path, '__init__.py')
echo.
echo             if os.path.exists(pkg_py_path_after_extract):
echo                 print(f"Renaming pkg.py to __init__.py in {pkg_install_path}")
echo                 os.rename(pkg_py_path_after_extract, init_py_path)
echo             else:
echo                 print("Warning: pkg.py not found in extracted package.")
echo.
echo         os.remove(temp_file_name) # Clean up the downloaded tar.gz
echo         print(f"Installation of '{pkg_name}' complete.")
echo.
echo     except requests.exceptions.RequestException as e:
echo         print(f"Error downloading package: {e}")
echo     except tarfile.ReadError as e:
echo         print(f"Error extracting package: {e}")
echo     except Exception as e:
echo         print(f"An unexpected error occurred during installation: {e}")
echo.
echo # Example usage (for testing, you'd call installpkg from your PyOS)
echo # if __name__ == "__main__":
echo #     # This would be a URL to a .tar.gz package
echo #     example_package_url = "http://example.com/some_package.tar.gz"
echo #     # installpkg(example_package_url)
) > "__init__.py"

REM Go back to the original directory
popd
echo --- All tasks completed successfully! ---
pause
exit /b 0
