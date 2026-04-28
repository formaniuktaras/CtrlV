# CtrlV Packaging (Windows)

This document covers technical packaging/release details for CtrlV.

## Prerequisites

- Windows 10/11 x64.
- Python 3.12+.
- Project dependencies:

```powershell
pip install -r requirements.txt
pip install -r packaging/requirements-build.txt
```

- Inno Setup 6 (`ISCC.exe`) installed and available from PATH or default Program Files location.

## Build commands

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File packaging/scripts/clean.ps1
powershell -ExecutionPolicy Bypass -File packaging/scripts/build_portable.ps1
powershell -ExecutionPolicy Bypass -File packaging/scripts/build_installer.ps1
```

Or single command:

```powershell
powershell -ExecutionPolicy Bypass -File packaging/scripts/build_all.ps1
```

## Output paths

Expected artifacts:

- `dist/CtrlV-portable/CtrlV.exe`
- `release/portable/CtrlV-{version}-portable/`
- `release/installer/CtrlV-Setup-{version}.exe`

Version/app metadata is read from `app/version.py` (`APP_NAME`, `PUBLISHER`, `VERSION`).

## build_all.ps1 workflow

`build_all.ps1` executes, in order:

1. `clean.ps1`
2. `build_portable.ps1`
3. `build_installer.ps1`

It stops on first failure and prints output folders on success.

## Installer behavior (Inno Setup)

Installer script: `packaging/inno/ctrlv_installer.iss`

Current behavior:

- Per-user install (`PrivilegesRequired=lowest`).
- Default install path: `%LOCALAPPDATA%\Programs\CtrlV`.
- Start Menu shortcut is always created.
- Desktop shortcut is always created.
- Startup shortcut is always created to `CtrlV.exe --startup` (can be disabled in app settings/tray).
- Final screen keeps `Launch CtrlV now` checked.
- Installer requests closing running CtrlV before replacing files.

If icon file `assets/icons/app.ico` is missing, build continues with a warning and default icon.

## Tooling error handling

- Missing PyInstaller: script fails with guidance to run:
  `pip install -r packaging/requirements-build.txt`
- Missing Inno Setup: script fails with guidance to install Inno Setup 6.

## Known limitations

- No code signing.
- No auto-updater.
- Windows-only packaging pipeline.
- Inno Setup 6 is required for installer builds.
