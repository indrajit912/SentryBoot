import sys
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Force UTF-8 encoding for standard output and error on Windows to prevent UnicodeEncodeErrors
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


from sentryboot import __version__, __author__, __website__, __copyright__
from sentryboot.config.manager import ConfigManager
from sentryboot.logging.logger import log_event, get_log_content, LOG_FILE
from sentryboot.authentication.auth import run_auth_challenge, send_alert_email
from sentryboot.utils.system_info import get_system_diagnostics
from sentryboot.emailer.client import HermesClient
from sentryboot.notifications.formatter import format_test_email

app = typer.Typer(
    name="sentryboot",
    help="🛡️ SentryBoot: Windows Boot-time Authentication and Alert Sentry.",
    no_args_is_help=True
)

console = Console()

def print_banner():
    """Prints a consistent, premium CLI banner."""
    banner_text = Text()
    banner_text.append(f"🛡️ SentryBoot CLI v{__version__}\n", style="bold cyan")
    banner_text.append(f"{__copyright__} | Developer: {__author__} ({__website__})", style="dim grey")
    console.print(Panel(banner_text, border_style="cyan", expand=False))


@app.command("init")
def init():
    """First-time setup of SentryBoot configuration and email client validation."""
    print_banner()
    
    config = ConfigManager()
    
    # Clean previous state if it exists
    if config.exists() or ConfigManager.CONFIG_DIR.exists():
        console.print("[bold yellow]Previous application data detected. Cleaning up...[/bold yellow]")
        cleanup_summary = ConfigManager.reset_state()
        
        # Display summary
        summary_msg = []
        if cleanup_summary["config_deleted"]:
            summary_msg.append("  - Deleted configuration file")
        if cleanup_summary["logs_deleted"]:
            summary_msg.append("  - Deleted log files")
        if cleanup_summary["snapshots_deleted"] > 0:
            summary_msg.append(f"  - Deleted {cleanup_summary['snapshots_deleted']} snapshot(s)")
            
        if summary_msg:
            console.print("[green]Cleanup complete:[/green]")
            for msg in summary_msg:
                console.print(msg)
        else:
            console.print("[green]No files required cleaning.[/green]")
        console.print("[bold green]✔ Directory structure re-initialized cleanly.[/bold green]\n")
        
    console.print("[bold yellow]Creating Hermes Email Bot Setup:[/bold yellow]")
    console.print("1. Go to your Hermes Bot website: [cyan]https://hermesbot.pythonanywhere.com[/cyan]")
    console.print("2. Log in and create an Email Bot (or note your existing API Key and Bot ID).")
    console.print("3. Prepare your recipient email address and secure passphrase.\n")
    
    # Prompt config variables
    base_url = typer.prompt("Hermes API Base URL", default="https://hermesbot.pythonanywhere.com")
    api_key = typer.prompt("Hermes API Key (Secret)", hide_input=True)
    bot_id = typer.prompt("Hermes Email Bot ID", default="")
    recipient = typer.prompt("Recipient Email Address")
    timeout_mins = typer.prompt("Default Passphrase Timeout (in minutes)", default=2, type=int)
    
    while True:
        passphrase = typer.prompt("Create Secret Passphrase (for unlocking)", hide_input=True)
        confirm = typer.prompt("Confirm Passphrase", hide_input=True)
        if passphrase == confirm:
            break
        console.print("[bold red]Passphrases do not match! Please try again.[/bold red]")
        
    console.print("\n[bold yellow]Saving configuration securely...[/bold yellow]")
    config.set_credentials(
        api_key=api_key,
        bot_id=bot_id,
        recipient=recipient,
        passphrase=passphrase,
        base_url=base_url,
        default_timeout_mins=timeout_mins
    )
    config.save()
    console.print("[bold green]✔ Configuration saved and encrypted using Windows DPAPI.[/bold green]")
    
    # Run config validation by sending a test email
    console.print("\n[bold yellow]Sending test email to validate configuration...[/bold yellow]")
    try:
        diagnostics = get_system_diagnostics()
        html_body = format_test_email(diagnostics)
        
        client = HermesClient(
            base_url=config.hermes_base_url,
            api_key=config.hermes_api_key,
            bot_id=config.hermes_emailbot_id
        )
        
        with console.status("[bold green]Dispatching test email via Hermes API...[/bold green]"):
            client.send_email(
                to_emails=config.recipient_email,
                subject=f"✅ SentryBoot Test Notification",
                body_html=html_body,
                from_name="SentryBoot Guard"
            )
            
        log_event("SentryBoot Initialized", "N/A", "YES")
        console.print("[bold green]✔ Test email sent successfully! Please check your inbox.[/bold green]")
        console.print("[bold green]✔ SentryBoot first-time setup completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Failed to send test email: {str(e)}[/bold red]")
        console.print("[bold red]Please verify your Hermes API credentials and internet connection.[/bold red]")
        log_event("SentryBoot Initialization Failed", "N/A", "FAILED", str(e))
        sys.exit(1)


