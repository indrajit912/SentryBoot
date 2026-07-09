import sys
import ctypes
from ctypes import wintypes
from typing import Callable

# Win32 Console Control Event Constants
CTRL_C_EVENT = 0
CTRL_BREAK_EVENT = 1
CTRL_CLOSE_EVENT = 2
CTRL_LOGOFF_EVENT = 5
CTRL_SHUTDOWN_EVENT = 6

# Define Win32 Handler Prototype: BOOL CALLBACK HandlerRoutine(DWORD dwCtrlType);
HandlerRoutineType = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)

# Prevent Python GC from garbage-collecting the callback reference
_handler_ref = None

def register_close_handler(on_close_callback: Callable[[int], None]) -> bool:
    """Registers a native Windows console control handler using ctypes.
    
    Triggers the callback when the console window is closed (X button, Alt+F4),
    when the user logs off, or when Windows shuts down.
    
    Returns:
        bool: True if handler was successfully registered, False otherwise.
    """
    if sys.platform != 'win32':
        return False
        
    global _handler_ref
    
    def win_handler(ctrl_type: int) -> bool:
        if ctrl_type in (CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT):
            # Execute the user-provided alert/log callback
            on_close_callback(ctrl_type)
            # Return False so that other handlers in the chain (and the default OS handler)
            # are executed, allowing the system to proceed with standard closure.
            return False
        return False
        
    try:
        _handler_ref = HandlerRoutineType(win_handler)
        
        SetConsoleCtrlHandler = ctypes.windll.kernel32.SetConsoleCtrlHandler
        SetConsoleCtrlHandler.argtypes = [HandlerRoutineType, wintypes.BOOL]
        SetConsoleCtrlHandler.restype = wintypes.BOOL
        
        success = SetConsoleCtrlHandler(_handler_ref, True)
        return bool(success)
    except Exception:
        return False
