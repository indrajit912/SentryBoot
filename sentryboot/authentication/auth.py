import os
import sys
import time
import threading
import base64
from typing import Optional, Tuple
from pathlib import Path

# Rich Console imports
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn

from sentryboot import __version__, __author__, __website__, __copyright__
from sentryboot.config.manager import ConfigManager
from sentryboot.utils.win_handlers import register_close_handler
from sentryboot.utils.system_info import get_system_diagnostics
from sentryboot.emailer.client import HermesClient
from sentryboot.notifications.formatter import format_alert_email
from sentryboot.logging.logger import log_event
from sentryboot.utils.camera import capture_snapshot

try:
    import msvcrt
except ImportError:
    msvcrt = None

# Thread safety for alert dispatch
email_lock = threading.Lock()
email_sent = False

def send_alert_email(reason: str, config: ConfigManager) -> bool:
    """Dispatches the security alert email via Hermes. Thread-safe."""
    global email_sent
    with email_lock:
        if email_sent:
            return True
        email_sent = True
        
    try:
        diagnostics = get_system_diagnostics()
        
        # Attempt to capture a webcam snapshot
        snapshot_dir = Path.home() / ".sentryboot" / "snapshots"
        snapshot_path = None
        snapshot_base64 = None
        
        try:
            snapshot_path = capture_snapshot(snapshot_dir)
            if snapshot_path and snapshot_path.exists():
                with open(snapshot_path, "rb") as image_file:
                    snapshot_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception:
            # Do not fail if webcam capture fails for any reason
            pass
            
        html_body = format_alert_email(reason, diagnostics, snapshot_base64=snapshot_base64)
        
        attachments = None
        if snapshot_base64 and snapshot_path:
            attachments = [{
                "filename": snapshot_path.name,
                "content": snapshot_base64
            }]
            
        client = HermesClient(
            base_url=config.hermes_base_url,
            api_key=config.hermes_api_key,
            bot_id=config.hermes_emailbot_id
        )
        
        client.send_email(
            to_emails=config.recipient_email,
            subject=f"⚠️ [SentryBoot Alert] Unauthorized Access ({reason})",
            body_html=html_body,
            from_name="SentryBoot Guard",
            attachments=attachments
        )
        
        snap_log_str = str(snapshot_path) if snapshot_path else "None"
        log_event(f"Alert Sent: {reason}", "FAILED", "YES", snapshot_path=snap_log_str)
        return True
    except Exception as e:
        log_event(f"Alert Failed: {reason}", "FAILED", "FAILED", str(e))
        return False


def build_ui_panel(remaining: float, 
                   max_time: float, 
                   input_masked: str, 
                   attempts_left: int, 
                   status_msg: str, 
                   status_style: str = "white") -> Panel:
    """Builds a beautiful Rich UI layout containing the logo, info, countdown bar, and passphrase prompt."""
    
    # Progress color based on remaining time
    if remaining > 60:
        bar_style = "green"
    elif remaining > 30:
        bar_style = "yellow"
    else:
        bar_style = "red"
        
    pct = max(0.0, min(1.0, remaining / max_time))
    bar_width = 30
    filled_width = int(pct * bar_width)
    bar_char = "█"
    empty_char = "░"
    bar_str = f"[{bar_style}]{bar_char * filled_width}{empty_char * (bar_width - filled_width)}[/{bar_style}]"
    
    # Header title
    title_text = Text()
    title_text.append("🛡️ SENTRYBOOT SECURITY SHIELD", style="bold red")
    
    body_text = Text()
    body_text.append(f"\nVersion: v{__version__} | Developer: {__author__} ({__website__})\n", style="dim grey")
    body_text.append(f"{__copyright__}\n\n", style="dim grey")
    body_text.append("SYSTEM STATUS: LOCKDOWN\n", style="bold red blink")
    body_text.append("Please enter the secret passphrase to unlock the terminal.\n", style="white")
    
    if max_time % 60 == 0:
        time_desc = f"{int(max_time / 60)} minute(s)" if max_time != 60 else "1 minute"
    else:
        time_desc = f"{int(max_time)} seconds"
        
    body_text.append(f"You have {time_desc} to authenticate before an alert is dispatched.\n\n", style="yellow")
    
    body_text.append(f"Time Remaining: {int(remaining)}s  {bar_str}\n", style="bold")
    body_text.append(f"Security Attempts Left: {attempts_left}\n\n", style="bold yellow" if attempts_left > 1 else "bold red")
    
    body_text.append("Passphrase: ", style="bold cyan")
    body_text.append(input_masked, style="bold white")
    
    if status_msg:
        body_text.append(f"\n\n👉 {status_msg}", style=status_style)
        
    return Panel(
        body_text,
        title=title_text,
        border_style="red" if remaining < 30 else "blue",
        expand=False,
        padding=(1, 4)
    )


