import os
import socket
import ctypes
import requests
from datetime import datetime, timedelta
from typing import Dict, Any

def get_windows_username() -> str:
    """Retrieves the current logged-in Windows username."""
    # Attempt to read from environment or getuser
    username = os.environ.get("USERNAME") or os.environ.get("USER")
    if not username:
        try:
            import getpass
            username = getpass.getuser()
        except Exception:
            username = "Unknown"
    return username

def get_computer_name() -> str:
    """Retrieves the system computer name."""
    return socket.gethostname()

def get_local_ip() -> str:
    """Retrieves the local IP address."""
    try:
        # Create dummy socket to get the routing local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def get_public_ip() -> str:
    """Retrieves the public IP address with a short timeout."""
    try:
        response = requests.get("https://api.ipify.org", timeout=3.0)
        if response.status_code == 200:
            return response.text.strip()
    except Exception:
        pass
    return "Unavailable (Offline)"

def get_system_uptime() -> timedelta:
    """Retrieves system uptime using native Windows API."""
    try:
        # GetTickCount64 returns milliseconds since system boot
        millis = ctypes.windll.kernel32.GetTickCount64()
        return timedelta(milliseconds=millis)
    except Exception:
        return timedelta(0)

def get_system_diagnostics() -> Dict[str, Any]:
    """Aggregates all diagnostic data for system notification."""
    uptime = get_system_uptime()
    boot_time = datetime.now() - uptime
    
    return {
        "computer_name": get_computer_name(),
        "username": get_windows_username(),
        "local_ip": get_local_ip(),
        "public_ip": get_public_ip(),
        "uptime_str": str(uptime).split('.')[0],  # format as H:MM:SS
        "boot_time_str": boot_time.strftime("%b %d, %y %I:%M:%S %p"),
        "os_version": f"Windows ({socket.gethostname()})"
    }
