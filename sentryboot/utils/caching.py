import os
import json
import time
import uuid
import logging
import threading
from pathlib import Path
from typing import Optional, Dict
from sentryboot.config.manager import ConfigManager
from sentryboot.emailer.client import HermesClient
from sentryboot.logging.logger import log_event

CACHE_DIR = Path.home() / ".sentryboot" / "cache"

def cache_alert(reason: str, 
                diagnostics: dict, 
                snapshot_name: Optional[str], 
                snapshot_base64: Optional[str], 
                forensics: Dict[str, str]):
    """Saves alert payload locally to cache directory when offline."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "reason": reason,
            "diagnostics": diagnostics,
            "snapshot_name": snapshot_name,
            "snapshot_base64": snapshot_base64,
            "forensics": forensics,
            "timestamp": time.time()
        }
        filename = CACHE_DIR / f"alert_{int(time.time())}_{uuid.uuid4().hex[:8]}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)
        log_event(f"Alert cached offline: {reason}", "FAILED", "NO")
    except Exception as e:
        # Fallback logging if caching fails
        logging.error(f"Failed to cache alert: {str(e)}")

def sync_cached_alerts(config: ConfigManager):
    """Attempts to send all cached offline alerts via Hermes API."""
    if not CACHE_DIR.exists():
        return

    json_files = sorted(CACHE_DIR.glob("*.json"))
    if not json_files:
        return

    log_event(f"Syncing {len(json_files)} cached offline alert(s)", "N/A", "NO")
    
    # Initialize Hermes Client
    client = HermesClient(
        base_url=config.hermes_base_url,
        api_key=config.hermes_api_key,
        bot_id=config.hermes_emailbot_id
    )

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
                
            reason = payload.get("reason", "Unknown")
            diagnostics = payload.get("diagnostics", {})
            snapshot_name = payload.get("snapshot_name")
            snapshot_base64 = payload.get("snapshot_base64")
            forensics = payload.get("forensics", {})
            
            # Format HTML body for the cached alert
            from sentryboot.notifications.formatter import format_alert_email
            html_body = format_alert_email(reason, diagnostics, snapshot_base64=snapshot_base64)
            
            # Build attachments list
            attachments = []
            if snapshot_base64 and snapshot_name:
                attachments.append({
                    "filename": snapshot_name,
                    "content": snapshot_base64
                })
            
            # Add forensics files
            import base64
            for name, content in forensics.items():
                if content:
                    b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
                    attachments.append({
                        "filename": name,
                        "content": b64_content
                    })
            
            # Dispatch email
            client.send_email(
                to_emails=config.recipient_email,
                subject=f"⚠️ [SentryBoot Alert] Offline Alert Sync ({reason})",
                body_html=html_body,
                from_name="SentryBoot Guard",
                attachments=attachments if attachments else None
            )
            
            # Remove cached file on success
            file_path.unlink()
            log_event(f"Cached alert synced successfully: {reason}", "N/A", "NO")
            
        except Exception as e:
            # If a sync fails, abort the loop and wait for next sync cycle
            log_event(f"Sync failed for {file_path.name}: {str(e)}", "N/A", "NO")
            break

def start_background_sync(config: ConfigManager):
    """Launches the cached alert synchronization task in a daemon thread."""
    thread = threading.Thread(target=sync_cached_alerts, args=(config,), daemon=True)
    thread.start()
