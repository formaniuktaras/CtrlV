# Changelog

All notable changes to this project are documented in this file.

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
