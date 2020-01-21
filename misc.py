import os
import platform

from setuptools import sandbox



VIRTUAL_BOX_KEY = "SOFTWARE\Oracle\VirtualBox"
VIRTUAL_BOX_INSTALL_DIR_KEY = "SOFTWARE\Oracle\VirtualBox\InstallDir"


def get_virtual_box_key():
    import winreg
    return winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, VIRTUAL_BOX_KEY,
                          access=winreg.KEY_READ | winreg.KEY_WOW64_64KEY)


def check_virtual_box_installed():
    system = platform.system()
    if system == "Windows":
        try:
            with get_virtual_box_key():
                return True
        except FileNotFoundError:
            return False

    import shutil
    return bool(shutil.which("virtualbox"))

def get_virtual_box_installation_path():
    try:
        with get_virtual_box_key() as key:
            installation_path, _ = winreg.QueryValueEx(key, "InstallDir")
            return installation_path
    except FileNotFoundError:
        return None

def vboxapi_constant(type_name, attr_name):
    from vboxapi.VirtualBox_constants import VirtualBoxReflectionInfo

    vbox_constants = VirtualBoxReflectionInfo(None)
    types = vbox_constants.all_values(type_name)
    return types.get(attr_name)

def gb_to_byte_size(size):
    return size << 30
