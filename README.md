# CtrlV

Desktop clipboard manager foundation for Windows using **Python 3.12+** and **PySide6**.

## Features in stage 1

- Clipboard monitoring via `QClipboard`.
- In-memory history store with max size and duplicate prevention.
- Support for clipboard items:
  - text
  - images
  - local file lists
  - unknown fallback
- GUI history list with icons, preview text, and metadata.
- Restore selected item back to system clipboard.
- Basic logging for app lifecycle and clipboard events.

## Project structure

```text
app/
  main.py
  bootstrap.py
  core/
    clipboard_monitor.py
    clipboard_parser.py
    history_store.py
    models.py
    signals.py
  services/
    clipboard_service.py
  ui/
    history_list.py
    main_window.py
    styles.py
  utils/
    helpers.py
    logging_config.py
```

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

## Notes

- This stage intentionally avoids persistence (SQLite), hotkeys, docking/snap, tray icon, and auto-hide behavior.
- The code is organized so those features can be added without rewriting core components.
