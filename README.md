# CtrlV

CtrlV is a Windows desktop clipboard utility built with Python and PySide6. It runs as a sidebar panel, tracks clipboard history, and stays accessible from the system tray.

The current project state is focused on a stable local desktop workflow and packaging for distribution to other users.

## Who this app is for

- users who copy/paste frequently and need quick access to recent clipboard items;
- users who prefer a docked sidebar instead of a full window application;
- developers/maintainers who want a small, readable PySide6 desktop codebase.

## User overview

CtrlV starts as a frameless sidebar window and monitors clipboard changes.

- Select an item in history and copy it back to clipboard.
- Hide/show the panel from the tray icon.
- Keep panel docked left/right or switch to floating mode.
- Use auto-hide and hover reveal for a compact desktop footprint.
- Collapse/expand the docked panel.
- Keep behavior preferences across restarts via persisted settings.

## Implemented features (current status)

- Clipboard monitoring via `QClipboard`
- Clipboard history list with duplicate prevention and item limit
- History item types: text, image, files, unknown fallback
- Sidebar panel UI
- Docking behavior (left/right) and floating mode
- Collapse/expand behavior
- Auto-hide/reveal behavior near screen edge
- Tray integration (toggle panel, clear history, quit, always-on-top, auto-hide)
- Settings persistence (`QSettings`) for sidebar/tray behavior
- Windows packaging layer:
  - PyInstaller spec (`onedir` portable build)
  - Inno Setup installer
  - PowerShell build scripts
  - Packaging documentation

## Limitations and not-yet-implemented items

This repository intentionally does **not** include the following yet:

- global hotkeys;
- full-text search over history;
- pinned/favorite items;
- persistent SQLite clipboard history database;
- auto-updater;
- telemetry/analytics;
- cloud sync;
- code signing;
- CI/CD release automation;
- Windows startup integration;
- alternative package channels (MSI/winget/scoop).

## Run from source (developer quick start)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

## Build and installation overview

Packaging tools live under `packaging/`.

### Build portable package

```powershell
./packaging/scripts/build_portable.ps1
```

Result:

- `release/portable/CtrlV-<version>-portable/`

### Build installer

```powershell
./packaging/scripts/build_installer.ps1
```

Result:

- `release/installer/CtrlV-Setup-<version>-x64.exe`

### Build full release pipeline

```powershell
./packaging/scripts/build_all.ps1
```

For detailed packaging flow, see `packaging/README.md`.

## Release artifacts (expected)

Example for version `0.1.0`:

- `release/portable/CtrlV-0.1.0-portable/`
- `release/installer/CtrlV-Setup-0.1.0-x64.exe`

## Project structure

```text
app/
  main.py
  bootstrap.py
  version.py
  core/
  services/
  ui/
  utils/
assets/
  icons/
packaging/
  pyinstaller/
  inno/
  scripts/
  templates/
```

## Versioning

Application name/publisher/version are defined in one place:

- `app/version.py`

Packaging scripts read this file to keep artifact names and installer metadata consistent.

## License status

Current repository license status is defined in `LICENSE`.
At this stage, no open-source license grant is provided yet.

## Changelog

Release notes are tracked in `CHANGELOG.md`.
