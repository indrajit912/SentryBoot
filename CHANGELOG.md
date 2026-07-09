# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-09

### Added
- First public release of **SentryBoot**.
- Fully-interactive Typer CLI supporting `init`, `start`, `status`, `test-email`, `config`, `logs`, and `version` commands.
- Secure configuration backend using Windows native Data Protection API (DPAPI) via `ctypes`.
- Cryptographic PBKDF2-HMAC-SHA256 hashing for system unlock passphrases (100,000 iterations).
- High-fidelity visual challenge prompt using `rich` featuring countdown timer, masked inputs, and keyboard buffer scanning via `msvcrt`.
- Thread-safe console control event interception via Windows `SetConsoleCtrlHandler` API to trigger alerts on window close or logoff events.
- Structured boot event logging supporting daily size limits and automatic file rotation.
- Hermes Email API integration with premium HTML templates for both setup testing and real-time security alerts.
