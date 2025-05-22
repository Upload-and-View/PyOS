# PyOS:
## Description:

An "operating system" on Python. To use it, you must use `build.sh`, which automatically starts whenever installer is running.

For now, only compatible for Debian-based Linux distributions, we will add soon compatibility for other distributions. PS: Don't use Windows build (`build.bat`), as it is out of date and does not build system fully.
## How to build system manually?

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
Done! All steps done!
Credits:

Thanks to: Muser (me)  
Thanks to AI features for enhancing code.
