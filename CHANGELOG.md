# Changelog

All notable changes to this project are documented in this file.

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
