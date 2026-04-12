# CtrlV

CtrlV — lightweight clipboard manager for Windows with a docked sidebar and system tray control.
It keeps your recent copied items close at hand and helps you quickly copy any item back to the clipboard.

## Key Features

- Clipboard history for text, images, and file lists.
- Sidebar panel that docks to the left or right screen edge.
- Collapsed edge state to keep the panel out of the way.
- Auto-hide with reveal on mouse hover near the screen edge.
- System tray control for quick show/hide and app actions.
- Launch at Windows startup (toggle from tray menu).
- Restore copied items back to the clipboard in one action.
- Single-instance behavior (opening CtrlV again focuses the running app).

## How It Works (UX)

CtrlV is primarily a tray app.

- After launch, CtrlV runs in the system tray and manages a sidebar panel.
- It is not a traditional “open once, keep centered window” desktop app.
- You can open the sidebar by:
  - clicking the tray icon;
  - moving the mouse to the docked edge (when auto-hide is enabled).
- Closing the sidebar window does not terminate CtrlV; it hides to tray.
- To fully exit, use **Quit** from the tray menu.
- If started with startup mode, CtrlV opens minimized to tray and waits for interaction.

## Screenshots

This repository does not include final product screenshots yet.
When screenshots are added, this section will show:

- Sidebar in expanded state with clipboard history.
- Sidebar in collapsed edge state.
- System tray context menu with controls.

## Installation

### Option 1 — Installer

1. Download the latest `CtrlV-Setup-<version>-x64.exe` from releases.
2. Run the installer and complete setup.
3. Start CtrlV from the Start Menu or desktop shortcut.
4. After launch, look for the CtrlV icon in the system tray.

### Option 2 — Portable

1. Download the portable archive/folder build.
2. Extract it to any local folder.
3. Run the CtrlV executable.
4. CtrlV starts and becomes available from the tray.

## Basic Usage

1. Copy any text, image, or files in Windows as usual (`Ctrl+C`).
2. Open CtrlV sidebar from tray click or edge hover reveal.
3. Select an item in history.
4. Click **Copy selected again** (or double-click the item).
5. Paste it in your target app (`Ctrl+V`).

Auto-hide behavior:

- With **Auto-hide** enabled, the sidebar can collapse to a thin edge strip.
- Hover near the docked edge to reveal it.
- Disable **Auto-hide** in tray menu if you prefer a stable expanded panel.

## Settings / Control

Most runtime controls are available from the tray menu:

- **Show sidebar / Hide sidebar**
- **Always on top** toggle
- **Auto-hide** toggle
- **Launch at Windows startup** toggle
- **Clear history**
- **Quit**

CtrlV also remembers key UI preferences between launches:

- dock side (left/right),
- panel size and position,
- collapsed/expanded state,
- auto-hide and always-on-top state.

## Troubleshooting

- **Sidebar does not open:** check that CtrlV is running in the system tray, then click the tray icon.
- **App seems “closed” after pressing X:** this is expected; CtrlV hides to tray. Use tray icon to reopen.
- **Does not start with Windows:** open tray menu and verify **Launch at Windows startup** is enabled.
- **Second launch does nothing:** CtrlV allows only one running instance; interact with the existing tray app.
- **Need logs for debugging:** current logging is console/stdout-based in runtime; no dedicated log file is configured by default.

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

Main packaging assets:

- `packaging/pyinstaller/ctrlv.spec`
- `packaging/inno/ctrlv_installer.iss`
- `packaging/scripts/build_portable.ps1`
- `packaging/scripts/build_installer.ps1`
- `packaging/scripts/build_all.ps1`

Detailed packaging notes are available in `packaging/README.md`.

## Project Structure

```text
app/          # application source code
  core/       # clipboard parsing, models, history storage
  services/   # tray, autostart, app lifecycle, settings
  ui/         # main window, sidebar behavior, panel controller
  utils/      # helpers and logging setup
assets/       # icons and static resources
packaging/    # PyInstaller, Inno Setup, release scripts
```

## Current Status

Implemented:

- system tray lifecycle and menu controls,
- docked sidebar panel (left/right),
- collapsed edge mode and hover reveal,
- clipboard history with restore-to-clipboard action,
- launch at Windows startup toggle,
- persisted UI/tray settings,
- single-instance protection.

Not implemented yet:

- history search,
- pinned/favorite items,
- global hotkeys,
- persistent history database,
- auto-updater.

## License

License terms are provided in `LICENSE`.
