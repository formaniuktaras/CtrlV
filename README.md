# CtrlV

CtrlV — lightweight clipboard manager for Windows with a docked sidebar and system tray control.
It keeps your recent copied items close at hand and helps you quickly copy any item back to the clipboard.

## Key Features

- Clipboard history for text, images, and file lists.
- Sidebar panel that docks to the left or right screen edge.
- Collapsed edge state to keep the panel out of the way.
- Auto-hide with reveal on mouse hover near the screen edge.
- System tray control for runtime actions and recovery.
- Launch at Windows startup (shortcut with `--startup`).
- Single-instance behavior (opening CtrlV again focuses the running app).
- Rotating UTF-8 file logs for diagnostics.

## Tray Menu

- Show sidebar / Hide sidebar
- Settings...
- Always on top
- Auto-hide
- Launch at startup
- Reset panel position/state
- Open logs folder
- Clear history
- Quit

All checkable tray items stay synchronized with Settings window state.

## Logging

CtrlV writes logs to a user-specific app data path (not current working directory):

- `%LOCALAPPDATA%\CtrlV\logs\ctrlv.log`

Log file uses rotation (`ctrlv.log` + backups) and includes startup, shutdown, tray/actions, autostart updates, recovery actions, single-instance events, and unhandled exceptions.

## Installation

### Option 1 — Installer (recommended)

1. Download the latest `CtrlV-Setup-<version>-x64.exe` from releases.
2. Run the installer and complete setup.
3. Start CtrlV from Start Menu or desktop shortcut.

Why installer is better for most users:

- predictable install path and shortcuts;
- cleaner uninstall flow;
- easier first-run onboarding and startup integration.

### Option 2 — Portable

1. Download the portable archive/folder build.
2. Extract it to any local folder.
3. Run the CtrlV executable.

Portable is best for advanced/manual workflows.

## Troubleshooting

- **App “doesn't open”:** check system tray first. CtrlV may already be running hidden.
- **Second launch does nothing:** single-instance mode sends focus/show request to existing instance.
- **Sidebar disappeared or moved off-screen:** use **Reset panel position/state** from tray menu or Settings → Advanced.
- **Startup behavior is wrong:** verify **Launch at startup** and **Start minimized to tray** in Settings.
- **Need diagnostics:** open tray menu → **Open logs folder** and inspect `ctrlv.log`.

## Development

Run from source (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

Useful launch arguments:

- `--startup` — start minimized to tray (used by autostart shortcut).
- `--minimized` — start minimized behavior for manual testing.

## Build / Packaging

CtrlV uses:

- **PyInstaller** for Windows executable packaging.
- **Inno Setup** for installer creation.
- **PowerShell scripts** for repeatable build steps.

Detailed packaging notes: `packaging/README.md`.

## License

License terms are provided in `LICENSE`.
