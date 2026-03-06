import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk


FIRMWARE_ROOT = Path(__file__).resolve().parents[2] / "firmware"
if str(FIRMWARE_ROOT) not in sys.path:
    sys.path.insert(0, str(FIRMWARE_ROOT))

from config import EMOTIONS
from led_matrix_store import (
    MATRIX_COLS,
    MATRIX_ROWS,
    blank_patterns_for_emotions,
    grid_to_segments,
    load_led_matrix_patterns,
    matrix_commands_for_emotion,
    save_led_matrix_patterns,
    segments_to_grid,
)
from serial_client import SerialManager


class LedMatrixDrawerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NIER LED Matrix Drawer")
        self.root.geometry("1260x700")
        self.root.minsize(1100, 640)

        self.serial = SerialManager(debug_cb=self._on_tx)
        self.connected = False
        self.patterns = load_led_matrix_patterns(EMOTIONS)
        self.current_emotion = tk.StringVar(value=EMOTIONS[0])
        self.port_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Status: Offline")
        self.info_var = tk.StringVar(value="Patterns loaded from settings.json")
        self.drawing_enabled = tk.BooleanVar(value=True)

        self.cell = 24
        self.pad = 2
        self.grid = [[0 for _ in range(MATRIX_COLS)] for _ in range(MATRIX_ROWS)]
        self.rectangles = [[None for _ in range(MATRIX_COLS)] for _ in range(MATRIX_ROWS)]

        self._build_style()
        self._build_ui()
        self._refresh_ports()
        self._load_current_emotion_grid()

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Sub.TLabel", font=("Segoe UI", 10))
        style.configure("Section.TLabelframe", padding=8)
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        header = ttk.Frame(self.root, padding=(16, 12, 16, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="NIER LED Matrix Drawer", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Draw 24x8 patterns per emotion. Rotation compensation is applied when sending to robot.",
            style="Sub.TLabel",
        ).grid(row=1, column=0, sticky="w")

        body = ttk.Frame(self.root, padding=(16, 8, 16, 16))
        body.grid(row=1, column=0, sticky="nsew")
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        body.columnconfigure(0, weight=5)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = ttk.Labelframe(body, text="Pattern Editor (24x8)", style="Section.TLabelframe")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        top_controls = ttk.Frame(left)
        top_controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(top_controls, text="Emotion").grid(row=0, column=0, sticky="w")
        emotion_menu = ttk.Combobox(
            top_controls,
            values=EMOTIONS,
            textvariable=self.current_emotion,
            state="readonly",
            width=20,
        )
        emotion_menu.grid(row=0, column=1, padx=(8, 0), sticky="w")
        emotion_menu.bind("<<ComboboxSelected>>", self._on_emotion_change)
        ttk.Checkbutton(
            top_controls,
            text="Drawing enabled",
            variable=self.drawing_enabled,
        ).grid(row=0, column=2, padx=(16, 0), sticky="w")

        canvas_wrap = ttk.Frame(left)
        canvas_wrap.grid(row=1, column=0, sticky="nsew")
        canvas_wrap.rowconfigure(0, weight=1)
        canvas_wrap.columnconfigure(0, weight=1)
        width = MATRIX_COLS * (self.cell + self.pad) + self.pad
        height = MATRIX_ROWS * (self.cell + self.pad) + self.pad
        self.canvas = tk.Canvas(canvas_wrap, width=width, height=height, bg="#1E1E1E", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nw")
        self._build_grid()

        action_bar = ttk.Frame(left)
        action_bar.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(action_bar, text="Save Pattern", style="Primary.TButton", command=self._save_current).grid(row=0, column=0, sticky="w")
        ttk.Button(action_bar, text="Clear Pattern", command=self._clear_current).grid(row=0, column=1, padx=(8, 0), sticky="w")
        ttk.Button(action_bar, text="Clear All", command=self._clear_all).grid(row=0, column=2, padx=(8, 0), sticky="w")
        ttk.Button(action_bar, text="Send Current", command=self._send_current).grid(row=0, column=3, padx=(8, 0), sticky="w")

        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        conn = ttk.Labelframe(right, text="Connection", style="Section.TLabelframe")
        conn.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        conn.columnconfigure(1, weight=1)
        ttk.Label(conn, text="COM").grid(row=0, column=0, sticky="w")
        self.port_menu = ttk.OptionMenu(conn, self.port_var, "")
        self.port_menu.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(conn, text="Refresh", command=self._refresh_ports).grid(row=0, column=2, padx=(6, 0))
        self.connect_btn = ttk.Button(conn, text="Connect", style="Primary.TButton", command=self._toggle_connection)
        self.connect_btn.grid(row=1, column=0, pady=(8, 0), sticky="w")
        ttk.Label(conn, textvariable=self.status_var).grid(row=1, column=1, columnspan=2, sticky="w", padx=(6, 0))

        info = ttk.Labelframe(right, text="Info", style="Section.TLabelframe")
        info.grid(row=1, column=0, sticky="ew")
        ttk.Label(
            info,
            text="Hardware note: the matrix is mounted 90° to the right.\n"
            "This app rotates output before sending so drawn faces appear upright.",
            wraplength=320,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(info, textvariable=self.info_var, foreground="#0B5E20", wraplength=320).grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )

    def _build_grid(self) -> None:
        for y in range(MATRIX_ROWS):
            for x in range(MATRIX_COLS):
                x0 = self.pad + x * (self.cell + self.pad)
                y0 = self.pad + y * (self.cell + self.pad)
                x1 = x0 + self.cell
                y1 = y0 + self.cell
                rect = self.canvas.create_rectangle(x0, y0, x1, y1, fill="#3A3A3A", outline="#666666", width=1)
                self.canvas.tag_bind(rect, "<Button-1>", lambda _e, gx=x, gy=y: self._toggle_pixel(gy, gx))
                self.rectangles[y][x] = rect
        for split in (8, 16):
            x = self.pad + split * (self.cell + self.pad) - (self.pad // 2)
            self.canvas.create_line(x, 0, x, self.canvas.winfo_reqheight(), fill="#AFAFAF", width=2)

    def _load_current_emotion_grid(self) -> None:
        emotion = self.current_emotion.get()
        segments = self.patterns.get(emotion)
        if segments is None:
            return
        self.grid = segments_to_grid(segments)
        self._redraw_grid()

    def _redraw_grid(self) -> None:
        for y in range(MATRIX_ROWS):
            for x in range(MATRIX_COLS):
                color = "#00C853" if self.grid[y][x] else "#3A3A3A"
                self.canvas.itemconfigure(self.rectangles[y][x], fill=color)

    def _toggle_pixel(self, y: int, x: int) -> None:
        if not self.drawing_enabled.get():
            return
        self.grid[y][x] = 0 if self.grid[y][x] else 1
        self._redraw_grid()

    def _on_emotion_change(self, _event=None) -> None:
        self._load_current_emotion_grid()
        self.info_var.set(f"Loaded {self.current_emotion.get()} pattern from settings.")

    def _save_current(self) -> None:
        emotion = self.current_emotion.get()
        self.patterns[emotion] = grid_to_segments(self.grid)
        save_led_matrix_patterns(self.patterns, EMOTIONS)
        self.info_var.set(f"Saved {emotion} pattern to settings.json")

    def _clear_current(self) -> None:
        self.grid = [[0 for _ in range(MATRIX_COLS)] for _ in range(MATRIX_ROWS)]
        self._redraw_grid()
        self.info_var.set(f"Cleared current canvas for {self.current_emotion.get()}.")

    def _clear_all(self) -> None:
        self.patterns = blank_patterns_for_emotions(EMOTIONS)
        save_led_matrix_patterns(self.patterns, EMOTIONS)
        self._load_current_emotion_grid()
        self.info_var.set("Cleared all emotion patterns and saved settings.json")

    def _send_current(self) -> None:
        if not self.connected or not self.serial.serial_port:
            self.info_var.set("Connect first to send MATRIX commands.")
            return
        emotion = self.current_emotion.get()
        self.patterns[emotion] = grid_to_segments(self.grid)
        for cmd in matrix_commands_for_emotion(emotion, self.patterns):
            self.serial.send_line(cmd)
        self.info_var.set(f"Sent MATRIX payload for {emotion}.")

    def _refresh_ports(self) -> None:
        ports = self.serial.refresh_ports()
        menu = self.port_menu["menu"]
        menu.delete(0, "end")
        for port in ports:
            menu.add_command(label=port, command=tk._setit(self.port_var, port))
        if ports and self.port_var.get() not in ports:
            self.port_var.set(ports[0])

    def _toggle_connection(self) -> None:
        if self.connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self) -> None:
        port = self.port_var.get()
        if not port:
            self.status_var.set("Status: No COM selected")
            return
        ok, err = self.serial.connect(port)
        if not ok:
            self.status_var.set(f"Status: Error - {err}")
            return
        self.connected = True
        self.connect_btn.configure(text="Disconnect")
        self.status_var.set(f"Status: Connected ({port})")
        self.serial.send_line("HELLO")

    def _disconnect(self) -> None:
        self.serial.disconnect()
        self.connected = False
        self.connect_btn.configure(text="Connect")
        self.status_var.set("Status: Offline")

    def _on_tx(self, _line: str) -> None:
        pass

    def on_close(self) -> None:
        self._disconnect()
        self.root.destroy()


def run() -> None:
    root = tk.Tk()
    app = LedMatrixDrawerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    run()
