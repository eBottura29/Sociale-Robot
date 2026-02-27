import sys
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

SETTINGS_DIR = Path(__file__).resolve().parent
if str(SETTINGS_DIR) not in sys.path:
    sys.path.insert(0, str(SETTINGS_DIR))

from settings import get_by_path, load_settings, save_settings, set_by_path


FIELD_SPECS = [
    ("Desktop: Serial Baud", "desktop_app.serial.baud", int),
    ("Desktop: Serial Timeout", "desktop_app.serial.timeout", float),
    ("Desktop: LLM Model", "desktop_app.llm.model_name", str),
    ("Desktop: Sentiment Model", "desktop_app.llm.sentiment_model_name", str),
    ("Desktop: Allow Download", "desktop_app.llm.allow_download", bool),
    ("Desktop: Max Tokens", "desktop_app.llm.max_new_tokens", int),
    ("Desktop: Min Tokens", "desktop_app.llm.min_new_tokens", int),
    ("Desktop: Repetition Penalty", "desktop_app.llm.repetition_penalty", float),
    ("Desktop: Temperature", "desktop_app.llm.temperature", float),
    ("Desktop: Top P", "desktop_app.llm.top_p", float),
    ("Robot Pin: Drive Left", "robot.pins.drive_left", int),
    ("Robot Pin: Drive Right", "robot.pins.drive_right", int),
    ("Robot Pin: Sonar Pan", "robot.pins.sonar_pan", int),
    ("Robot Pin: Eyebrow Left", "robot.pins.eyebrow_left", int),
    ("Robot Pin: Eyebrow Right", "robot.pins.eyebrow_right", int),
    ("Robot Limit: Max Distance", "robot.limits.max_distance_cm", int),
    ("Robot Limit: Max Velocity", "robot.limits.max_velocity", int),
    ("Robot Timing: Telemetry ms", "robot.timing.telemetry_interval_ms", int),
    ("Robot Timing: Cmd timeout ms", "robot.timing.command_timeout_ms", int),
    ("Robot Nav: Avoid threshold", "robot.navigation.avoid_threshold_cm", int),
    ("Robot Nav: Approach threshold", "robot.navigation.approach_threshold_cm", int),
]


class SettingsApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NIER Settings Editor")
        self.root.geometry("980x760")
        self.root.minsize(920, 700)

        self.settings = load_settings()
        self.vars: dict[str, tk.StringVar] = {}

        self._build_style()
        self._build_ui()
        self._load_values()

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Subheader.TLabel", font=("Segoe UI", 10))
        style.configure("Section.TLabelframe", padding=8)
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        header = ttk.Frame(self.root, padding=(18, 14, 18, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Settings Editor", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Central settings in src/settings/settings.json",
            style="Subheader.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        body = ttk.Frame(self.root, padding=(18, 8, 18, 18))
        body.grid(row=1, column=0, sticky="nsew")
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)
        body.columnconfigure(0, weight=1)

        emotions_frame = ttk.Labelframe(body, text="Desktop Emotions", style="Section.TLabelframe")
        emotions_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        emotions_frame.columnconfigure(0, weight=1)
        self.emotions_text = tk.Text(emotions_frame, height=4, font=("Consolas", 10))
        self.emotions_text.grid(row=0, column=0, sticky="ew")

        fields_frame = ttk.Labelframe(body, text="General Settings", style="Section.TLabelframe")
        fields_frame.grid(row=1, column=0, sticky="nsew")
        fields_frame.rowconfigure(0, weight=1)
        fields_frame.columnconfigure(0, weight=1)

        canvas = tk.Canvas(fields_frame, highlightthickness=0)
        scroll = ttk.Scrollbar(fields_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        rows = ttk.Frame(canvas)
        rows.columnconfigure(1, weight=1)
        canvas_window = canvas.create_window((0, 0), window=rows, anchor="nw")

        def on_rows_configure(_event) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event) -> None:
            canvas.itemconfigure(canvas_window, width=event.width)

        rows.bind("<Configure>", on_rows_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        for i, (label, path, _typ) in enumerate(FIELD_SPECS):
            ttk.Label(rows, text=label).grid(row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value="")
            ttk.Entry(rows, textvariable=var).grid(row=i, column=1, sticky="ew", padx=(8, 0), pady=3)
            self.vars[path] = var

        buttons = ttk.Frame(body)
        buttons.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        buttons.columnconfigure(0, weight=1)
        ttk.Button(buttons, text="Reload", command=self._reload).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(buttons, text="Save", style="Primary.TButton", command=self._save).grid(row=0, column=2)

    def _load_values(self) -> None:
        for _label, path, _typ in FIELD_SPECS:
            value = get_by_path(self.settings, path, "")
            self.vars[path].set(str(value))

        emotions = get_by_path(self.settings, "desktop_app.emotions", [])
        self.emotions_text.delete("1.0", "end")
        self.emotions_text.insert("1.0", "\n".join(str(item) for item in emotions))

    def _reload(self) -> None:
        self.settings = load_settings()
        self._load_values()

    def _parse_value(self, raw: str, typ: type):
        if typ is int:
            return int(raw.strip())
        if typ is float:
            return float(raw.strip())
        if typ is bool:
            lowered = raw.strip().lower()
            return lowered in ("1", "true", "yes", "on")
        return raw

    def _save(self) -> None:
        updated = load_settings()
        try:
            for _label, path, typ in FIELD_SPECS:
                raw = self.vars[path].get()
                value = self._parse_value(raw, typ)
                set_by_path(updated, path, value)

            emotion_lines = [
                line.strip()
                for line in self.emotions_text.get("1.0", "end").splitlines()
                if line.strip()
            ]
            set_by_path(updated, "desktop_app.emotions", emotion_lines)
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return

        save_settings(updated)
        self.settings = updated
        messagebox.showinfo("Saved", "Settings saved to src/settings/settings.json")


def run() -> None:
    root = tk.Tk()
    SettingsApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
