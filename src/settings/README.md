# Central Settings

This folder contains centralized project settings:

- `settings.json`: editable values for desktop + robot defaults/pins.
- `settings.py`: loader/saver helpers.
- `settings_app.py`: Tkinter editor UI.
- `main.py`: launcher for the editor.

Run the editor from repository root:

```bash
python src/settings/main.py
```

Desktop app config values are loaded from this file via `src/desktop_app/config.py`.
