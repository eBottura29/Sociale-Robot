import json
import sys
import time
from pathlib import Path

import serial
import tkinter as tk
from tkinter import ttk

FIRMWARE_ROOT = Path(__file__).resolve().parents[2] / "firmware"
if str(FIRMWARE_ROOT) not in sys.path:
    sys.path.insert(0, str(FIRMWARE_ROOT))

from config import CONTROL_LAB_DEFAULTS, EMOTION_BUZZER_ENABLED, EMOTIONS, PAN_AUTO_SPEED_MS
from emotion_output_store import load_emotion_buzzer_pitch_map, load_emotion_rgb_map
from eyebrow_store import browmap_command_for_emotion, load_eyebrow_angles
from led_matrix_store import load_led_matrix_patterns, matrix_commands_for_emotion
from serial_client import SerialManager


class ControlLabApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NIER Control Lab")
        width = int(CONTROL_LAB_DEFAULTS.get("window_width", 1220))
        height = int(CONTROL_LAB_DEFAULTS.get("window_height", 840))
        min_width = int(CONTROL_LAB_DEFAULTS.get("window_min_width", 1080))
        min_height = int(CONTROL_LAB_DEFAULTS.get("window_min_height", 760))
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(min_width, min_height)

        self.serial = SerialManager(debug_cb=self._on_tx)
        self.connected = False
        self.poll_after_id = None
        self.active_keys = set()

        self.motion_enabled = tk.BooleanVar(value=False)
        self.sonar_enabled = tk.BooleanVar(value=True)
        self.pan_auto = tk.BooleanVar(value=True)
        self.buzzer_enabled = tk.BooleanVar(value=False)
        self.emotion_buzzer_enabled = tk.BooleanVar(
            value=bool(CONTROL_LAB_DEFAULTS.get("default_emotion_buzzer_enabled", EMOTION_BUZZER_ENABLED))
        )

        self.speed_var = tk.IntVar(value=int(CONTROL_LAB_DEFAULTS.get("default_drive_speed", 80)))
        self.pan_angle_var = tk.IntVar(value=int(CONTROL_LAB_DEFAULTS.get("default_pan_angle", 90)))
        self.pan_auto_speed_var = tk.IntVar(
            value=int(CONTROL_LAB_DEFAULTS.get("default_pan_auto_speed_ms", PAN_AUTO_SPEED_MS))
        )
        self.emo_name_var = tk.StringVar(value=EMOTIONS[0])
        self.emo_intensity_var = tk.IntVar(value=int(CONTROL_LAB_DEFAULTS.get("default_emotion_intensity", 70)))
        self.left_brow_var = tk.IntVar(value=int(CONTROL_LAB_DEFAULTS.get("default_brow_left", 90)))
        self.right_brow_var = tk.IntVar(value=int(CONTROL_LAB_DEFAULTS.get("default_brow_right", 90)))
        self.rgb_r_var = tk.IntVar(value=int(CONTROL_LAB_DEFAULTS.get("default_rgb_r", 0)))
        self.rgb_g_var = tk.IntVar(value=int(CONTROL_LAB_DEFAULTS.get("default_rgb_g", 0)))
        self.rgb_b_var = tk.IntVar(value=int(CONTROL_LAB_DEFAULTS.get("default_rgb_b", 0)))
        self.buzzer_pitch_var = tk.IntVar(value=int(CONTROL_LAB_DEFAULTS.get("default_buzzer_pitch", 880)))
        self.lcd_var = tk.StringVar(value="")
        self.port_var = tk.StringVar(value="")

        self.telemetry_vars: dict[str, tk.StringVar] = {}
        self.last_drive = None
        self.last_drive_sent_at = 0.0
        self.drive_keepalive_after_id = None
        self.drive_keepalive_interval_ms = 120
        self.pan_auto_after_id = None
        self.pan_auto_target_angle = 20
        self.pan_auto_min_angle = 20.0
        self.pan_auto_max_angle = 160.0
        self.pan_auto_angle = float(self.pan_auto_min_angle)
        self.pan_auto_direction = 1.0
        self.pan_auto_tick_ms = 20
        self.pan_auto_last_tick_at = 0.0
        base_pan_step = max(1, min(30, int(CONTROL_LAB_DEFAULTS.get("pan_key_step_deg", 5))))
        self.pan_key_step_deg = max(1, min(30, base_pan_step * 2))
        base_pan_scale = max(0.05, min(1.0, float(CONTROL_LAB_DEFAULTS.get("pan_manual_scale", 0.35))))
        self.pan_manual_scale = max(0.05, min(1.0, base_pan_scale * 2.0))
        self.pan_hold_repeat_ms = max(25, min(200, int(CONTROL_LAB_DEFAULTS.get("pan_hold_repeat_ms", 50))))
        self.pan_smooth_interval_ms = max(15, min(80, int(CONTROL_LAB_DEFAULTS.get("pan_smooth_interval_ms", 20))))
        self.pan_angle_float = float(self.pan_angle_var.get())
        self.pan_motion_after_id = None
        self.pan_motion_last_ts = 0.0

        self.keybinds = self._load_keybinds()
        self.matrix_patterns = load_led_matrix_patterns(EMOTIONS)
        self.eyebrow_angles = load_eyebrow_angles(EMOTIONS)
        self.emotion_rgb_map = load_emotion_rgb_map(EMOTIONS)
        self.emotion_buzzer_pitch_map = load_emotion_buzzer_pitch_map(EMOTIONS)

        self._build_style()
        self._build_ui()
        self._refresh_ports()
        self._reset_telemetry()
        self._bind_keys()

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
        ttk.Label(header, text="NIER Control Lab", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Testing tool using firmware serial commands", style="Sub.TLabel").grid(
            row=1, column=0, sticky="w"
        )

        body = ttk.Frame(self.root, padding=(16, 8, 16, 16))
        body.grid(row=1, column=0, sticky="nsew")
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        controls_wrap = ttk.Frame(body)
        controls_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        controls_wrap.rowconfigure(0, weight=1)
        controls_wrap.columnconfigure(0, weight=1)

        self.controls_canvas = tk.Canvas(controls_wrap, highlightthickness=0)
        controls_scroll = ttk.Scrollbar(controls_wrap, orient="vertical", command=self.controls_canvas.yview)
        self.controls_canvas.configure(yscrollcommand=controls_scroll.set)
        self.controls_canvas.grid(row=0, column=0, sticky="nsew")
        controls_scroll.grid(row=0, column=1, sticky="ns")

        controls = ttk.Frame(self.controls_canvas)
        controls.columnconfigure(0, weight=1)
        self.controls_window_id = self.controls_canvas.create_window((0, 0), window=controls, anchor="nw")
        controls.bind("<Configure>", self._on_controls_configure)
        self.controls_canvas.bind("<Configure>", self._on_controls_canvas_configure)
        self.controls_canvas.bind("<Enter>", self._bind_controls_mousewheel)
        self.controls_canvas.bind("<Leave>", self._unbind_controls_mousewheel)

        status = ttk.Frame(body)
        status.grid(row=0, column=1, sticky="nsew")
        status.columnconfigure(0, weight=1)
        status.rowconfigure(3, weight=1)

        self._build_connection(status)
        self._build_telemetry(status)
        self._build_log(status)

        self._build_drive(controls)
        self._build_emotion(controls)
        self._build_eyebrows(controls)
        self._build_pan(controls)
        self._build_rgb(controls)
        self._build_buzzer(controls)
        self._build_lcd(controls)

    def _on_controls_configure(self, _event) -> None:
        self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox("all"))

    def _on_controls_canvas_configure(self, event) -> None:
        self.controls_canvas.itemconfigure(self.controls_window_id, width=event.width)

    def _bind_controls_mousewheel(self, _event) -> None:
        self.root.bind_all("<MouseWheel>", self._on_controls_mousewheel)

    def _unbind_controls_mousewheel(self, _event) -> None:
        self.root.unbind_all("<MouseWheel>")

    def _on_controls_mousewheel(self, event) -> None:
        delta = -1 if event.delta > 0 else 1
        self.controls_canvas.yview_scroll(delta, "units")

    def _build_connection(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="Connection", style="Section.TLabelframe")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="COM").grid(row=0, column=0, sticky="w")
        self.port_menu = ttk.OptionMenu(frame, self.port_var, "")
        self.port_menu.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(frame, text="Refresh", command=self._refresh_ports).grid(row=0, column=2, padx=(6, 0))

        self.connect_btn = ttk.Button(frame, text="Connect", style="Primary.TButton", command=self._toggle_connection)
        self.connect_btn.grid(row=1, column=0, pady=(8, 0), sticky="w")

        self.connection_var = tk.StringVar(value="Status: Offline")
        ttk.Label(frame, textvariable=self.connection_var).grid(row=1, column=1, columnspan=2, sticky="w", padx=(6, 0))

        ttk.Checkbutton(frame, text="Motion enabled", variable=self.motion_enabled, command=self._on_motion_toggle).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )
        ttk.Checkbutton(frame, text="Sonar enabled", variable=self.sonar_enabled, command=self._on_sonar_toggle).grid(
            row=3, column=0, columnspan=3, sticky="w"
        )

    def _build_drive(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="Drive (WASD)", style="Section.TLabelframe")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Speed").grid(row=0, column=0, sticky="w")
        ttk.Scale(frame, from_=30, to=255, orient="horizontal", variable=self.speed_var).grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )
        ttk.Label(frame, text="Hold keys to move while motion is enabled").grid(row=1, column=0, columnspan=2, sticky="w")

    def _build_emotion(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="Emotion Sender", style="Section.TLabelframe")
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Emotion").grid(row=0, column=0, sticky="w")
        emo_menu = ttk.Combobox(frame, textvariable=self.emo_name_var, values=EMOTIONS, state="readonly")
        emo_menu.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(frame, text="Intensity").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Scale(frame, from_=0, to=100, orient="horizontal", variable=self.emo_intensity_var).grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=(6, 0)
        )
        btns = ttk.Frame(frame)
        btns.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(btns, text="Apply Emotion", command=self._send_emotion).grid(row=0, column=0)
        ttk.Button(btns, text="Clear Emotions", command=self._clear_emotions).grid(row=0, column=1, padx=(8, 0))
        ttk.Checkbutton(frame, text="Buzzer from emotion", variable=self.emotion_buzzer_enabled).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

    def _build_eyebrows(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="Eyebrows", style="Section.TLabelframe")
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Left").grid(row=0, column=0, sticky="w")
        ttk.Scale(frame, from_=45, to=135, orient="horizontal", variable=self.left_brow_var).grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )
        ttk.Label(frame, text="Right").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Scale(frame, from_=45, to=135, orient="horizontal", variable=self.right_brow_var).grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=(6, 0)
        )
        ttk.Button(frame, text="Apply Eyebrows", command=self._send_eyebrows).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _build_pan(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="Top Servo (Pan)", style="Section.TLabelframe")
        frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(frame, text="Automatic scan", variable=self.pan_auto, command=self._on_pan_mode_toggle).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(frame, text="Manual angle").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.pan_scale = ttk.Scale(frame, from_=0, to=180, orient="horizontal", variable=self.pan_angle_var)
        self.pan_scale.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(6, 0))
        ttk.Label(frame, text="Sweep speed (deg/s)").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.pan_auto_speed_scale = ttk.Scale(frame, from_=40, to=600, orient="horizontal", variable=self.pan_auto_speed_var)
        self.pan_auto_speed_scale.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(6, 0))
        ttk.Label(frame, text="Manual mode sends full speed: 0=left, 90=stop, 180=right").grid(
            row=3, column=0, columnspan=2, sticky="w"
        )
        self.pan_btn = ttk.Button(frame, text="Apply Pan Angle", command=self._send_pan_angle)
        self.pan_btn.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._sync_pan_widgets()

    def _build_rgb(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="RGB LED", style="Section.TLabelframe")
        frame.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="R").grid(row=0, column=0, sticky="w")
        ttk.Scale(frame, from_=0, to=255, orient="horizontal", variable=self.rgb_r_var).grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )
        ttk.Label(frame, text="G").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Scale(frame, from_=0, to=255, orient="horizontal", variable=self.rgb_g_var).grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=(6, 0)
        )
        ttk.Label(frame, text="B").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Scale(frame, from_=0, to=255, orient="horizontal", variable=self.rgb_b_var).grid(
            row=2, column=1, sticky="ew", padx=(8, 0), pady=(6, 0)
        )
        ttk.Button(frame, text="Apply RGB", command=self._send_rgb).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _build_buzzer(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="Buzzer", style="Section.TLabelframe")
        frame.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(frame, text="Buzzer ON", variable=self.buzzer_enabled).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Pitch (Hz)").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Scale(frame, from_=100, to=5000, orient="horizontal", variable=self.buzzer_pitch_var).grid(
            row=1, column=1, sticky="ew", padx=(8, 0), pady=(6, 0)
        )
        ttk.Button(frame, text="Apply Buzzer", command=self._send_buzzer).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _build_lcd(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="LCD", style="Section.TLabelframe")
        frame.grid(row=6, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        entry = ttk.Entry(frame, textvariable=self.lcd_var)
        entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(frame, text="Send LCD", command=self._send_lcd).grid(row=0, column=1, padx=(8, 0))

    def _build_telemetry(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="Telemetry", style="Section.TLabelframe")
        frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        frame.columnconfigure(1, weight=1)
        labels = [
            "Sonar Links",
            "Sonar Rechts",
            "Dichtste Afstand",
            "Batterij",
            "Navigatie Modus",
            "Sonar Status",
            "Laatste Commando",
            "RGB Status",
            "Matrix",
            "LCD",
            "Eyebrow Links",
            "Eyebrow Rechts",
            "Pan Mode",
            "Pan Angle",
            "Buzzer",
            "Buzzer Pitch",
        ]
        for idx, label in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=idx, column=0, sticky="w")
            var = tk.StringVar(value="-")
            ttk.Label(frame, textvariable=var, wraplength=320).grid(row=idx, column=1, sticky="w", padx=(8, 0))
            self.telemetry_vars[label] = var

    def _build_log(self, parent: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent, text="Serial Log", style="Section.TLabelframe")
        frame.grid(row=3, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.log = tk.Text(frame, height=10, font=("Consolas", 9), state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")

    def _load_keybinds(self) -> dict:
        defaults = {
            "forward": "w",
            "backward": "s",
            "left": "a",
            "right": "d",
            "toggle_motion": "m",
            "toggle_sonar": "t",
            "toggle_pan_mode": "p",
            "toggle_buzzer": "b",
            "send_lcd": "return",
            "apply_emotion": "e",
            "apply_rgb": "c",
            "apply_eyebrows": "x",
        }
        path = Path(__file__).with_name("keybinds.json")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for key, value in defaults.items():
                loaded = data.get(key, value)
                if not isinstance(loaded, str) or not loaded.strip():
                    data[key] = value
            return {k: str(v).lower() for k, v in data.items()}
        except Exception:
            return defaults

    def _bind_keys(self) -> None:
        self.root.bind_all("<KeyPress>", self._on_key_press)
        self.root.bind_all("<KeyRelease>", self._on_key_release)

    def _on_key_press(self, event) -> None:
        key = event.keysym.lower()
        widget_class = event.widget.winfo_class()
        if widget_class in ("Entry", "TEntry") and key != self.keybinds["send_lcd"]:
            return
        if key in ("left", "right", "up", "down"):
            if key in self.active_keys:
                return
            self.active_keys.add(key)
            self._start_pan_motion_loop()
            return
        if key in self.active_keys:
            return
        self.active_keys.add(key)

        if key == self.keybinds["toggle_motion"]:
            self.motion_enabled.set(not self.motion_enabled.get())
            self._on_motion_toggle()
            return
        if key == self.keybinds["toggle_sonar"]:
            self.sonar_enabled.set(not self.sonar_enabled.get())
            self._on_sonar_toggle()
            return
        if key == self.keybinds["toggle_pan_mode"]:
            self.pan_auto.set(not self.pan_auto.get())
            self._on_pan_mode_toggle()
            return
        if key == self.keybinds["toggle_buzzer"]:
            self.buzzer_enabled.set(not self.buzzer_enabled.get())
            self._send_buzzer()
            return
        if key == self.keybinds["apply_emotion"]:
            self._send_emotion()
            return
        if key == self.keybinds["apply_rgb"]:
            self._send_rgb()
            return
        if key == self.keybinds["apply_eyebrows"]:
            self._send_eyebrows()
            return
        if key == self.keybinds["send_lcd"]:
            self._send_lcd()
            return

        self._update_drive_from_keys()

    def _on_key_release(self, event) -> None:
        key = event.keysym.lower()
        if key in self.active_keys:
            self.active_keys.remove(key)
        if key in ("left", "right", "up", "down"):
            if self._pan_direction_from_active_keys() == 0:
                self._stop_pan_motion_loop()
        self._update_drive_from_keys()

    def _pan_direction_from_active_keys(self) -> int:
        right = ("right" in self.active_keys) or ("up" in self.active_keys)
        left = ("left" in self.active_keys) or ("down" in self.active_keys)
        if right and not left:
            return 1
        if left and not right:
            return -1
        return 0

    def _ensure_pan_manual_mode(self) -> bool:
        if not self.sonar_enabled.get():
            return False
        if self.pan_auto.get():
            self.pan_auto.set(False)
            self._on_pan_mode_toggle()
        return True

    def _start_pan_motion_loop(self) -> None:
        if not self._ensure_pan_manual_mode():
            return
        self._set_t("Pan Mode", "MANUAL")
        self.pan_angle_float = float(self.pan_angle_var.get())
        self.pan_motion_last_ts = time.time()
        self._tick_pan_motion_loop()

    def _stop_pan_motion_loop(self) -> None:
        if self.pan_motion_after_id is not None:
            self.root.after_cancel(self.pan_motion_after_id)
            self.pan_motion_after_id = None
        self.pan_motion_last_ts = 0.0

    def _tick_pan_motion_loop(self) -> None:
        if not self._ensure_pan_manual_mode():
            self._stop_pan_motion_loop()
            return
        direction = self._pan_direction_from_active_keys()
        if direction == 0:
            self._stop_pan_motion_loop()
            return
        now = time.time()
        if self.pan_motion_last_ts <= 0.0:
            dt = self.pan_smooth_interval_ms / 1000.0
        else:
            dt = max(0.005, min(0.2, now - self.pan_motion_last_ts))
        self.pan_motion_last_ts = now
        base_speed = (self.pan_key_step_deg * 1000.0) / max(1.0, float(self.pan_hold_repeat_ms))
        speed_deg_per_s = max(20.0, min(720.0, base_speed))
        next_angle = self.pan_angle_float + (direction * speed_deg_per_s * dt)
        next_angle = max(0.0, min(180.0, next_angle))
        if abs(next_angle - self.pan_angle_float) >= 0.001:
            self.pan_angle_float = next_angle
            requested = int(round(self.pan_angle_float))
            if requested != int(self.pan_angle_var.get()):
                self.pan_angle_var.set(requested)
                self._set_t("Pan Angle", f"{requested} deg")
            self._send_pan_angle()
        self.pan_motion_after_id = self.root.after(self.pan_smooth_interval_ms, self._tick_pan_motion_loop)

    def _toggle_connection(self) -> None:
        if self.connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self) -> None:
        port = self.port_var.get()
        if not port:
            self.connection_var.set("Status: No COM selected")
            return
        ok, err = self.serial.connect(port)
        if not ok:
            self.connection_var.set(f"Status: Error - {err}")
            return
        self.connected = True
        self.connect_btn.configure(text="Disconnect")
        self.connection_var.set(f"Status: Connected ({port})")
        self._reset_telemetry()
        self._send_line("HELLO")
        self._send_line("SONAR:ON")
        self._on_pan_mode_toggle()
        self._poll_serial()

    def _disconnect(self) -> None:
        self._stop_pan_auto_loop()
        self._stop_pan_motion_loop()
        self._stop_drive_keepalive()
        self._send_stop()
        if self.poll_after_id:
            self.root.after_cancel(self.poll_after_id)
            self.poll_after_id = None
        self.serial.disconnect()
        self.connected = False
        self.connect_btn.configure(text="Connect")
        self.connection_var.set("Status: Offline")

    def _on_motion_toggle(self) -> None:
        if not self.motion_enabled.get():
            self._send_stop()

    def _on_sonar_toggle(self) -> None:
        self._set_t("Sonar Status", "SCAN AAN" if self.sonar_enabled.get() else "HEAD STILL")
        self._send_line("SONAR:ON")
        if self.sonar_enabled.get():
            if self.pan_auto.get():
                self._start_pan_auto_loop()
        else:
            self._stop_pan_auto_loop()
            self._send_line("PAN:MANUAL")
            self._send_line("PAN:90")

    def _on_pan_mode_toggle(self) -> None:
        self._stop_pan_auto_loop()
        self._sync_pan_widgets()
        if self.pan_auto.get():
            self._send_line("PAN:MANUAL")
            self._start_pan_auto_loop()
        else:
            self._send_line("PAN:MANUAL")
            self._send_pan_angle()

    def _sync_pan_widgets(self) -> None:
        state = "disabled" if self.pan_auto.get() else "normal"
        self.pan_scale.configure(state=state)
        self.pan_btn.configure(state=state)

    def _send_emotion(self) -> None:
        values = {name: 0 for name in EMOTIONS}
        emotion_name = self.emo_name_var.get()
        intensity = int(self.emo_intensity_var.get())
        values[emotion_name] = intensity
        payload = ",".join(str(values[name]) for name in EMOTIONS)
        browmap_cmd = browmap_command_for_emotion(emotion_name, EMOTIONS, self.eyebrow_angles)
        if browmap_cmd:
            self._send_line(browmap_cmd)
        for matrix_cmd in matrix_commands_for_emotion(emotion_name, self.matrix_patterns):
            self._send_line(matrix_cmd)
        rgb = self.emotion_rgb_map.get(emotion_name, (0, 0, 0))
        self._send_line(f"RGB:{rgb[0]},{rgb[1]},{rgb[2]}")
        if self.emotion_buzzer_enabled.get():
            pitch = int(self.emotion_buzzer_pitch_map.get(emotion_name, 0))
            if pitch > 0 and intensity > 0:
                self._send_line(f"BUZZER:ON,{pitch}")
            else:
                self._send_line("BUZZER:OFF")
        else:
            self._send_line("BUZZER:OFF")
        self._send_line(f"EMO:{payload}")

    def _clear_emotions(self) -> None:
        self._send_line("EMO:0,0,0,0,0,0,0,0")

    def _send_eyebrows(self) -> None:
        left = max(45, min(135, int(self.left_brow_var.get())))
        right = max(45, min(135, int(self.right_brow_var.get())))
        self._send_line(f"BROW:{left},{right}")

    def _send_pan_angle(self) -> None:
        if self.pan_auto.get():
            return
        # Map slider around center to a reduced continuous-servo speed range.
        # Inverted so UI direction matches expected head movement.
        requested = max(0, min(180, int(self.pan_angle_var.get())))
        self.pan_angle_float = float(requested)
        centered = (requested - 90) / 90.0
        inverted = -centered
        scaled = inverted * self.pan_manual_scale
        target = max(0, min(180, int(round(90 + (scaled * 90)))))
        self._send_line(f"PAN:{target}")

    def _clamped_pan_auto_speed(self) -> int:
        raw = int(self.pan_auto_speed_var.get())
        return max(10, min(600, raw))

    def _start_pan_auto_loop(self) -> None:
        if not self.connected or not self.serial.serial_port or not self.pan_auto.get() or not self.sonar_enabled.get():
            return
        self._stop_pan_auto_loop()
        self.pan_auto_angle = float(self.pan_auto_min_angle)
        self.pan_auto_direction = 1.0
        self.pan_auto_last_tick_at = time.time()
        self._send_line(f"PAN:{int(round(self.pan_auto_angle))}")
        self._tick_pan_auto_loop()

    def _stop_pan_auto_loop(self) -> None:
        if self.pan_auto_after_id is not None:
            self.root.after_cancel(self.pan_auto_after_id)
            self.pan_auto_after_id = None
        self.pan_auto_last_tick_at = 0.0

    def _tick_pan_auto_loop(self) -> None:
        if not self.connected or not self.serial.serial_port or not self.pan_auto.get() or not self.sonar_enabled.get():
            self.pan_auto_after_id = None
            return
        now = time.time()
        if self.pan_auto_last_tick_at <= 0:
            dt = self.pan_auto_tick_ms / 1000.0
        else:
            dt = max(0.005, min(0.2, now - self.pan_auto_last_tick_at))
        self.pan_auto_last_tick_at = now
        speed_deg_per_s = float(self._clamped_pan_auto_speed())
        next_angle = self.pan_auto_angle + (self.pan_auto_direction * speed_deg_per_s * dt)
        if next_angle >= self.pan_auto_max_angle:
            overshoot = next_angle - self.pan_auto_max_angle
            next_angle = self.pan_auto_max_angle - overshoot
            self.pan_auto_direction = -1.0
        elif next_angle <= self.pan_auto_min_angle:
            overshoot = self.pan_auto_min_angle - next_angle
            next_angle = self.pan_auto_min_angle + overshoot
            self.pan_auto_direction = 1.0
        next_angle = max(self.pan_auto_min_angle, min(self.pan_auto_max_angle, next_angle))
        self.pan_auto_angle = next_angle
        self._send_line(f"PAN:{int(round(self.pan_auto_angle))}")
        self.pan_auto_after_id = self.root.after(self.pan_auto_tick_ms, self._tick_pan_auto_loop)

    def _send_rgb(self) -> None:
        r = int(self.rgb_r_var.get())
        g = int(self.rgb_g_var.get())
        b = int(self.rgb_b_var.get())
        self._send_line(f"RGB:{r},{g},{b}")

    def _send_buzzer(self) -> None:
        pitch = int(self.buzzer_pitch_var.get())
        if self.buzzer_enabled.get():
            self._send_line(f"BUZZER:ON,{pitch}")
        else:
            self._send_line("BUZZER:OFF")

    def _send_lcd(self) -> None:
        text = self.lcd_var.get().strip()
        self._send_line(f"LCD:{text}")

    def _send_stop(self) -> None:
        self.last_drive = None
        self._stop_drive_keepalive()
        self._send_line("STOP")

    def _stop_drive_keepalive(self) -> None:
        if self.drive_keepalive_after_id is not None:
            self.root.after_cancel(self.drive_keepalive_after_id)
            self.drive_keepalive_after_id = None

    def _send_drive(self, move, force: bool = False) -> None:
        now = time.time()
        if not force and move == self.last_drive and now - self.last_drive_sent_at < 0.12:
            return
        self.last_drive = move
        self.last_drive_sent_at = now
        if move == (0, 0):
            self._send_line("STOP")
        else:
            self._send_line(f"MOVE:{move[0]},{move[1]}")

    def _drive_keepalive_tick(self) -> None:
        if not self.motion_enabled.get():
            self.drive_keepalive_after_id = None
            return
        if not self.active_keys:
            self.drive_keepalive_after_id = None
            return
        if self.last_drive and self.last_drive != (0, 0):
            self._send_drive(self.last_drive, force=True)
            self.drive_keepalive_after_id = self.root.after(
                self.drive_keepalive_interval_ms, self._drive_keepalive_tick
            )
            return
        self.drive_keepalive_after_id = None

    def _update_drive_from_keys(self) -> None:
        if not self.motion_enabled.get():
            return
        # Invert both axes so key directions are flipped in control lab.
        fwd = self.keybinds["backward"] in self.active_keys
        back = self.keybinds["forward"] in self.active_keys
        left = self.keybinds["right"] in self.active_keys
        right = self.keybinds["left"] in self.active_keys

        speed = int(self.speed_var.get())
        move = (0, 0)
        if fwd and not back:
            if left and not right:
                move = (speed // 2, speed)
            elif right and not left:
                move = (speed, speed // 2)
            else:
                move = (speed, speed)
        elif back and not fwd:
            if left and not right:
                move = (-speed // 2, -speed)
            elif right and not left:
                move = (-speed, -speed // 2)
            else:
                move = (-speed, -speed)
        elif left and not right:
            move = (-speed, speed)
        elif right and not left:
            move = (speed, -speed)

        if move == (0, 0):
            self._send_drive(move)
            self._stop_drive_keepalive()
            return
        self._send_drive(move)
        if self.drive_keepalive_after_id is None:
            self.drive_keepalive_after_id = self.root.after(
                self.drive_keepalive_interval_ms, self._drive_keepalive_tick
            )

    def _poll_serial(self) -> None:
        if not self.connected or not self.serial.serial_port:
            return
        try:
            while self.serial.serial_port.in_waiting:
                raw = self.serial.serial_port.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", errors="ignore").strip()
                if line:
                    self._on_rx(line)
        except serial.SerialException as exc:
            self._append_log(f"[ERR] {exc}")
            self._disconnect()
            return
        self.poll_after_id = self.root.after(100, self._poll_serial)

    def _on_tx(self, line: str) -> None:
        self._append_log(f"[TX] {line}")

    def _on_rx(self, line: str) -> None:
        self._append_log(f"[RX] {line}")
        if line.startswith("ACK:"):
            self._set_t("Laatste Commando", line[4:])
            return
        if line.startswith("STAT:"):
            p = line[5:].split(",")
            if len(p) >= 5:
                self._set_t("Sonar Links", f"{self._safe_int(p[0])} cm")
                self._set_t("Sonar Rechts", f"{self._safe_int(p[1])} cm")
                self._set_t("Dichtste Afstand", f"{self._safe_int(p[2])} cm")
                self._set_t("Batterij", f"{self._safe_int(p[3])}%")
                self._set_t("Navigatie Modus", p[4])
            return
        if line.startswith("OUT:"):
            p = line[4:].split(",")
            if len(p) >= 6:
                self._set_t("RGB Status", f"{p[0]},{p[1]},{p[2]}")
                self._set_t("Buzzer", "Aan" if p[3] == "1" else "Uit")
                self._set_t("Matrix", p[4])
                self._set_t("LCD", ",".join(p[5:]).strip())
            return
        if line.startswith("BROW:"):
            p = line[5:].split(",")
            if len(p) >= 2:
                self._set_t("Eyebrow Links", f"{self._safe_int(p[0])} deg")
                self._set_t("Eyebrow Rechts", f"{self._safe_int(p[1])} deg")
            return
        if line.startswith("ACT:"):
            p = line[4:].split(",")
            if len(p) >= 4:
                self._set_t("Pan Mode", p[0])
                self._set_t("Pan Angle", f"{self._safe_int(p[1])} deg")
                self._set_t("Buzzer", "Aan" if p[2] == "1" else "Uit")
                self._set_t("Buzzer Pitch", f"{self._safe_int(p[3])} Hz")
            return

    def _send_line(self, line: str) -> None:
        if not self.connected or not self.serial.serial_port:
            return
        self.serial.send_line(line)

    def _reset_telemetry(self) -> None:
        defaults = {
            "Sonar Links": "0 cm",
            "Sonar Rechts": "0 cm",
            "Dichtste Afstand": "0 cm",
            "Batterij": "0%",
            "Navigatie Modus": "Offline",
            "Sonar Status": "SCAN AAN",
            "Laatste Commando": "-",
            "RGB Status": "0,0,0",
            "Matrix": "-",
            "LCD": "-",
            "Eyebrow Links": "90 deg",
            "Eyebrow Rechts": "90 deg",
            "Pan Mode": "AUTO",
            "Pan Angle": "90 deg",
            "Buzzer": "Uit",
            "Buzzer Pitch": "880 Hz",
        }
        for key, value in defaults.items():
            self._set_t(key, value)

    def _set_t(self, label: str, value: str) -> None:
        var = self.telemetry_vars.get(label)
        if var:
            var.set(value)

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    @staticmethod
    def _safe_int(value: str) -> int:
        try:
            return int(value)
        except ValueError:
            return 0

    def _refresh_ports(self) -> None:
        ports = self.serial.refresh_ports()
        menu = self.port_menu["menu"]
        menu.delete(0, "end")
        for port in ports:
            menu.add_command(label=port, command=tk._setit(self.port_var, port))
        if ports and self.port_var.get() not in ports:
            self.port_var.set(ports[0])

    def on_close(self) -> None:
        # Shutdown should not block on serial writes.
        self._stop_pan_auto_loop()
        self._stop_pan_motion_loop()
        self._stop_drive_keepalive()
        if self.poll_after_id:
            try:
                self.root.after_cancel(self.poll_after_id)
            except Exception:
                pass
            self.poll_after_id = None
        try:
            self.serial.disconnect()
        except Exception:
            pass
        self.connected = False
        try:
            self.root.quit()
        except Exception:
            pass
        self.root.destroy()


def run() -> None:
    root = tk.Tk()
    app = ControlLabApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    run()
