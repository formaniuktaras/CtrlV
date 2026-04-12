# CtrlV Packaging (Windows)

This folder contains production-oriented packaging assets for Windows 10/11:

- PyInstaller `onedir` portable build (primary distribution format).
- Inno Setup installer build based on portable output.
- PowerShell build scripts with predictable artifact layout.

## Structure

```text
packaging/
  README.md
  pyinstaller/
    ctrlv.spec
  inno/
    ctrlv_installer.iss
  scripts/
    _common.ps1
    clean.ps1
    build_portable.ps1
    build_installer.ps1
    build_all.ps1
  templates/
    portable_README.txt
```

## Prerequisites

- Windows 10/11 x64
- Python 3.12+
- Virtual environment with dependencies:
  - `pip install -r requirements.txt`
  - `pip install -r packaging/requirements-build.txt`
- Inno Setup 6 (for installer build):
  - Download: https://jrsoftware.org/isdl.php

## Version source of truth

Version is defined in a single place:

- `app/version.py` (`VERSION = "..."`)

Packaging scripts read this value and pass it into artifact names and installer metadata.

## Build commands

Run from repository root in PowerShell.

### Clean packaging outputs

```powershell
./packaging/scripts/clean.ps1
```

Removes:

- `build/`
- `dist/`
- `release/`

### Build portable (PyInstaller onedir)

```powershell
./packaging/scripts/build_portable.ps1
```

Outputs:

- `dist/CtrlV-portable/`
- `release/portable/CtrlV-portable-<version>/`

Portable directory contains:

- `CtrlV.exe`
- runtime files
- `VERSION.txt`
- `README.txt`

### Build installer (Inno Setup)

```powershell
./packaging/scripts/build_installer.ps1
```

Requires existing `dist/CtrlV-portable/CtrlV.exe`.

Outputs:

- `release/installer/CtrlV-setup-<version>-x64.exe`

### Build all

```powershell
./packaging/scripts/build_all.ps1
```

Pipeline:

1. Clean
2. Build portable
3. Build installer

## Installer behavior

- Installs to `{localappdata}\Programs\CtrlV` (per-user, no admin required).
- Creates Start Menu shortcut.
- Optional desktop shortcut.
- Registers uninstall entry.
- Offers "Launch CtrlV" after install.
- Does **not** remove user profile settings by default.

## Icon handling

Place icon at:

- `assets/icons/app.ico`

If missing, both portable and installer builds still work with default icons.
