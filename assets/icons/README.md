# Icons

Place the Windows application icon at:

- `assets/icons/app.ico`

Packaging integration is already wired for both:

- PyInstaller executable icon (`packaging/pyinstaller/ctrlv.spec`)
- Inno Setup installer icon (`packaging/inno/ctrlv_installer.iss`)

If `app.ico` is missing, builds still work and default icons are used.
