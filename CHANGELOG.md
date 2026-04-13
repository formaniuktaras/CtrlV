# Changelog

All notable changes to this project are documented in this file.

## [0.1.2] - 2026-04-13

### Changed
- Hardened autostart to a single canonical Startup-folder shortcut source (`CtrlV.lnk`) with strict validation of target path, arguments, and working directory.
- Made autostart enable/disable idempotent and duplicate-safe for known legacy shortcut variants.
- Improved startup flow so `--startup` launches tray-first and secondary autostart launches exit quietly without forcing sidebar activation.
- Improved runtime executable path resolution for packaged vs source runs (no current-working-directory dependency).
- Polished Inno Setup metadata/tasks/run behavior and standardized installer artifact naming to `CtrlV-Setup-<version>.exe`.
- Added installer close-running-app safeguards to reduce reinstall/upgrade mixed-state risks.
- Aligned product wording/behavior docs for installer, portable, startup, logs, and uninstall expectations.

## [0.1.1] - 2026-04-12

### Added
- Windows autostart service layer with enable/disable/status operations via per-user Startup shortcut.
- Tray menu toggle for autostart state, synchronized with actual system startup registration.
- Single-instance protection via Qt local socket signaling (second launch activates existing instance).
- Startup/login mode (`--startup`) and one-time first-run tray hint for clearer tray-first UX.

### Changed
- Hardened application shutdown lifecycle (settings flush + centralized cleanup).
- Installer now includes optional `Launch at Windows startup` task and removes startup shortcut on uninstall.

## [0.1.0] - 2026-04-12

### Added
- Initial public release packaging workflow for Windows.
- Portable PyInstaller distribution and Inno Setup installer pipeline.

### Changed
- Rewrote root README to reflect current implemented functionality.
- Standardized release artifact naming:
  - `CtrlV-<version>-portable`
  - `CtrlV-Setup-<version>-x64.exe`
- Improved packaging scripts output clarity and error handling.
- Cleaned up PyInstaller spec to focus on PySide6 runtime requirements.
- Updated packaging documentation for end-to-end release process.
