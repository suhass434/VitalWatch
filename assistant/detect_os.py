# filename: detect_os.py

import platform

try:
    import distro
except ImportError:
    distro = None

def get_os_distro() -> str:
    system = platform.system()

    if system == "Linux" and distro:
        return f"{distro.name()} {distro.version()}"
    elif system == "Linux":
        return "Linux (distro module not installed)"
    elif system == "Windows":
        return f"Windows {platform.release()}"
    elif system == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    else:
        return system

def main():
    os_info = get_os_distro()
    print(f"Detected OS: {os_info}")

if __name__ == "__main__":
    main()