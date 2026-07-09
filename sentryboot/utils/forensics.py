import sys
import subprocess
from typing import Dict

def get_process_snapshot() -> str:
    """Gathers a snapshot of running processes using native OS command-line tools."""
    try:
        if sys.platform == 'win32':
            # Run tasklist on Windows
            output = subprocess.check_output(["tasklist"], shell=True, stderr=subprocess.DEVNULL)
        else:
            # Run ps on Linux/macOS
            output = subprocess.check_output(["ps", "aux"], stderr=subprocess.DEVNULL)
        return output.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Failed to gather process snapshot: {str(e)}"

def get_network_snapshot() -> str:
    """Gathers active network connections using native OS tools."""
    try:
        if sys.platform == 'win32':
            # Run netstat on Windows
            output = subprocess.check_output(["netstat", "-ano"], shell=True, stderr=subprocess.DEVNULL)
        else:
            # Run netstat on Linux/macOS
            output = subprocess.check_output(["netstat", "-an"], stderr=subprocess.DEVNULL)
        return output.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Failed to gather network snapshot: {str(e)}"

def gather_forensics() -> Dict[str, str]:
    """Aggregates process list and network connections for attachment formatting."""
    return {
        "processes.txt": get_process_snapshot(),
        "network_connections.txt": get_network_snapshot()
    }
