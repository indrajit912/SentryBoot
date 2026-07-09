import os
import sys
import json
import base64
import hashlib
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Dict, Any, Optional

# Win32 Constants for DPAPI
CRYPTPROTECT_UI_FORBIDDEN = 0x01

class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ('cbData', wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_byte))
    ]

def encrypt_dpapi(data: str) -> str:
    """Encrypts a string using Windows DPAPI and returns a base64 encoded string."""
    if sys.platform != 'win32':
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')
        
    try:
        data_bytes = data.encode('utf-8')
        data_in = DATA_BLOB(
            len(data_bytes), 
            ctypes.cast(ctypes.create_string_buffer(data_bytes), ctypes.POINTER(ctypes.c_byte))
        )
        data_out = DATA_BLOB()
        
        success = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(data_in),
            u"SentryBoot Secret",
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(data_out)
        )
        
        if not success:
            raise ctypes.WinError()
            
        out_size = data_out.cbData
        out_ptr = data_out.pbData
        out_bytes = bytes((ctypes.c_byte * out_size).from_address(ctypes.addressof(out_ptr.contents)))
        
        ctypes.windll.kernel32.LocalFree(out_ptr)
        return base64.b64encode(out_bytes).decode('utf-8')
    except Exception as e:
        # Fallback to simple base64 if DPAPI fails
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def decrypt_dpapi(encrypted_b64: str) -> str:
    """Decrypts a base64 encoded DPAPI-encrypted string."""
    if sys.platform != 'win32':
        return base64.b64decode(encrypted_b64).decode('utf-8')
        
    try:
        encrypted_bytes = base64.b64decode(encrypted_b64)
        data_in = DATA_BLOB(
            len(encrypted_bytes), 
            ctypes.cast(ctypes.create_string_buffer(encrypted_bytes), ctypes.POINTER(ctypes.c_byte))
        )
        data_out = DATA_BLOB()
        
        success = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(data_in),
            None,
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(data_out)
        )
        
        if not success:
            raise ctypes.WinError()
            
        out_size = data_out.cbData
        out_ptr = data_out.pbData
        out_bytes = bytes((ctypes.c_byte * out_size).from_address(ctypes.addressof(out_ptr.contents)))
        
        ctypes.windll.kernel32.LocalFree(out_ptr)
        return out_bytes.decode('utf-8')
    except Exception:
        # Fallback decryption
        try:
            return base64.b64decode(encrypted_b64).decode('utf-8')
        except Exception as e:
            raise ValueError("Failed to decrypt configuration values.") from e

def encrypt_secret(val: str) -> str:
    """Wrapper to encrypt a value with DPAPI and tag it."""
    if not val:
        return ""
    if sys.platform == 'win32':
        try:
            return f"dpapi:{encrypt_dpapi(val)}"
        except Exception:
            pass
    return f"plain:{base64.b64encode(val.encode('utf-8')).decode('utf-8')}"

def decrypt_secret(val: str) -> str:
    """Wrapper to decrypt tagged secrets."""
    if not val:
        return ""
    if val.startswith("dpapi:"):
        return decrypt_dpapi(val[6:])
    elif val.startswith("plain:"):
        return base64.b64decode(val[6:]).decode('utf-8')
    return val

