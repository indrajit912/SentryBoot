from typing import Dict, Any, Tuple, Optional
from sentryboot import __version__, __author__, __website__, __copyright__

def format_alert_email(event_name: str, diagnostics: Dict[str, Any], snapshot_base64: Optional[str] = None) -> str:
    """Generates the HTML email body for a security alert.
    
    Args:
        event_name: Name of the event that triggered the alert (e.g., Timeout, Failed Login)
        diagnostics: System diagnostics dictionary
        snapshot_base64: Optional base64 encoded string of the captured webcam snapshot
        
    Returns:
        str: HTML Body
    """
    subject = f"⚠️ [SentryBoot Alert] Unauthorized Computer Access Detected!"
    
    # Extract details
    comp_name = diagnostics.get("computer_name", "Unknown")
    username = diagnostics.get("username", "Unknown")
    local_ip = diagnostics.get("local_ip", "Unknown")
    public_ip = diagnostics.get("public_ip", "Unknown")
    uptime = diagnostics.get("uptime_str", "Unknown")
    boot_time = diagnostics.get("boot_time_str", "Unknown")
    
    # Snapshot HTML snippet
    if snapshot_base64:
        snapshot_html = f"""
                            <!-- Intruder Snapshot -->
                            <div style="background-color: #12141a; border: 1px solid #ff3366; border-radius: 8px; padding: 15px; margin: 25px 0; text-align: center;">
                                <p style="color: #ff3366; font-size: 14px; font-weight: bold; text-transform: uppercase; margin-top: 0; margin-bottom: 12px; letter-spacing: 0.5px;">📸 Captured Intruder Photo</p>
                                <img src="data:image/jpeg;base64,{snapshot_base64}" alt="Intruder Snapshot" style="max-width: 100%; height: auto; border-radius: 4px; border: 1px solid #2d3139; box-shadow: 0 4px 8px rgba(0,0,0,0.5);" />
                            </div>
        """
    else:
        snapshot_html = """
                            <!-- No Snapshot Available -->
                            <div style="background-color: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107; padding: 12px 15px; margin: 25px 0; border-radius: 4px; color: #ffc107; font-size: 13px;">
                                ⚠️ Webcam snapshot unavailable (No webcam detected or device already busy).
                            </div>
        """
        
    # HTML template with premium dark-themed security layout
    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SentryBoot Security Alert</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0f1115; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e9ecef;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0f1115; padding: 40px 10px;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #1a1d24; border-radius: 12px; overflow: hidden; border: 1px solid #2d3139; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #ff3366 0%, #ff5e36 100%); padding: 30px 20px;">
                            <div style="font-size: 48px; margin-bottom: 10px;">⚠️</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Security Alert</h1>
                            <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.8); font-size: 14px; font-weight: 500;">Unauthorized System Access Attempt Detected</p>
                        </td>
                    </tr>
                    
                    <!-- Content Panel -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin-top: 0; font-size: 16px; line-height: 1.6; color: #ced4da;">
                                SentryBoot has intercepted an unauthenticated system access on your computer. The security passphrase challenge was not successfully completed.
                            </p>
                            
                            <!-- Event Callout -->
                            <div style="background-color: rgba(255, 77, 77, 0.1); border-left: 4px solid #ff3366; padding: 15px 20px; margin: 25px 0; border-radius: 4px;">
                                <strong style="color: #ff4d4d; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Trigger Event:</strong>
                                <div style="font-size: 18px; font-weight: 600; color: #ffffff; margin-top: 5px;">{event_name}</div>
                            </div>
                            
                            {snapshot_html}
                            
                            <h2 style="font-size: 18px; color: #ffffff; border-bottom: 1px solid #2d3139; padding-bottom: 8px; margin-top: 30px;">System Details</h2>
                            
                            <!-- Diagnostics Table -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 14px; margin-top: 15px;">
                                <tr style="border-bottom: 1px solid #2d3139;">
                                    <td style="padding: 10px 0; color: #868e96; font-weight: 500; width: 40%;">Computer Name</td>
                                    <td style="padding: 10px 0; color: #ffffff; font-weight: 600;">{comp_name}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #2d3139;">
                                    <td style="padding: 10px 0; color: #868e96; font-weight: 500;">Windows User</td>
                                    <td style="padding: 10px 0; color: #ffffff; font-weight: 600;">{username}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #2d3139;">
                                    <td style="padding: 10px 0; color: #868e96; font-weight: 500;">Boot Local Timestamp</td>
                                    <td style="padding: 10px 0; color: #ffffff; font-weight: 600;">{boot_time}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #2d3139;">
                                    <td style="padding: 10px 0; color: #868e96; font-weight: 500;">Local IP Address</td>
                                    <td style="padding: 10px 0; color: #ffffff; font-weight: 600; font-family: monospace;">{local_ip}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #2d3139;">
                                    <td style="padding: 10px 0; color: #868e96; font-weight: 500;">Public IP Address</td>
                                    <td style="padding: 10px 0; color: #ffffff; font-weight: 600; font-family: monospace;">{public_ip}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #2d3139;">
                                    <td style="padding: 10px 0; color: #868e96; font-weight: 500;">System Uptime</td>
                                    <td style="padding: 10px 0; color: #ffffff; font-weight: 600;">{uptime}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0; color: #868e96; font-weight: 500;">SentryBoot Version</td>
                                    <td style="padding: 10px 0; color: #ffffff; font-weight: 600;">v{__version__}</td>
                                </tr>
                            </table>
                            
                            <p style="margin-top: 35px; margin-bottom: 0; font-size: 13px; color: #868e96; line-height: 1.5; text-align: center;">
                                If this was you, please inspect your configuration or passphrase input latency. If this was not you, your system security may be compromised.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #12141a; padding: 25px 30px; text-align: center; border-top: 1px solid #2d3139; font-size: 12px; color: #6c757d;">
                            <p style="margin: 0 0 5px 0;">{__copyright__}</p>
                            <p style="margin: 0;">
                                Developed by <a href="{__website__}" style="color: #ff3366; text-decoration: none; font-weight: 500;">{__author__}</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html_body


