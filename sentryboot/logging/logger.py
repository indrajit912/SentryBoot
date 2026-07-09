import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional

LOG_DIR = Path.home() / ".sentryboot"
LOG_FILE = LOG_DIR / "boot.log"

class SentryFormatter(logging.Formatter):
    """Custom log formatter that uses the timestamp format:
    Mmm dd, YY HH:mm:ss AM/PM
    """
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        return dt.strftime("%b %d, %y %I:%M:%S %p")


def setup_logger() -> logging.Logger:
    """Configures and returns the SentryBoot rotating logger."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("sentryboot")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        # Rotate after 2MB, keep 5 backups
        handler = RotatingFileHandler(
            LOG_FILE, 
            maxBytes=2 * 1024 * 1024, 
            backupCount=5, 
            encoding='utf-8'
        )
        
        # Format: Time | Event | Auth Status | Email Sent | Exception
        formatter = SentryFormatter(
            fmt="%(asctime)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger


def log_event(event: str, 
              auth_status: str, 
              email_sent: str, 
              exception_str: str = "None") -> None:
    """Utility to log structured security boot events.
    
    Format of output:
    Event: <event> | Auth: <auth_status> | Email Sent: <email_sent> | Error: <exception_str>
    """
    logger = setup_logger()
    log_msg = f"Event: {event:<25} | Auth: {auth_status:<10} | Email Sent: {email_sent:<6} | Error: {exception_str}"
    logger.info(log_msg)


def get_log_content(lines_count: int = 100) -> str:
    """Retrieves the last lines of the log file."""
    if not LOG_FILE.exists():
        return "No log events found. File does not exist yet."
        
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return "".join(lines[-lines_count:])
    except Exception as e:
        return f"Error reading log file: {str(e)}"