def run_auth_challenge(timeout_seconds: Optional[int] = None) -> bool:
    """Runs the interactive authentication CLI challenge.
    
    Returns:
        bool: True if user authenticated successfully, False otherwise.
    """
    console = Console()
    config = ConfigManager()
    
    if not config.load():
        console.print("[bold red]Error: SentryBoot is not initialized. Run 'sentryboot init' first.[/bold red]")
        return False
        
    if timeout_seconds is None:
        # Fallback to configured default (default to 120s if somehow missing)
        timeout_seconds = int(getattr(config, "default_timeout_mins", 2) * 60)
        
    # Set Windows Console Title
    if sys.platform == 'win32':
        try:
            ctypes.windll.kernel32.SetConsoleTitleW("SentryBoot - System Locked")
        except Exception:
            pass

    # Log application start
    log_event("SentryBoot Guard Started", "PENDING", "NO")
    
    # Define Close Event Callback
    def on_console_close(ctrl_type: int):
        event_names = {
            2: "Terminal Closed",
            5: "User Logoff",
            6: "System Shutdown"
        }
        reason = event_names.get(ctrl_type, "Terminal Terminated Abruptly")
        # Direct trigger email in separate OS thread
        send_alert_email(reason, config)
        log_event(f"System closed abruptly ({reason})", "ABRUPT_CLOSE", "YES")
        
    # Register Win32 close handler
    registered_handler = register_close_handler(on_console_close)
    
    attempts_left = 3
    input_chars = []
    status_msg = ""
    status_style = "white"
    
    start_time = time.time()
    success = False
    
    # Visual character masking
    mask_char = "*"
    
    if msvcrt is None:
        # Fallback for non-Windows systems (macOS/Linux testing)
        console.print("[yellow]Non-Windows environment detected. Falling back to blocking input.[/yellow]")
        while attempts_left > 0:
            elapsed = time.time() - start_time
            if elapsed >= timeout_seconds:
                send_alert_email("Timeout Expired", config)
                return False
                
            try:
                passphrase = console.input("[bold cyan]Enter Passphrase:[/bold cyan] ", password=True)
            except (KeyboardInterrupt, EOFError):
                send_alert_email("Keyboard Interrupt", config)
                return False
                
            if config.check_passphrase(passphrase):
                log_event("Successful Authentication", "SUCCESS", "NO")
                console.print("[bold green]Success! Access Granted.[/bold green]")
                return True
            else:
                attempts_left -= 1
                log_event("Incorrect Passphrase", "FAILED", "NO")
                console.print(f"[bold red]Incorrect Passphrase. Attempts left: {attempts_left}[/bold red]")
                
        send_alert_email("Too Many Failed Attempts", config)
        return False

    # Windows Interactive masked non-blocking loop
    with Live(auto_refresh=False) as live:
        while True:
            elapsed = time.time() - start_time
            remaining = timeout_seconds - elapsed
            
            if remaining <= 0:
                live.update(Panel(Text("TIMEOUT EXPIRED. SENDING EMAIL ALERT...", style="bold red"), border_style="red"))
                live.refresh()
                send_alert_email("Timeout Expired", config)
                break
                
            # Update console title bar
            try:
                ctypes.windll.kernel32.SetConsoleTitleW(f"SentryBoot - {int(remaining)}s remaining")
            except Exception:
                pass
                
            # Render UI
            masked_str = mask_char * len(input_chars)
            panel = build_ui_panel(remaining, timeout_seconds, masked_str, attempts_left, status_msg, status_style)
            live.update(panel)
            live.refresh()
            
            # Check keyboard buffer
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                
                # Check for enter key
                if ch == b'\r' or ch == b'\n':
                    passphrase = "".join(input_chars)
                    input_chars.clear()
                    
                    if config.check_passphrase(passphrase):
                        success = True
                        log_event("Successful Authentication", "SUCCESS", "NO")
                        live.update(Panel(Text("ACCESS GRANTED. UNLOCKING...", style="bold green"), border_style="green"))
                        live.refresh()
                        break
                    else:
                        attempts_left -= 1
                        log_event("Incorrect Passphrase", f"FAILED ({attempts_left} left)", "NO")
                        status_msg = "Incorrect Passphrase! Access Denied."
                        status_style = "bold red"
                        
                        if attempts_left <= 0:
                            live.update(Panel(Text("TOO MANY FAILED ATTEMPTS. SENDING EMAIL ALERT...", style="bold red"), border_style="red"))
                            live.refresh()
                            send_alert_email("Too Many Failed Attempts", config)
                            break
                            
                # Check backspace
                elif ch == b'\x08':
                    if input_chars:
                        input_chars.pop()
                        
                # Check for Ctrl+C (Keyboard Interrupt)
                elif ch == b'\x03':
                    log_event("Keyboard Interrupt (Ctrl+C)", "INTERRUPTED", "YES")
                    live.update(Panel(Text("ABORTED BY USER. SENDING EMAIL ALERT...", style="bold red"), border_style="red"))
                    live.refresh()
                    send_alert_email("Keyboard Interrupt (Ctrl+C)", config)
                    break
                    
                # Ignore control key prefixes (e.g. arrows, fn keys)
                elif ch in (b'\x00', b'\xe0'):
                    if msvcrt.kbhit():
                        msvcrt.getch() # consume the trailing byte
                        
                # Handle standard keys
                else:
                    try:
                        char_str = ch.decode('utf-8')
                        if char_str.isprintable():
                            input_chars.append(char_str)
                    except UnicodeDecodeError:
                        pass
                        
            time.sleep(0.05)
            
    # Reset title bar
    if sys.platform == 'win32':
        try:
            ctypes.windll.kernel32.SetConsoleTitleW("Command Prompt")
        except Exception:
            pass
            
    return success
