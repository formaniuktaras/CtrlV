# CtrlV

CtrlV — lightweight clipboard manager for Windows with a docked sidebar and system tray control.
It keeps your recent copied items close at hand and helps you quickly copy any item back to the clipboard.

## Key Features

- Clipboard history for text, images, and file lists.
- Sidebar panel that docks to the left or right screen edge.
- Collapsed edge state to keep the panel out of the way.
- Auto-hide with reveal on mouse hover near the screen edge.
- System tray control for runtime actions and recovery.
- Launch at Windows startup (single canonical Startup shortcut with `--startup`).
- Single-instance behavior (second launch never creates a second tray icon).
- Rotating UTF-8 file logs for diagnostics.

## Installation

### Option 1 — Installer (recommended)

1. Download `CtrlV-Setup-<version>.exe`.
2. Run installer.
3. Optionally choose:
   - Desktop shortcut
   - Launch at Windows startup
4. Optionally launch CtrlV at the final installer step.

After install, CtrlV starts from Start Menu/Desktop and runs from `%LOCALAPPDATA%\Programs\CtrlV`.

### Option 2 — Portable

1. Download portable folder build.
2. Extract to any local folder.
3. Run `CtrlV.exe` directly.

Portable keeps manual workflow; installer gives cleaner OS integration.

## Startup and Tray Behavior

- Startup shortcut source of truth is:
  `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\CtrlV.lnk`
- CtrlV verifies autostart by target path + `--startup` args + working directory.
- Login autostart launches tray-first/minimized behavior (no aggressive full-window pop).
- Manual launch shows sidebar normally (unless you enabled start minimized setting).
- If CtrlV is already running, second launch exits; manual launch additionally asks running instance to show sidebar.

## Logs

CtrlV writes logs to:

- `%LOCALAPPDATA%\CtrlV\logs\ctrlv.log`

Use tray menu → **Open logs folder** for quick access.

## Recovery / Troubleshooting

- **Panel disappeared:** tray menu → **Reset panel position/state**.
- **App seems closed:** check system tray (X hides to tray by default).
- **Startup mismatch:** verify **Launch at startup** in tray/settings.
- **Second launch “does nothing”:** expected single-instance behavior.

## Uninstall behavior

Uninstall removes installed app files and installer-created shortcuts (including CtrlV startup shortcut).

Uninstall intentionally does **not** purge user profile data by default (settings/logs/history) for safer reinstall diagnostics.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

Useful launch arguments:

- `--startup` — autostart/login path (tray-first behavior).
- `--minimized` — manual minimized behavior test.

## Build / Packaging

- PyInstaller: portable onedir build.
- Inno Setup: per-user installer.
- Build scripts: `packaging/scripts/*.ps1`.
- Detailed notes: `packaging/README.md`.

## License

License terms are provided in `LICENSE`.