@app.command("start")
def start(timeout: Optional[int] = typer.Option(None, help="Challenge timeout in seconds. If not specified, uses the configured default.")):
    """Launches the SentryBoot authentication challenge (typically invoked by Windows Task Scheduler)."""
    config = ConfigManager()
    config.load()
    
    # Start background synchronization of cached offline alerts
    from sentryboot.utils.caching import start_background_sync
    start_background_sync(config)
    
    if timeout is None:
        timeout_seconds = int(config.default_timeout_mins * 60)
    else:
        timeout_seconds = timeout
        
    success = run_auth_challenge(timeout_seconds=timeout_seconds)
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


@app.command("status")
def status():
    """Displays the initialization and security status of SentryBoot."""
    print_banner()
    
    config = ConfigManager()
    table = Table(title="SentryBoot Status Details", border_style="cyan")
    table.add_column("Property", style="bold white")
    table.add_column("Value", style="cyan")
    
    initialized = config.load()
    table.add_row("Status", "[green]Initialized[/green]" if initialized else "[red]Not Initialized[/red]")
    table.add_row("Configuration Path", str(ConfigManager.CONFIG_FILE))
    table.add_row("Log Path", str(LOG_FILE))
    
    if initialized:
        diagnostics = get_system_diagnostics()
        table.add_row("Recipient Email", config.recipient_email)
        table.add_row("Hermes API URL", config.hermes_base_url)
        table.add_row("Windows Computer Name", diagnostics.get("computer_name"))
        table.add_row("Windows Active User", diagnostics.get("username"))
        
    console.print(table)


@app.command("test-email")
def test_email():
    """Sends a manual test email to the configured recipient."""
    config = ConfigManager()
    if not config.load():
        console.print("[bold red]SentryBoot is not initialized. Run 'sentryboot init' first.[/bold red]")
        sys.exit(1)
        
    console.print(f"[bold yellow]Sending test email to: {config.recipient_email}...[/bold yellow]")
    try:
        diagnostics = get_system_diagnostics()
        html_body = format_test_email(diagnostics)
        
        client = HermesClient(
            base_url=config.hermes_base_url,
            api_key=config.hermes_api_key,
            bot_id=config.hermes_emailbot_id
        )
        
        with console.status("[bold green]Connecting to Hermes...[/bold green]"):
            client.send_email(
                to_emails=config.recipient_email,
                subject=f"✅ SentryBoot Manual Test",
                body_html=html_body,
                from_name="SentryBoot Guard"
            )
        log_event("Manual Test Email Sent", "N/A", "YES")
        console.print("[bold green]✔ Manual test email dispatched successfully.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to dispatch test email: {str(e)}[/bold red]")
        log_event("Manual Test Email Failed", "N/A", "FAILED", str(e))
        sys.exit(1)


