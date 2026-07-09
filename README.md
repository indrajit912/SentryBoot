# 🛡️ SentryBoot

SentryBoot is a production-quality, modular, and installable Python CLI security utility for Windows, macOS, and Linux. It acts as a boot-time authentication sentry that detects unauthorized access to your computer and dispatches real-time HTML alerts to your email using the **Hermes Email API** if verification is bypassed or interrupted.

Developer: **Indrajit Ghosh**  
Website: [https://indrajitghosh.onrender.com](https://indrajitghosh.onrender.com)  
License: **MIT**

---

## 📖 Table of Contents
1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [Hermes Email Bot Setup](#-hermes-email-bot-setup)
4. [Installation](#-installation)
5. [First-Time Initialization](#-first-time-initialization)
6. [Windows Configuration](#-windows-configuration)
   - [Scenario 1: Repository Clone + Virtual Environment](#scenario-1-repository-clone--virtual-environment)
   - [Scenario 2: Installation via pipx from Git](#scenario-2-installation-via-pipx-from-git)
   - [CLI & PowerShell Command-Line Management](#cli--powershell-command-line-management)
7. [Unix (Linux/macOS) Configuration](#-unix-linuxmacos-configuration)
   - [Installation from Source](#installation-from-source)
   - [Installation via pipx](#installation-via-pipx)
   - [Scheduling via XDG Autostart (Linux Desktop - Recommended)](#scheduling-via-xdg-autostart-linux-desktop---recommended)
   - [Scheduling via launchd (macOS - Recommended)](#scheduling-via-launchd-macos---recommended)
   - [Scheduling via systemd User Service & Timer](#scheduling-via-systemd-user-service--timer)
   - [Scheduling via cron](#scheduling-via-cron)
8. [CLI Command Reference](#-cli-command-reference)
9. [Security Architecture & Considerations](#-security-architecture--considerations)
10. [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🔍 Overview

When your computer boots up and you log in, SentryBoot triggers a professional terminal window displaying a **2-minute countdown**. 

```text
+-----------------------------------------------------------+
| 🛡️ SENTRYBOOT SECURITY SHIELD                             |
|                                                           |
| SYSTEM STATUS: LOCKDOWN                                   |
| Please enter the secret passphrase to unlock the terminal. |
| You have 2 minutes to authenticate.                       |
|                                                           |
| Time Remaining: 112s  ██████████████████░░░░░░░░░░░░      |
| Security Attempts Left: 3                                 |
|                                                           |
| Passphrase: *******                                       |
+-----------------------------------------------------------+
```

If the passphrase is correct, SentryBoot exits cleanly and grants access.  
If any of the following occur:
- **No passphrase is entered** within the 2-minute timeout,
- **An incorrect passphrase is entered** three times,
- **The terminal window is forcibly closed** (e.g. via clicking the 'X' button or Alt+F4),
- **The program is interrupted** (e.g. via Ctrl+C),

then SentryBoot immediately sends a structured HTML notification to your email via the Hermes API, detailing system diagnostics (timestamp, computer name, username, local/public IP, uptime).

---

## ✨ Key Features

- **Windows DPAPI Security**: Locally encrypts your Hermes API credentials on disk using the native Windows Data Protection API (DPAPI). Only your logged-in Windows user session can decrypt them.
- **Window Close Interception**: Registers a Win32 Console Control Handler (`SetConsoleCtrlHandler`) via `ctypes` to immediately email an alert if the console is shut down or logged off.
- **Secure Hashing**: Passphrase verified offline using **PBKDF2-HMAC-SHA256** with 100,000 iterations and a unique salt. Passphrases are never stored in plaintext.
- **Anti-Garble Real-Time Input**: Standard input is intercepted character-by-character using the native `msvcrt` keyboard buffer, letting us display a real-time visual progress countdown and securely mask inputs as asterisks (`*`) without line corruption.
- **Boot Diagnostics**: Automatically gathers details like local IP, public IP, OS version, and exact boot uptime (queried via Win32 `GetTickCount64`).
- **Rotational Logging**: Logs events to a structured log file in the user's home directory with automatic size limits.
- **HTML-Only Notifications**: Optimized for modern email clients, utilizing clean CSS styling, progress status alerts, and diagnostic tables without fallback plain-text leakage.
- **Intruder Photo Capture**: Integrates with system webcams (using `opencv-python`) to automatically take a snapshot of the intruder upon unauthenticated system access, saving it locally under `~/.sentryboot/snapshots/` and embedding it directly into the HTML email alert.
- **Offline Alert Caching**: Encapsulates threat alert details in a local JSON cache if internet is missing or the email API fails, triggering a concurrent background daemon thread on startup to auto-sync them once the connection returns.
- **Intrusion Forensic Aggregation**: Automatically dumps running processes (`processes.txt`) and active socket connections (`network_connections.txt`) using native shell tools on failure, adding them to the alert email as file attachments.
- **Native Session Auto-Locking**: Protects the computer by calling native OS screen locking commands (Win32 `LockWorkStation` on Windows) immediately after registering the breach, locking the computer console from the intruder.

---

## ✉️ Hermes Email Bot Setup

SentryBoot uses your existing **Hermes Email API** bot to send alert notifications.

### How to Create a Hermes Bot:
1. Open your browser and navigate to the Hermes Bot service: **[https://hermesbot.pythonanywhere.com](https://hermesbot.pythonanywhere.com)**
2. Register an account or log in.
3. Click on **Create Bot** and select the **Email Bot** type.
4. Note your newly created:
   - **Hermes API Key** (typically a long token starting with Bearer authorization permissions)
   - **Hermes Emailbot ID**
5. Keep these credentials safe; you will need them during initialization.

---

## ⚙️ Installation

We recommend installing SentryBoot globally using `pipx` so it runs inside an isolated virtual environment but remains executable from any terminal.

### 1. Install via pipx (Recommended)
Make sure you have `pipx` installed. If not, install it via:
```powershell
pip install pipx
pipx ensurepath
```
Then, install SentryBoot directly from GitHub:
```powershell
pipx install git+https://github.com/ghostrix/sentryboot
```

### 2. Manual Installation (For Development)
Clone the repository and install it in editable mode:
```powershell
git clone https://github.com/ghostrix/sentryboot.git
cd sentryboot
pip install -e .
```

---

## 🚀 First-Time Initialization

To configure SentryBoot, run the `init` command:
```powershell
sentryboot init
```

> [!IMPORTANT]
> **Clean Initialization**: If SentryBoot was previously initialized, running `sentryboot init` will automatically detect and purge all existing local data. This includes configuration files, log files (`boot.log`), and captured snapshots. It then rebuilds the directory structure and prompts you for a fresh setup. The process is fully idempotent and safe, removing only SentryBoot-managed files.

This interactive wizard will walk you through the setup:
1. It requests the Hermes API Base URL (defaults to `https://hermesbot.pythonanywhere.com`).
2. It prompts you for your **Hermes API Key** (securely hidden as you type).
3. It asks for your **Hermes Email Bot ID**.
4. It asks for your **Recipient Email Address** (where security alerts will be sent).
5. It requests you to create a new **Secret Passphrase** and confirm it.
6. Finally, it encrypts the credentials using Windows DPAPI, saves the config to `~/.sentryboot/config.json`, and **sends a test verification email** to your address.

---

## 📸 Webcam Snapshot Feature

SentryBoot includes a webcam snapshot capability to capture a photo of the intruder upon unauthorized system access:

### ⚙️ How It Works
1. When an intrusion event is detected (timeout, wrong passphrase, or closed window):
   - SentryBoot queries the system to detect if an active, usable webcam is present.
   - If a camera is available, SentryBoot opens it, performs a brief 0.5s auto-exposure warm-up, and captures a single frame.
   - The snapshot is saved to `~/.sentryboot/snapshots/` using a unique filename containing a timestamp and a UUID (e.g., `intruder_20260709_193012_a3b2c1d0.jpg`).
   - The captured image is converted to a base64 Data URI and embedded directly inside the HTML email alert.
   - The absolute path to the local file is stored in `boot.log` under the `Snapshot:` key.
2. If no webcam is available, the device is busy/locked by another application, or camera permission is denied:
   - SentryBoot logs a warning to `boot.log` (stating `Snapshot: None`).
   - The intrusion response continues normally without failing, and the Hermes email alert is dispatched with a warning that the snapshot was unavailable.

### 🛡️ Platform-Specific Camera Permissions
* **Windows**: Works out of the box. Ensure that "Camera access" is toggled on under **Settings > Privacy & security > Camera**, and that "Let desktop apps access your camera" is enabled.
* **macOS**: When running SentryBoot for the first time, macOS will prompt you for camera access. Make sure to grant permission. You can manage this under **System Settings > Privacy & Security > Camera** (ensure Terminal/Console app is checked).
* **Linux**: Ensure your user belongs to the `video` group to access camera device nodes (e.g., `/dev/video0`). Run `sudo usermod -aG video $USER` and restart your session if permission is denied.

---

## 💻 Windows Configuration

Windows uses **Task Scheduler** to automate boot-time execution. Follow the instructions below based on how you installed the application.

### Scenario 1: Repository Clone + Virtual Environment

Assume the user performs the following installation steps:
1. Clones the repository to `C:\Users\<YourUsername>\Documents\hello_world\sentryboot`
2. Changes into the project directory:
   ```cmd
   cd C:\Users\indra\Documents\hello_world\sentryboot
   ```
3. Creates a virtual environment named `env`:
   ```cmd
   python -m venv env
   ```
4. Activates the virtual environment and installs the application:
   ```cmd
   .\env\Scripts\activate
   pip install .
   ```

#### 🔍 Locating the Executable and Interpreter
Within this virtual environment layout, the relevant executables are:
* **sentryboot Executable**: `C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe`
* **Python Interpreter**: `C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\python.exe`

#### 📅 Task Scheduler Graphical Configuration
1. Open the Start menu, search for **Task Scheduler**, and run it.
2. Click **Create Task** in the right Actions pane (do not click *Create Basic Task*).
3. **General Tab**:
   - **Name**: `SentryBoot`
   - **Security Options**: Select **"Run only when user is logged on"** (CRITICAL: Selecting "run whether user is logged on or not" executes SentryBoot in background Session 0. The CLI window will be completely invisible, causing the challenge to time out and send an alert).
   - **Privilege Level**: Check **"Run with highest privileges"** (Runs the terminal as Administrator, making it harder for standard users to close it without authorization).
4. **Triggers Tab**:
   - Click **New...**
   - Begin the task: **"At log on"**
   - Under Settings: Select **"Any user"** or **"Specific user"** (your account).
   - Advanced Settings: Check **"Delay task for:"** and select or type **"10 seconds"** (CRITICAL: Delaying the task ensures Windows has time to establish Wi-Fi/network connectivity before the script runs, avoiding offline request failures).
   - Click **OK**.
5. **Actions Tab**:
   - Click **New...**
   - Action: **"Start a program"**
   - Choose one of the following shell options to launch the interactive prompt:
     
     **Option A: Using Command Prompt (`cmd.exe`)**
     - **Program/script**: `cmd.exe`
     - **Add arguments (optional)**: `/c start /wait "SentryBoot Guard" "C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe" start`
     - **Start in (optional)**: `C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts`
     
     **Option B: Using Windows PowerShell (`powershell.exe`)**
     - **Program/script**: `powershell.exe`
     - **Add arguments (optional)**: `-NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe' start"`
     - **Start in (optional)**: `C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts`
     
     **Option C: Using PowerShell 7 Core (`pwsh.exe`)**
     - **Program/script**: `pwsh.exe`
     - **Add arguments (optional)**: `-NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe' start"`
     - **Start in (optional)**: `C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts`
     
     **Option D: Using Windows Terminal (`wt.exe`) hosting PowerShell 7**
     - **Program/script**: `wt.exe`
     - **Add arguments (optional)**: `pwsh.exe -NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe' start"`
     - **Start in (optional)**: `C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts`
     
   - Click **OK**.
6. **Conditions Tab**:
   - Uncheck **"Start the task only if the computer is on AC power"** (Ensures SentryBoot runs on laptops when unplugged).
   - Uncheck **"Stop if the computer switches to battery power"**.
7. **Settings Tab**:
   - Uncheck **"Stop the task if it runs longer than"** (Otherwise, Task Scheduler will kill the task after 3 days).
   - Click **OK** to save the task.

> [!TIP]
> **Maximized / Fullscreen Mode in Task Scheduler**:
> To force the security challenge window to open maximized or in fullscreen mode at startup, modify the **Add arguments** field:
> * **Option A (Command Prompt - `cmd.exe`)**: Add `/max` to open maximized.
>   `cmd.exe /c start "" /max /wait "C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe" start`
> * **Option B/C (PowerShell - `powershell.exe`/`pwsh.exe`)**: Insert the `-WindowStyle Maximized` parameter.
>   `pwsh.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Maximized -Command "& 'C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe' start"`
> * **Option D (Windows Terminal - `wt.exe`)**: Use the `-M` (Maximized) or `-F` (Fullscreen) switches directly at the beginning of the arguments list.
>   `wt.exe -F pwsh.exe -NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe' start"`

---

### Scenario 2: Installation via `pipx` from Git

If you installed SentryBoot globally via `pipx`:
```powershell
pipx install git+https://github.com/ghostrix/sentryboot
```

#### 🔍 Locating the pipx Executable
In `pipx`, executables are stored in a centralized directory. To find the path, open a command prompt and run:
```cmd
where sentryboot
```
Typically, this resolves to:
`C:\Users\<YourUsername>\.local\bin\sentryboot.exe`

#### 📅 Task Scheduler Configuration for pipx
The configuration is identical to Scenario 1, except for the **Actions** tab values:

**Option A: Using Command Prompt (`cmd.exe`)**
* **Program/script**: `cmd.exe`
* **Add arguments (optional)**: `/c start /wait "SentryBoot Guard" "C:\Users\<YourUsername>\.local\bin\sentryboot.exe" start`
* **Start in (optional)**: `C:\Users\<YourUsername>\.local\bin`

**Option B: Using Windows PowerShell (`powershell.exe`)**
* **Program/script**: `powershell.exe`
* **Add arguments (optional)**: `-NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\<YourUsername>\.local\bin\sentryboot.exe' start"`
* **Start in (optional)**: `C:\Users\<YourUsername>\.local\bin`

**Option C: Using PowerShell 7 Core (`pwsh.exe`)**
* **Program/script**: `pwsh.exe`
* **Add arguments (optional)**: `-NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\<YourUsername>\.local\bin\sentryboot.exe' start"`
* **Start in (optional)**: `C:\Users\<YourUsername>\.local\bin`

**Option D: Using Windows Terminal (`wt.exe`) hosting PowerShell 7**
* **Program/script**: `wt.exe`
* **Add arguments (optional)**: `pwsh.exe -NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\<YourUsername>\.local\bin\sentryboot.exe' start"`
* **Start in (optional)**: `C:\Users\<YourUsername>\.local\bin`

> [!TIP]
> **Maximized / Fullscreen Mode in Task Scheduler**:
> To force the security challenge window to open maximized or in fullscreen mode at startup, modify the **Add arguments** field:
> * **Option A (Command Prompt - `cmd.exe`)**: Add `/max` to open maximized.
>   `cmd.exe /c start "" /max /wait "C:\Users\<YourUsername>\.local\bin\sentryboot.exe" start`
> * **Option B/C (PowerShell - `powershell.exe`/`pwsh.exe`)**: Insert the `-WindowStyle Maximized` parameter.
>   `pwsh.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Maximized -Command "& 'C:\Users\<YourUsername>\.local\bin\sentryboot.exe' start"`
> * **Option D (Windows Terminal - `wt.exe`)**: Use the `-M` (Maximized) or `-F` (Fullscreen) switches directly at the beginning of the arguments list.
>   `wt.exe -F pwsh.exe -NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\<YourUsername>\.local\bin\sentryboot.exe' start"`

#### 🔄 Key Differences between venv and pipx
* **Scope**: Virtual environment installation requires targeting the project-specific `env/Scripts` path. `pipx` isolates the environment in a global app directory and drops a shim in `%USERPROFILE%\.local\bin\`.
* **Path Resilience**: If the repository clone directory is deleted or moved, a virtual environment task will break. A `pipx` installation remains fully functional as it is managed in the user's local application data folder.

---

### CLI & PowerShell Command-Line Management

Instead of using the graphical Task Scheduler, you can fully manage the scheduled tasks using the Windows Command Prompt (`schtasks`) or PowerShell.

#### 1. Creating the Task
* **Using `schtasks` (Command Prompt as Admin)**:
  ```cmd
  schtasks /create /tn "SentryBoot" /tr "cmd.exe /c start /wait \"SentryBoot Guard\" \"C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe\" start" /sc onlogon /rl highest /f
  ```
* **Using PowerShell (As Admin)**:
  ```powershell
  $Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c start /wait `"SentryBoot Guard`" `"C:\Users\indra\Documents\hello_world\sentryboot\env\Scripts\sentryboot.exe`" start"
  $Trigger = New-ScheduledTaskTrigger -AtLogon
  $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
  Register-ScheduledTask -TaskName "SentryBoot" -Trigger $Trigger -Action $Action -Settings $Settings -RunLevel Highest -Force
  ```

#### 2. Listing and Querying Tasks
* **Using `schtasks`**:
  ```cmd
  schtasks /query /fo TABLE | findstr /i "SentryBoot"
  ```
* **Using PowerShell**:
  ```powershell
  Get-ScheduledTask -TaskName "SentryBoot"
  ```

#### 3. Inspecting Task Details
* **Using `schtasks`**:
  ```cmd
  schtasks /query /tn "SentryBoot" /v /fo LIST
  ```
* **Using PowerShell**:
  ```powershell
  Get-ScheduledTask -TaskName "SentryBoot" | Get-ScheduledTaskInfo
  ```

#### 4. Running the Task Manually (Testing)
* **Using `schtasks`**:
  ```cmd
  schtasks /run /tn "SentryBoot"
  ```
* **Using PowerShell**:
  ```powershell
  Start-ScheduledTask -TaskName "SentryBoot"
  ```

#### 5. Viewing Task Execution History and Logs
Scheduled task executions are recorded in the Windows Event Log under:  
`Microsoft-Windows-TaskScheduler/Operational` (Event ID 100 indicates start, 102 indicates success, 201 indicates completion).

* **PowerShell query to tail task logs**:
  ```powershell
  Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" | Where-Object {$_.Message -like "*SentryBoot*"} | Select-Object -First 10 | Format-Table TimeCreated, Id, Message -Wrap
  ```

#### 6. Deleting the Task
* **Using `schtasks`**:
  ```cmd
  schtasks /delete /tn "SentryBoot" /f
  ```
* **Using PowerShell**:
  ```powershell
  Unregister-ScheduledTask -TaskName "SentryBoot" -Confirm:$false
  ```

---

## 🐧 Unix (Linux/macOS) Configuration

Spawning an interactive CLI window on Unix-like operating systems during boot or login requires configuring the target display server (X11/Wayland) or launching a terminal emulator.

### Installation from Source
1. Clone and navigate to the repository:
   ```bash
   git clone https://github.com/ghostrix/sentryboot.git
   cd sentryboot
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
3. Install the application:
   ```bash
   pip install .
   ```
The executable is located at `CWD/env/bin/sentryboot`.

### Installation via `pipx`
Install globally:
```bash
pipx install git+https://github.com/ghostrix/sentryboot
```
Verify the installation path:
```bash
which sentryboot
```
Typically resolves to `~/.local/bin/sentryboot` on Linux or `/usr/local/bin/sentryboot` on macOS.

---

### Scheduling via XDG Autostart (Linux Desktop - Recommended)

For Linux users running a graphical desktop environment (GNOME, KDE, XFCE), the most reliable way to trigger an interactive SentryBoot terminal window upon login is via an XDG Autostart Entry. This avoids X11 display session authorization issues.

1. Create the autostart directory if it does not exist:
   ```bash
   mkdir -p ~/.config/autostart
   ```
2. Create a desktop entry file at `~/.config/autostart/sentryboot.desktop`:
   ```ini
   [Desktop Entry]
   Type=Application
   Name=SentryBoot Guard
   Comment=Boot-time security authentication challenge
   Exec=sentryboot start
   Terminal=true
   Categories=System;Security;
   RunAtStartup=true
   ```
3. Mark the file as executable:
   ```bash
   chmod +x ~/.config/autostart/sentryboot.desktop
   ```
When logging into your Linux desktop, your default system terminal will automatically launch SentryBoot.

---

### Scheduling via `launchd` (macOS - Recommended)

On macOS, `launchd` is the native service management framework. We can configure a Launch Agent that executes upon graphical login and spawns a visible Terminal shell running SentryBoot.

1. Create a Launch Agent configuration file at `~/Library/LaunchAgents/com.sentryboot.plist`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.sentryboot</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/bin/open</string>
           <string>-a</string>
           <string>Terminal</string>
           <string>/usr/local/bin/sentryboot</string>
           <string>start</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>LimitLoadToSessionType</key>
       <string>Aqua</string>
   </dict>
   </plist>
   ```
   *(Note: Ensure `/usr/local/bin/sentryboot` matches your actual installation path. If using a virtual environment, substitute it with the absolute path to your `env/bin/sentryboot` executable).*

2. Load the Launch Agent:
   ```bash
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.sentryboot.plist
   ```
   *(Legacy command: `launchctl load ~/Library/LaunchAgents/com.sentryboot.plist`)*

3. **Verification**:
   - Manually trigger: `launchctl kickstart -p gui/$(id -u)/com.sentryboot`
   - Unload/Disable: `launchctl bootout gui/$(id -u)/com.sentryboot`

---

### Scheduling via `systemd` User Service & Timer

If you want to manage SentryBoot as a user-level service on Linux systemd distributions, follow these steps.

1. Create a service file at `~/.config/systemd/user/sentryboot.service`:
   ```ini
   [Unit]
   Description=SentryBoot Lock Screen Authentication
   After=graphical-session.target

   [Service]
   Type=simple
   Environment=DISPLAY=:0
   ExecStart=/usr/bin/xterm -hold -e "$HOME/.local/bin/sentryboot start"
   Restart=no

   [Install]
   WantedBy=graphical-session.target
   ```
   *(Note: Using terminal wrappers like `xterm -hold -e` or `gnome-terminal --` is required to bind SentryBoot to a visible graphical window).*

2. Create a systemd timer file at `~/.config/systemd/user/sentryboot.timer` to delay execution slightly:
   ```ini
   [Unit]
   Description=Run SentryBoot 10s after Graphical Login

   [Timer]
   OnStartupSec=10
   OnActiveSec=10
   Unit=sentryboot.service

   [Install]
   WantedBy=timers.target
   ```

3. Reload systemd daemon and activate the timer:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now sentryboot.timer
   ```

4. **Monitoring and Management**:
   - View scheduled timers: `systemctl --user list-timers`
   - Manually run task: `systemctl --user start sentryboot.service`
   - Read systemd logs: `journalctl --user -u sentryboot.service -n 50`
   - Disable/Remove task: `systemctl --user disable --now sentryboot.timer`

---

### Scheduling via `cron`

`cron` is a fallback option. Since cron runs in the background without graphical terminal bindings, you must explicitly declare the target `DISPLAY` environment and trigger a GUI terminal emulator.

1. Edit your user crontab:
   ```bash
   crontab -e
   ```
2. Append the following entry (adjust executable paths accordingly):
   ```text
   @reboot SLEEP 10 && DISPLAY=:0 /usr/bin/xterm -e /usr/local/bin/sentryboot start
   ```
3. Save and close.
4. **Management**:
   - List cron jobs: `crontab -l`
   - Remove cron jobs: `crontab -r`

---

## 💻 CLI Command Reference

### `sentryboot init`
Initializes the configuration parameters (including the default challenge timeout in minutes), encrypts keys via DPAPI, and sends a validation HTML test email.

### `sentryboot update-secrets`
Securely updates the lock challenge passphrase, Hermes API Key, Emailbot ID, and default challenge timeout. To prevent unauthorized modifications, SentryBoot prompts you to verify your current passphrase before changes are allowed. Leave inputs blank to keep their current value.

### `sentryboot start`
Runs the unauthenticated countdown challenge. Uses the configured default timeout (in minutes) if no arguments are specified. You can temporarily override it with the `--timeout` option (specified in seconds):
```powershell
sentryboot start --timeout 60
```

### `sentryboot status`
Validates initialization states and outputs active directory paths.

### `sentryboot test-email`
Triggers an immediate test email to check integration latency.

### `sentryboot config`
Prints masked configurations. API keys and hashed salts are never revealed to stdout.

### `sentryboot logs`
Tails entries of `boot.log`. Supports `--lines` constraints:
```powershell
sentryboot logs --lines 20
```

### `sentryboot version`
Prints version and copyright structures.

---

## 🔒 Security Architecture & Considerations

### 1. Safe Configuration Storage (DPAPI)
Config keys (specifically the Hermes API Key) are stored in `~/.sentryboot/config.json` encrypted using Windows **DPAPI**. The OS handles key management transparently, binding encryption specifically to your local Windows user security context. Other local users or guest accounts cannot decrypt your files.

### 2. Abrupt Termination Interception
If an intruder tries to bypass the lock screen by clicking the **'X' close button** on the console or forcing a user logoff, Windows sends a `CTRL_CLOSE_EVENT` to the process. SentryBoot traps this event natively via a registered console control handler, immediately dispatches the Hermes API request, and writes it to the local log file before letting the process exit.

### 3. User-Space Limitations
> [!WARNING]
> Because SentryBoot runs as an application in user space, a sophisticated attacker with physical computer access and Administrative privileges could bypass it:
> - By terminating the process using Task Manager or Process Hacker (which issues a `TerminateProcess` / `SIGKILL` event that user-space software cannot trap).
> - By disabling the Windows Task Scheduler entry.
> - By booting from an external Linux Live USB.
>
> **SentryBoot is designed as a secure audit log and real-time alert sentry, not a replacement for full disk encryption.** For complete security, we strongly recommend combining SentryBoot with **Windows BitLocker Full Disk Encryption** and a strong BIOS/UEFI password.

### 4. Logging & Failure Recovery
Logs are stored in `~/.sentryboot/boot.log` with a custom-built format using date formatting compatible with your requested template: `Mmm dd, YY HH:mm:ss AM/PM` (e.g. `Jul 09, 26 06:42:13 PM`).
In the event that the internet is offline during a boot alert, the application logs the failure locally, recording all diagnostics and exception traces, ensuring you have an offline audit trail when you log back in.

---

## ❓ Troubleshooting & FAQ

### Q: The console window popped up but immediately closed, and I got an alert email!
**A:** This usually happens if SentryBoot was not initialized correctly, or the configuration file was corrupted. Run `sentryboot status` to check if configuration loading succeeds. If it fails, run `sentryboot init` to reconfigure.

### Q: Why does the scheduler command require `cmd.exe /c start /wait`?
**A:** Windows Task Scheduler executes programs in the background by default. By wrapping the call inside `cmd.exe /c start /wait`, we force Windows to launch a visible console shell window that prompts you for input.

### Q: What happens if my computer is offline during boot?
**A:** SentryBoot will attempt to send the email alert. Since the network is offline, the Hermes API request will timeout. The app logs this event as `Alert Failed` in `boot.log` along with the diagnostics, providing an offline audit record.

### Q: How do I uninstall SentryBoot?
1. Open Task Scheduler and delete the `SentryBoot` task.
2. Uninstall the package via pipx:
   ```powershell
   pipx uninstall sentryboot
   ```
3. Remove the local configuration directory:
   ```powershell
   Remove-Item -Recurse -Force ~/.sentryboot
   ```
