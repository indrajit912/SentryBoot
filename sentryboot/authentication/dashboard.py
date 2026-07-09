import os
import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from sentryboot import __version__, __author__, __copyright__
from sentryboot.utils.system_info import get_system_diagnostics
from sentryboot.config.manager import ConfigManager

def display_welcome_dashboard(config: ConfigManager, console: Optional[Console] = None):
    """Displays a premium post-authentication success dashboard in the console.
    
    Handles missing or unavailable statistics gracefully, using ASCII-safe headers
    to prevent unicode character map encoding errors on legacy Windows platforms.
    """
    if console is None:
        console = Console()
    
    # Retrieve system statistics with safe fallback
    try:
        diagnostics = get_system_diagnostics()
    except Exception:
        diagnostics = {}
        
    username = diagnostics.get("username", os.environ.get("USERNAME") or "User")
    comp_name = diagnostics.get("computer_name", "Unknown-PC")
    uptime = diagnostics.get("uptime_str", "N/A")
    boot_time = diagnostics.get("boot_time_str", "N/A")
    local_ip = diagnostics.get("local_ip", "127.0.0.1")
    public_ip = diagnostics.get("public_ip", "Offline")
    
    # Welcome Message with premium styling
    welcome_text = Text()
    welcome_text.append(f"*** Welcome Back, {username}! ***\n", style="bold green")
    welcome_text.append("Passphrase verified successfully. Access granted.", style="dim white")
    
    # Left Column Table - Session & System Info
    sys_table = Table(show_header=False, box=None, padding=(0, 2))
    sys_table.add_row("[bold cyan]Session User:[/]", username)
    sys_table.add_row("[bold cyan]Host Name:[/]", comp_name)
    sys_table.add_row("[bold cyan]System Uptime:[/]", uptime)
    sys_table.add_row("[bold cyan]Boot Time:[/]", boot_time)
    
    # Right Column Table - Network & Security Info
    sec_table = Table(show_header=False, box=None, padding=(0, 2))
    sec_table.add_row("[bold yellow]Security Status:[/]", "[bold green]ACTIVE[/]")
    sec_table.add_row("[bold yellow]Recipient Email:[/]", config.recipient_email or "N/A")
    sec_table.add_row("[bold yellow]Local IP Address:[/]", local_ip)
    sec_table.add_row("[bold yellow]Public IP Address:[/]", public_ip)
    
    # Wrap tables in panels for visual separation
    panel_left = Panel(sys_table, title="[bold white][ SYSTEM INFO ][/]", border_style="cyan", expand=True)
    panel_right = Panel(sec_table, title="[bold white][ SECURITY INFO ][/]", border_style="yellow", expand=True)
    
    # Combine panels side-by-side using rich.columns
    cols = Columns([panel_left, panel_right], expand=True)
    
    # Print the welcome banner
    console.print()
    console.print(Panel(
        welcome_text,
        title="[bold green]SENTRYBOOT ACCESS GRANTED[/]",
        border_style="green",
        expand=False,
        padding=(1, 6)
    ))
    
    # Print the columns below
    console.print(cols)
    console.print(f"[dim grey]SentryBoot v{__version__} | Logs: {ConfigManager.CONFIG_DIR / 'boot.log'}[/dim grey]\n")