def hash_passphrase(passphrase: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """Hashes the passphrase using PBKDF2-HMAC-SHA256. Returns (hash_hex, salt_hex)."""
    if salt is None:
        salt = os.urandom(16)
    iterations = 100000
    key = hashlib.pbkdf2_hmac('sha256', passphrase.encode('utf-8'), salt, iterations)
    return key.hex(), salt.hex()

def verify_passphrase(passphrase: str, hash_hex: str, salt_hex: str) -> bool:
    """Verifies a passphrase against the saved hash and salt."""
    try:
        salt = bytes.fromhex(salt_hex)
        iterations = 100000
        key = hashlib.pbkdf2_hmac('sha256', passphrase.encode('utf-8'), salt, iterations)
        return key.hex() == hash_hex
    except Exception:
        return False


class ConfigManager:
    """Manages the configuration storage and retrieval for SentryBoot."""
    
    CONFIG_DIR = Path.home() / ".sentryboot"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    def __init__(self):
        self.hermes_base_url: str = "https://hermesbot.pythonanywhere.com"
        self.hermes_api_key: Optional[str] = None
        self.hermes_emailbot_id: Optional[str] = None
        self.recipient_email: Optional[str] = None
        self.passphrase_hash: Optional[str] = None
        self.passphrase_salt: Optional[str] = None
        self.default_timeout_mins: int = 2
        
    def exists(self) -> bool:
        """Returns True if the config file exists."""
        return self.CONFIG_FILE.exists()
        
    def load(self) -> bool:
        """Loads configuration from file. Decrypts sensitive fields. Returns True if successful."""
        if not self.exists():
            return False
            
        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.hermes_base_url = data.get("hermes_base_url", "https://hermesbot.pythonanywhere.com")
            
            # Decrypt secret values
            enc_key = data.get("hermes_api_key")
            self.hermes_api_key = decrypt_secret(enc_key) if enc_key else None
            
            # Email bot ID is not strictly secret, but could be decrypted if we encrypted it
            enc_bot = data.get("hermes_emailbot_id")
            if enc_bot:
                self.hermes_emailbot_id = decrypt_secret(enc_bot) if enc_bot.startswith(("dpapi:", "plain:")) else enc_bot
            else:
                self.hermes_emailbot_id = None
                
            self.recipient_email = data.get("recipient_email")
            self.passphrase_hash = data.get("passphrase_hash")
            self.passphrase_salt = data.get("passphrase_salt")
            self.default_timeout_mins = int(data.get("default_timeout_mins", 2))
            return True
        except Exception:
            return False
            
    def save(self) -> None:
        """Encrypts sensitive fields and saves configuration to file."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Restrict directory access on Windows (ACLs) or unix permissions
        if sys.platform != 'win32':
            try:
                self.CONFIG_DIR.chmod(0o700)
            except Exception:
                pass
                
        # Encrypt the secrets before serializing
        enc_api_key = encrypt_secret(self.hermes_api_key) if self.hermes_api_key else ""
        enc_bot_id = encrypt_secret(self.hermes_emailbot_id) if self.hermes_emailbot_id else ""
        
        data = {
            "hermes_base_url": self.hermes_base_url,
            "hermes_api_key": enc_api_key,
            "hermes_emailbot_id": enc_bot_id,
            "recipient_email": self.recipient_email,
            "passphrase_hash": self.passphrase_hash,
            "passphrase_salt": self.passphrase_salt,
            "default_timeout_mins": self.default_timeout_mins
        }
        
        # Write file with restricted access if possible
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600  # User read/write only
        
        # On Windows, open with standard fd/mode does not fully block all permissions,
        # but we also encrypt the key inside the JSON using DPAPI which protects it.
        try:
            fd = os.open(self.CONFIG_FILE, flags, mode)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception:
            # Fallback to standard open if os.open fails
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
    def set_credentials(self, 
                        api_key: str, 
                        bot_id: Optional[str], 
                        recipient: str, 
                        passphrase: str,
                        base_url: str = "https://hermesbot.pythonanywhere.com",
                        default_timeout_mins: int = 2) -> None:
        self.default_timeout_mins = default_timeout_mins
        """Sets configuration values and hashes the passphrase."""
        self.hermes_base_url = base_url.strip()
        self.hermes_api_key = api_key.strip()
        self.hermes_emailbot_id = bot_id.strip() if bot_id else None
        self.recipient_email = recipient.strip()
        
        h, s = hash_passphrase(passphrase)
        self.passphrase_hash = h
        self.passphrase_salt = s
        
    def check_passphrase(self, passphrase: str) -> bool:
        """Validates input passphrase against stored hash."""
        if not self.passphrase_hash or not self.passphrase_salt:
            return False
        return verify_passphrase(passphrase, self.passphrase_hash, self.passphrase_salt)

    @classmethod
    def reset_state(cls) -> dict:
        """Deletes all local application data, logs, config, and snapshots.
        
        Returns:
            dict: Summary of deleted items.
        """
        import logging
        
        summary = {
            "config_deleted": False,
            "logs_deleted": False,
            "snapshots_deleted": 0,
            "dir_recreated": False
        }
        
        # Close any open file handlers to release file locks on Windows
        logger = logging.getLogger("sentryboot")
        for handler in list(logger.handlers):
            try:
                handler.close()
                logger.removeHandler(handler)
            except Exception:
                pass
                
        if cls.CONFIG_DIR.exists():
            # Delete configuration file
            if cls.CONFIG_FILE.exists():
                try:
                    cls.CONFIG_FILE.unlink()
                    summary["config_deleted"] = True
                except Exception:
                    pass
                    
            # Delete snapshots
            snapshots_dir = cls.CONFIG_DIR / "snapshots"
            if snapshots_dir.exists():
                try:
                    for f in snapshots_dir.glob("*"):
                        if f.is_file():
                            f.unlink()
                            summary["snapshots_deleted"] += 1
                    snapshots_dir.rmdir()
                except Exception:
                    pass
                    
            # Delete logs
            for f in cls.CONFIG_DIR.glob("*.log*"):
                try:
                    if f.is_file():
                        f.unlink()
                        summary["logs_deleted"] = True
                except Exception:
                    pass
                    
            # Delete any other stray files
            for f in cls.CONFIG_DIR.glob("*"):
                try:
                    if f.is_file():
                        f.unlink()
                except Exception:
                    pass
                    
            # Recreate the clean directory structure
            try:
                cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                summary["dir_recreated"] = True
            except Exception:
                pass
        else:
            try:
                cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                summary["dir_recreated"] = True
            except Exception:
                pass
                
        return summary