def format_test_email(diagnostics: Dict[str, Any]) -> str:
    """Generates the HTML email body for a test email during init.
    
    Args:
        diagnostics: System diagnostics dictionary
        
    Returns:
        str: HTML Body
    """
    comp_name = diagnostics.get("computer_name", "Unknown")
    username = diagnostics.get("username", "Unknown")
    
    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SentryBoot Test Verification</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0f1115; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e9ecef;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0f1115; padding: 40px 10px;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #1a1d24; border-radius: 12px; overflow: hidden; border: 1px solid #2d3139; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px 20px;">
                            <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">SentryBoot Setup</h1>
                            <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.8); font-size: 14px; font-weight: 500;">Hermes Integration Successful</p>
                        </td>
                    </tr>
                    
                    <!-- Content Panel -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin-top: 0; font-size: 16px; line-height: 1.6; color: #ced4da;">
                                Hello, this is a test email sent from <strong>SentryBoot</strong> to confirm that your Hermes Email Bot integration is fully functional and credentials are correct.
                            </p>
                            
                            <div style="background-color: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 15px 20px; margin: 25px 0; border-radius: 4px;">
                                <strong style="color: #34d399; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Integration Status:</strong>
                                <div style="font-size: 18px; font-weight: 600; color: #ffffff; margin-top: 5px;">Active & Secure</div>
                            </div>
                            
                            <p style="font-size: 14px; line-height: 1.6; color: #ced4da;">
                                System: <strong>{comp_name}</strong><br>
                                Account: <strong>{username}</strong><br>
                                Version: <strong>v{__version__}</strong>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #12141a; padding: 25px 30px; text-align: center; border-top: 1px solid #2d3139; font-size: 12px; color: #6c757d;">
                            <p style="margin: 0 0 5px 0;">{__copyright__}</p>
                            <p style="margin: 0;">
                                Developed by <a href="{__website__}" style="color: #10b981; text-decoration: none; font-weight: 500;">{__author__}</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html_body