@app.command("config")
def show_config():
    """Safely displays current configuration metadata without leaking secrets."""
    print_banner()
    config = ConfigManager()
    if not config.load():
        console.print("[bold red]SentryBoot is not initialized. Run 'sentryboot init' first.[/bold red]")
        sys.exit(1)
        
    table = Table(title="SentryBoot Safe Configuration View", border_style="blue")
    table.add_column("Key", style="bold white")
    table.add_column("Value", style="yellow")
    
    table.add_row("Hermes Base URL", config.hermes_base_url)
    table.add_row("Hermes API Key", "[PROTECTED & ENCRYPTED WITH WINDOWS DPAPI]")
    table.add_row("Hermes Emailbot ID", config.hermes_emailbot_id or "Not Configured")
    table.add_row("Recipient Email", config.recipient_email)
    table.add_row("Default Timeout (Mins)", str(config.default_timeout_mins))
    table.add_row("Passphrase Salt (Hex)", config.passphrase_salt)
    table.add_row("Passphrase Hash (Hex)", config.passphrase_hash)
    
    console.print(table)


@app.command("update-secrets")
def update_secrets():
    """Securely updates the secret passphrase, Hermes API Key, and Emailbot ID."""
    print_banner()
    config = ConfigManager()
    if not config.load():
        console.print("[bold red]SentryBoot is not initialized. Run 'sentryboot init' first.[/bold red]")
        sys.exit(1)
        
    # Verify current passphrase for security
    current_pass = typer.prompt("Enter CURRENT passphrase to authorize changes", hide_input=True)
    if not config.check_passphrase(current_pass):
        console.print("[bold red]❌ Authentication failed. Unauthorized modification blocked.[/bold red]")
        log_event("Unauthorized Configuration Change Attempted", "FAILED", "NO")
        sys.exit(1)
        
    console.print("[bold green]✔ Current passphrase verified successfully.[/bold green]\n")
    console.print("[bold yellow]Enter new secrets (leave blank to keep current value):[/bold yellow]")
    
    # Prompt for new Hermes API key
    new_api_key = typer.prompt("New Hermes API Key", default="[keep current]", show_default=True)
    if new_api_key != "[keep current]" and new_api_key.strip():
        config.hermes_api_key = new_api_key.strip()
        
    # Prompt for new Bot ID
    current_bot_id = config.hermes_emailbot_id or ""
    new_bot_id = typer.prompt("New Hermes Email Bot ID", default=current_bot_id, show_default=True)
    config.hermes_emailbot_id = new_bot_id.strip() if new_bot_id.strip() else None
    
    # Prompt for new Passphrase
    change_pass = typer.confirm("Do you want to change the secret passphrase?")
    if change_pass:
        while True:
            new_pass = typer.prompt("Create New Secret Passphrase", hide_input=True)
            confirm = typer.prompt("Confirm New Secret Passphrase", hide_input=True)
            if new_pass == confirm:
                from sentryboot.config.manager import hash_passphrase
                h, s = hash_passphrase(new_pass)
                config.passphrase_hash = h
                config.passphrase_salt = s
                break
            console.print("[bold red]Passphrases do not match! Please try again.[/bold red]")
            
    # Prompt for new default timeout
    new_timeout = typer.prompt("New Default Passphrase Timeout (in minutes)", default=config.default_timeout_mins, type=int)
    config.default_timeout_mins = new_timeout
            
    # Save the updated configuration
    config.save()
    console.print("\n[bold green]✔ Configuration updated and encrypted successfully.[/bold green]")
    log_event("Configuration Secrets Updated", "N/A", "NO")


@app.command("logs")
def show_logs(lines: int = typer.Option(50, help="Number of tail lines to display.")):
    """Displays the rolling SentryBoot logs with color formatting."""
    print_banner()
    console.print(f"[bold yellow]Tailing last {lines} entries of SentryBoot log:[/bold yellow]")
    log_content = get_log_content(lines)
    
    # Display formatted logs
    console.print(Panel(log_content, border_style="grey37", title="boot.log", expand=False))


@app.command("version")
def show_version():
    """Displays application version, developer and website details."""
    print_banner()


if __name__ == "__main__":
    app()
