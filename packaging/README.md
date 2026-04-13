# Packaging and Release (Windows)

This directory contains the release workflow for CtrlV on Windows: build portable with PyInstaller and build installer with Inno Setup.

## Source of truth

Packaging metadata comes from `app/version.py`:

- `APP_NAME`
- `PUBLISHER`
- `VERSION`

Build scripts pass these values into installer defines and artifact names.

## Prerequisites

- Windows 10/11 x64
- Python 3.12+
- `pip install -r requirements.txt`
- `pip install -r packaging/requirements-build.txt`
- Inno Setup 6 (`ISCC.exe`)

## Build commands (PowerShell)

```powershell
./packaging/scripts/clean.ps1
./packaging/scripts/build_portable.ps1
./packaging/scripts/build_installer.ps1
# or
./packaging/scripts/build_all.ps1
```

## Release outputs

```text
release/
  portable/
    CtrlV-<version>-portable/
  installer/
    CtrlV-Setup-<version>.exe
```

## Installer behavior

- Per-user install (`%LOCALAPPDATA%\Programs\CtrlV`)
- Start Menu shortcut
- Optional desktop shortcut
- Optional `Launch at Windows startup` task
- Optional `Launch CtrlV` at install finish
- Installer asks to close running CtrlV before file replacement

Autostart is intentionally single-mechanism only:

- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\CtrlV.lnk`
- shortcut args: `--startup`
- shortcut working dir: install folder

Runtime toggles and installer task both manage the same startup artifact.

## Uninstall behavior

Uninstall removes installed files and installer shortcuts, including `CtrlV.lnk` in user Startup folder.

User profile data (settings/logs/history) is preserved by default.

## Known limitations

- No auto-updater yet (manual reinstall/upgrade flow).
- No code-signing in this phase.
- No MSI/winget/scoop packaging in this phase.
