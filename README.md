# CtrlV

CtrlV is a Windows clipboard manager with a docked sidebar, tray control, and a fast restore/paste workflow for previously copied items.

## What CtrlV does

CtrlV keeps a local clipboard history and lets you reuse old clipboard content without leaving your current task.

- Tracks clipboard history for text, images, and file lists.
- Lets you select an old item and copy it back to the clipboard.
- Can auto-paste **text** items into the previously active external window.
- Runs in the system tray and supports show/hide control from tray.

## Key Features

- Clipboard history for text/images/files.
- Docked sidebar panel.
- Auto-hide with hover reveal.
- System tray control.
- Copy-only and auto-paste workflows.
- Startup launch support.
- Single-instance behavior.
- Logs and recovery actions.

## User Actions

| Action | Result |
| --- | --- |
| Single click item | Selects item only |
| Double click text item | Copies and auto-pastes into previous window |
| Double click image/file item | Copies only, user pastes manually |
| Copy to clipboard | Copies selected item only |
| Enter on selected item | Same as double click |
| Delete | Deletes selected unpinned item |
| Pin/unpin | Keeps item available in Pinned |
| Clear history | Clears history, preserves pinned items |
| Tray left click | Shows/hides sidebar |
| Window close X | Hides to tray |
| Tray Quit | Exits CtrlV |

## Auto-paste behavior

- Auto-paste runs only for **text** items.
- CtrlV remembers the previous **external** foreground window before showing the sidebar.
- If Windows blocks focus restore, CtrlV still copies text into clipboard and shows a manual fallback message.
- In that case, press `Ctrl+V` manually in your target app.
- This fallback can happen because of Windows focus restrictions and does not always mean CtrlV is broken.

## Installation

### Recommended: Installer

1. Download `CtrlV-Setup-{version}.exe`.
2. Run the setup file.
3. Complete installer steps.
4. Launch CtrlV (enabled by default on the final installer screen).

Installer behavior:

- Installs to `%LOCALAPPDATA%\Programs\CtrlV`.
- No admin rights required (per-user install).
- Start Menu shortcut is always created.
- Desktop shortcut is always created.
- Startup shortcut is always created (`CtrlV.exe --startup`).
- CtrlV starts with Windows by default. Disable it from **Tray → Launch at startup**.

### Portable

1. Download the portable build folder.
2. Extract it.
3. Run `CtrlV.exe`.

Portable vs installer:

- Installer: better Windows integration (shortcuts, uninstall entry, startup default).
- Portable: manual run and manual placement.

## Startup and tray behavior

- Startup shortcut target uses `CtrlV.exe --startup`.
- Startup shortcut path:
  `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\CtrlV.lnk`
- Startup launch runs tray-first/minimized when enabled in settings.
- Manual launch shows the sidebar UI.
- Second launch does not create a second tray icon (single-instance behavior).

## Build from source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r packaging/requirements-build.txt
python -m app.main
```

## Build portable

```powershell
powershell -ExecutionPolicy Bypass -File packaging/scripts/build_portable.ps1
```

Expected outputs:

- `dist/CtrlV-portable/CtrlV.exe`
- `release/portable/CtrlV-{version}-portable/`

## Build installer

```powershell
powershell -ExecutionPolicy Bypass -File packaging/scripts/build_installer.ps1
```

Expected output:

- `release/installer/CtrlV-Setup-{version}.exe`

## Build everything

```powershell
powershell -ExecutionPolicy Bypass -File packaging/scripts/build_all.ps1
```

## Manual action test plan

1. Open Notepad.
2. Copy text `A`.
3. Open CtrlV.
4. Single-click an item → only selection should change.
5. Click **Copy to clipboard** → clipboard updates, Notepad content does not change.
6. Double-click a **text** item → CtrlV hides, Notepad receives pasted text.
7. Double-click an **image/file** item → item is copied only, no auto-paste.
8. Tray left click toggles sidebar show/hide.
9. Window close (`X`) hides to tray.
10. Tray **Quit** exits process.
11. With startup enabled, after Windows reboot CtrlV starts tray-first/minimized.

## Release checklist

- [ ] App starts from source (`python -m app.main`).
- [ ] Portable EXE starts by double-click.
- [ ] Installer installs without admin rights.
- [ ] Desktop shortcut works.
- [ ] Start Menu shortcut works.
- [ ] Tray icon appears.
- [ ] Close (`X`) hides to tray.
- [ ] Tray Quit exits app.
- [ ] Startup shortcut works.
- [ ] Double click text auto-pastes into Notepad.
- [ ] Double click image/file copies only.
- [ ] Logs folder opens from tray.

## Logs

- Log file: `%LOCALAPPDATA%\CtrlV\logs\ctrlv.log`
- Tray action: **Open logs folder**

## Troubleshooting

- **Panel disappeared**: use tray → **Show sidebar** or **Reset panel position/state**.
- **Auto-paste did not work**: CtrlV already copied text to clipboard; switch to target app and press `Ctrl+V` manually.
- **Auto-paste goes to wrong window**:
  - Open target app first.
  - Show CtrlV after target app is active.
  - If panel was revealed from collapsed edge hover, this flow is now fixed to remember the active target before reveal.
- **App seems closed**: check system tray; close (`X`) can hide to tray.
- **CtrlV starts but no window appears**: expected for startup launch; check system tray and click **Show sidebar**.
- **Second launch does nothing**: expected; CtrlV runs as a single instance.
- **Startup does not work**: verify **Tray → Launch at startup** is enabled and check Startup shortcut exists.
- **Installer cannot replace files**: close running CtrlV (or use tray **Quit**) and rerun installer.

## Uninstall

Uninstall removes installed files and installer-created shortcuts, including the Startup shortcut. User data (logs/settings/history) is preserved unless manually deleted.

## License

See `LICENSE`.
