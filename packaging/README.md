# Packaging and Release (Windows)

This directory contains the release workflow for CtrlV on Windows: building a portable package with PyInstaller and creating a user installer with Inno Setup.

## Scope

The packaging layer is responsible for:

- producing release artifacts for end users;
- keeping artifact names/versioning consistent;
- using one version source (`app/version.py`);
- preserving a predictable output layout under `release/`.

## Prerequisites

- Windows 10/11 x64
- Python 3.12+
- Project dependencies installed:

```powershell
pip install -r requirements.txt
pip install -r packaging/requirements-build.txt
```

- Inno Setup 6 installed for installer builds (`ISCC.exe` in PATH or default Program Files location)

## Source of truth for name/version

Packaging reads metadata from `app/version.py`:

- `APP_NAME`
- `PUBLISHER`
- `VERSION`

Scripts pass these values into PyInstaller and Inno Setup build steps.

## Build commands

Run from repository root in PowerShell.

### 1) Clean previous outputs

```powershell
./packaging/scripts/clean.ps1
```

### 2) Build portable package

```powershell
./packaging/scripts/build_portable.ps1
```

Produces:

- `dist/CtrlV-portable/` (PyInstaller output)
- `release/portable/CtrlV-<version>-portable/` (release-ready copy)

### 3) Build installer

```powershell
./packaging/scripts/build_installer.ps1
```

Requires `dist/CtrlV-portable/CtrlV.exe` from the portable step.

Produces:

- `release/installer/CtrlV-Setup-<version>-x64.exe`

### 4) Run full pipeline

```powershell
./packaging/scripts/build_all.ps1
```

Runs `clean -> build_portable -> build_installer`.

## Release output layout

```text
release/
  portable/
    CtrlV-<version>-portable/
      CtrlV.exe
      README.txt
      VERSION.txt
      ...runtime files...
  installer/
    CtrlV-Setup-<version>-x64.exe
```

## Installer behavior

The installer is per-user and does not require admin privileges.

- Default install directory: `%LOCALAPPDATA%\Programs\CtrlV`
- Start Menu shortcut: yes
- Optional desktop shortcut: yes
- Uninstall entry: yes
- Launch app after install: optional checkbox
- User settings cleanup on uninstall: not performed by default

## Icon wiring

Place app icon at:

- `assets/icons/app.ico`

If this file exists, both PyInstaller and Inno Setup use it automatically.
If it is missing, builds still succeed with default icons.
