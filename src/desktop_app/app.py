import threading
from datetime import datetime
from collections import deque
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import serial

from config import EMOTIONS
from emotions import EmotionEngine
from llm import LlmEngine
from serial_client import SerialManager


class NierDesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NIER Desktop App")
        self.root.geometry("1100x720")
        self.root.minsize(980, 640)

        self.connected = False
        self.emotion_values = {name: 0 for name in EMOTIONS}
        self.telemetry_vars = {}
        self.debug_vars = {}
        self.debug_enabled = tk.BooleanVar(value=False)
        self.recent_messages = deque(maxlen=3)
        self.conversation_history = []
        self.lcd_scroll_after_id = None
        self.lcd_scroll_index = 0
        self.lcd_scroll_text = ""

        self.logger = AppLogger()
        self.logger.log("APP_START", "Desktop app gestart")

        self.serial = SerialManager(debug_cb=self._on_serial_tx_debug)
        self.llm = LlmEngine(debug_cb=self._on_llm_debug)
        self.emotions = EmotionEngine()

        self._build_style()
        self._build_layout()
        self._reset_stats()
        self._refresh_ports()


    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subheader.TLabel", font=("Segoe UI", 11))
        style.configure("Section.TLabelframe", padding=12)
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 11, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Chat.TText", font=("Consolas", 10))


    def _build_layout(self) -> None:
        root = self.root
        root.columnconfigure(0, weight=1)

        header = ttk.Frame(root, padding=(18, 16, 0, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="NIER - Neural Interactive Emotional Robot", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Desktop app om met de NIER robot te communiceren",
            style="Subheader.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        body = ttk.Frame(root, padding=(18, 8, 0, 18))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self._build_chat_panel(body)
        self._build_status_panel(body)

        root.rowconfigure(1, weight=1)

    def _build_chat_panel(self, parent: ttk.Frame) -> None:
        chat_frame = ttk.Frame(parent)
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        chat_frame.rowconfigure(1, weight=0)
        chat_frame.columnconfigure(0, weight=1)

        chat_header = ttk.Frame(chat_frame)
        chat_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        chat_header.columnconfigure(0, weight=1)

        ttk.Label(chat_header, text="Robot interactie", style="Section.TLabelframe.Label").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(chat_header, text="Stuur bericht en ontvang antwoord", style="Subheader.TLabel").grid(
            row=0, column=1, sticky="e"
        )
        ttk.Checkbutton(
            chat_header,
            text="Debug info tonen",
            variable=self.debug_enabled,
            command=self._toggle_debug_panel,
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.response_frame = ttk.Labelframe(chat_frame, text="Antwoord (PC)", style="Section.TLabelframe")
        self.response_frame.grid(row=1, column=0, sticky="ew")
        self.response_frame.columnconfigure(0, weight=1)
        self.response_label = ttk.Label(
            self.response_frame,
            text="...",
            font=("Segoe UI", 11),
            wraplength=520,
            justify="left",
        )
        self.response_label.grid(row=0, column=0, sticky="w", pady=(4, 4))
        self.response_frame.grid_remove()

        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        input_frame.columnconfigure(0, weight=1)

        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.grid(row=0, column=0, sticky="ew")
        self.message_entry.bind("<Return>", self._on_send)

        ttk.Button(input_frame, text="Versturen", style="Primary.TButton", command=self._on_send).grid(
            row=0, column=1, padx=(8, 0)
        )

        self.lcd_frame = ttk.Labelframe(chat_frame, text="LCD output (2x16)", style="Section.TLabelframe")
        self.lcd_frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        self.lcd_frame.columnconfigure(0, weight=1)

        self.lcd_line1 = ttk.Label(self.lcd_frame, text=" " * 16, font=("Consolas", 12))
        self.lcd_line2 = ttk.Label(self.lcd_frame, text=" " * 16, font=("Consolas", 12))
        self.lcd_line1.grid(row=0, column=0, sticky="w")
        self.lcd_line2.grid(row=1, column=0, sticky="w")
        self.lcd_frame.grid_remove()

        self.debug_frame = ttk.Labelframe(chat_frame, text="Debug informatie", style="Section.TLabelframe")
        self.debug_frame.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        self.debug_frame.columnconfigure(1, weight=1)

        self._debug_row(self.debug_frame, 0, "Antwoord (PC)")
        self._debug_row(self.debug_frame, 1, "LCD regel 1")
        self._debug_row(self.debug_frame, 2, "LCD regel 2")
        self._debug_row(self.debug_frame, 3, "RGB LED")
        self._debug_row(self.debug_frame, 4, "Buzzer")
        self._debug_row(self.debug_frame, 5, "LED matrix")
        self._debug_row(self.debug_frame, 6, "Laatste TX")
        self._debug_row(self.debug_frame, 7, "Laatste RX")

        self.debug_frame.grid_remove()

    def _build_status_panel(self, parent: ttk.Frame) -> None:
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=0, column=1, sticky="nsew")
        status_frame.rowconfigure(2, weight=1)
        status_frame.columnconfigure(0, weight=1)

        connection = ttk.Labelframe(status_frame, text="Seriele verbinding", style="Section.TLabelframe")
        connection.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        connection.columnconfigure(1, weight=1)

        ttk.Label(connection, text="COM-poort").grid(row=0, column=0, sticky="w")
        self.port_var = tk.StringVar(value="")
        self.port_menu = ttk.OptionMenu(connection, self.port_var, "")
        self.port_menu.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(connection, text="Vernieuwen", command=self._refresh_ports).grid(row=0, column=2, padx=(8, 0))

        self.connect_button = ttk.Button(
            connection, text="Verbinden", style="Primary.TButton", command=self._toggle_connection
        )
        self.connect_button.grid(row=1, column=0, pady=(8, 0), sticky="w")

        self.connection_status = ttk.Label(connection, text="Status: Offline")
        self.connection_status.grid(row=1, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(8, 0))

        self.reset_button = ttk.Button(connection, text="Reset", command=self._send_reset, state="disabled")
        self.reset_button.grid(row=2, column=0, pady=(6, 0), sticky="w")
        self.reset_label = ttk.Label(connection, text="Soft reset (staat blijft bewaard)")
        self.reset_label.grid(row=2, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(6, 0))
        self.reset_button.grid_remove()
        self.reset_label.grid_remove()

        emotions_frame = ttk.Labelframe(status_frame, text="Emotie statistieken", style="Section.TLabelframe")
        emotions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        emotions_frame.columnconfigure(1, weight=1)

        self.emotion_bars = {}

        for idx, name in enumerate(EMOTIONS):
            ttk.Label(emotions_frame, text=name).grid(row=idx, column=0, sticky="w")
            bar = ttk.Progressbar(emotions_frame, maximum=100, value=self.emotion_values[name])
            bar.grid(row=idx, column=1, sticky="ew", padx=(8, 8))
            value_label = ttk.Label(emotions_frame, text=f"{self.emotion_values[name]}%")
            value_label.grid(row=idx, column=2, sticky="e")
            self.emotion_bars[name] = (bar, value_label)

        telemetry = ttk.Labelframe(status_frame, text="Robot telemetrie", style="Section.TLabelframe")
        telemetry.grid(row=2, column=0, sticky="nsew")
        telemetry.columnconfigure(1, weight=1)

        self._telemetry_row(telemetry, 0, "Sonar Links", "0 cm")
        self._telemetry_row(telemetry, 1, "Sonar Rechts", "0 cm")
        self._telemetry_row(telemetry, 2, "Dichtste Afstand", "0 cm")
        self._telemetry_row(telemetry, 3, "Navigatie Modus", "Offline")
        self._telemetry_row(telemetry, 4, "Laatste Commando", "-")
        self._telemetry_row(telemetry, 5, "RGB Status", "-")

        battery_frame = ttk.Frame(telemetry)
        battery_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        battery_frame.columnconfigure(1, weight=1)
        ttk.Label(battery_frame, text="Batterij").grid(row=0, column=0, sticky="w")
        self.battery_bar = ttk.Progressbar(battery_frame, maximum=100, value=0)
        self.battery_bar.grid(row=0, column=1, sticky="ew", padx=(8, 0))


    def _telemetry_row(self, parent: ttk.Frame, row: int, label: str, value: str) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        var = tk.StringVar(value=value)
        ttk.Label(parent, textvariable=var).grid(row=row, column=1, sticky="w", padx=(8, 0))
        self.telemetry_vars[label] = var


    def _debug_row(self, parent: ttk.Frame, row: int, label: str) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        var = tk.StringVar(value="-")
        ttk.Label(parent, textvariable=var, wraplength=420, justify="left").grid(
            row=row, column=1, sticky="w", padx=(8, 0)
        )
        self.debug_vars[label] = var


    def _on_send(self, event=None) -> None:
        message = self.message_entry.get().strip()

        if not message:
            return

        self.message_entry.delete(0, "end")
        self.response_label.configure(text="Antwoord wordt berekend...")
        self._set_debug("Laatste TX", f"Lokaal bericht: {message}")
        self.logger.log("USER_MSG", message)
        threading.Thread(target=self._process_message_thread, args=(message,), daemon=True).start()


    def _process_message_thread(self, message: str) -> None:
        try:
            response = self._handle_basic_intent(message)
            if response is None:
                history = list(self.conversation_history)
                response = self.llm.generate_response(message, history=history, emotions=self.emotion_values)
            temp_history = list(self.recent_messages)
            temp_history.append(f"Gebruiker: {message}")
            temp_history.append(f"Robot: {response}")
            context_text = " ".join(temp_history[-3:])
            sentimentscore = self.llm.sentiment_score(context_text)
            emotions = self.emotions.compute(context_text, sentimentscore)
            self.root.after(0, lambda: self._apply_response(message, response, emotions))
        except Exception as exc:
            self.logger.log("ERROR", f"Message verwerking faalde: {exc}")
            self.root.after(0, lambda: self.response_label.configure(text="Er ging iets mis."))


    def _apply_response(self, message: str, response: str, emotions: dict) -> None:
        self.response_label.configure(text=response)
        self._set_debug("Antwoord (PC)", response)
        self.logger.log("ROBOT_MSG", response)
        self._update_lcd(response)
        self._start_lcd_scroll(response)
        self._set_debug("LCD regel 1", self.lcd_line1.cget("text"))
        self._set_debug("LCD regel 2", self.lcd_line2.cget("text"))

        self.recent_messages.append(f"Gebruiker: {message}")
        self.recent_messages.append(f"Robot: {response}")
        self.conversation_history.append(f"Gebruiker: {message}")
        self.conversation_history.append(f"Robot: {response}")

        for name, value in emotions.items():
            self._set_emotion(name, value)

        if self.connected and self.serial.serial_port:
            self._send_line(f"LCD:{self._truncate_for_serial(response)}")
            self._send_line(f"EMO:{self._serialize_emotions(emotions)}")
            self._set_telemetry("Laatste Commando", "LCD/EMO")
        else:
            self._set_telemetry("Laatste Commando", "-")


    def _handle_basic_intent(self, message: str) -> str | None:
        lowered = message.lower()

        if any(phrase in lowered for phrase in ["hoe laat", "tijd is het", "hoe laat is het", "tijd?"]):
            now = datetime.now().strftime("%H:%M:%S")
            return f"Het is {now}."
        
        return None


    def _update_lcd(self, text: str) -> None:
        line1 = text[:16].ljust(16)
        line2 = text[16:32].ljust(16)
        self.lcd_line1.config(text=line1)
        self.lcd_line2.config(text=line2)


    def _start_lcd_scroll(self, text: str) -> None:
        cleaned = text.replace("\n", " ").replace("\r", " ").replace(",", " ").strip()

        if not cleaned:
            cleaned = " "

        self.lcd_scroll_text = cleaned
        self.lcd_scroll_index = 0

        if self.lcd_scroll_after_id:
            self.root.after_cancel(self.lcd_scroll_after_id)
            self.lcd_scroll_after_id = None

        self._schedule_lcd_scroll()


    def _schedule_lcd_scroll(self) -> None:
        if len(self.lcd_scroll_text) <= 32:
            return

        buffer = f"{self.lcd_scroll_text}    {self.lcd_scroll_text}"
        start = self.lcd_scroll_index
        view = buffer[start:start + 32].ljust(32)
        self.lcd_line1.config(text=view[:16])
        self.lcd_line2.config(text=view[16:32])
        self.lcd_scroll_index += 1

        if self.lcd_scroll_index > len(self.lcd_scroll_text):
            self.lcd_scroll_index = 0

        self.lcd_scroll_after_id = self.root.after(450, self._schedule_lcd_scroll)


    def _truncate_for_serial(self, text: str, limit: int = 128) -> str:
        trimmed = text.replace("\n", " ").replace("\r", " ").strip()
        if len(trimmed) <= limit:
            return trimmed
        
        return trimmed[:limit].rstrip()


    def _serialize_emotions(self, emotions: dict) -> str:
        values = [str(emotions.get(name, 0)) for name in EMOTIONS]
        return ",".join(values)


    def _set_emotion(self, name: str, value: int) -> None:
        value = max(0, min(100, value))
        self.emotion_values[name] = value
        bar, label = self.emotion_bars[name]
        bar.configure(value=value)
        label.configure(text=f"{value}%")


    def _toggle_connection(self) -> None:
        if self.connected:
            self._disconnect()
        else:
            self._connect()


    def _connect(self) -> None:
        port = self.port_var.get()

        if not port:
            self.connection_status.configure(text="Status: Geen COM-poort geselecteerd")
            self.logger.log("CONNECT_FAIL", "Geen COM-poort geselecteerd")
            return
        ok, err = self.serial.connect(port)
        if not ok:
            self.connection_status.configure(text=f"Status: Fout - {err}")
            self.logger.log("CONNECT_FAIL", err)
            return

        self.connected = True
        self.connect_button.configure(text="Verbreken")
        self.connection_status.configure(text=f"Status: Verbonden ({port})")
        self.logger.log("CONNECT_OK", f"Verbonden met {port}")
        self.reset_button.configure(state="normal")

        self._reset_stats()
        self._send_line("HELLO")
        self._poll_serial()


    def _disconnect(self) -> None:
        self.connect_button.configure(text="Verbinden")
        self.connection_status.configure(text="Status: Offline")
        self.logger.log("DISCONNECT", "Verbinding verbroken")
        self.reset_button.configure(state="disabled")
        self._safe_stop()


    def _safe_stop(self) -> None:
        self.serial.safe_stop()
        self.connected = False


    def _send_line(self, line: str) -> None:
        self.serial.send_line(line)

    def _send_reset(self) -> None:
        if not self.connected or not self.serial.serial_port:
            self._set_debug("Laatste TX", "RESET (niet verbonden)")
            return
        self._send_line("RESET")
        self._set_telemetry("Laatste Commando", "RESET")


    def _poll_serial(self) -> None:
        if not self.connected or not self.serial.serial_port:
            return
        try:
            while self.serial.serial_port.in_waiting:
                raw = self.serial.serial_port.readline()
                if not raw:
                    break
                try:
                    line = raw.decode("utf-8", errors="ignore").strip()
                except UnicodeDecodeError:
                    continue
                if line:
                    self._handle_line(line)
        except serial.SerialException as exc:
            self.connection_status.configure(text=f"Status: Verbroken - {exc}")
            self.logger.log("SERIAL_ERR", str(exc))
            self._disconnect()
            return

        self.root.after(100, self._poll_serial)


    def _handle_line(self, line: str) -> None:
        self._set_debug("Laatste RX", line)
        self.logger.log("RX", line)

        if line == "READY":
            self._set_telemetry("Navigatie Modus", "Online")
            return

        if line.startswith("ACK:"):
            self._set_telemetry("Laatste Commando", line[4:])
            return

        if line.startswith("STAT:"):
            payload = line[5:]
            parts = payload.split(",")

            if len(parts) >= 5:
                self._set_telemetry("Sonar Links", f"{parts[0]} cm")
                self._set_telemetry("Sonar Rechts", f"{parts[1]} cm")
                self._set_telemetry("Dichtste Afstand", f"{parts[2]} cm")
                self.battery_bar.configure(value=self._safe_int(parts[3]))
                self._set_telemetry("Navigatie Modus", parts[4])

            return

        if line.startswith("OUT:"):
            payload = line[4:]
            parts = payload.split(",")

            if len(parts) >= 6:
                rgb = f"{parts[0]},{parts[1]},{parts[2]}"
                buzzer = "Aan" if parts[3] == "1" else "Uit"
                matrix = parts[4]
                lcd = ",".join(parts[5:]).strip()

                self._set_debug("RGB LED", rgb)
                self._set_debug("Buzzer", buzzer)
                self._set_debug("LED matrix", matrix)
                self._set_debug("LCD regel 1", lcd[:16].ljust(16))
                self._set_debug("LCD regel 2", lcd[16:32].ljust(16))
                self._update_lcd(lcd)
                self._set_telemetry("RGB Status", rgb)
                
            return
        
        if line.startswith("EMO:"):
            payload = line[4:]
            parts = payload.split(",")

            if len(parts) >= 8:
                for name, value in zip(EMOTIONS, parts[:8]):
                    self._set_emotion(name, self._safe_int(value))


    def _set_telemetry(self, label: str, value: str) -> None:
        var = self.telemetry_vars.get(label)
        if var:
            var.set(value)


    def _set_debug(self, label: str, value: str) -> None:
        var = self.debug_vars.get(label)
        if var:
            var.set(value)

    def _on_serial_tx_debug(self, msg: str) -> None:
        self._set_debug("Laatste TX", msg)
        self.logger.log("TX", msg)

    def _on_llm_debug(self, msg: str) -> None:
        self.root.after(0, lambda: self._set_debug("Laatste RX", msg))
        self.logger.log("LLM", msg)

    def _toggle_debug_panel(self) -> None:
        if self.debug_enabled.get():
            self.debug_frame.grid()
            self.lcd_frame.grid()
            self.response_frame.grid()
            self.reset_button.grid()
            self.reset_label.grid()
        else:
            self.debug_frame.grid_remove()
            self.lcd_frame.grid_remove()
            self.response_frame.grid_remove()
            self.reset_button.grid_remove()
            self.reset_label.grid_remove()


    def _safe_int(self, value: str) -> int:
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

        if self.port_var.get() not in ports:
            self.port_var.set(ports[0])


    def _reset_stats(self) -> None:
        self.emotions.reset()

        for name in EMOTIONS:
            self._set_emotion(name, 0)

        self._set_telemetry("Sonar Links", "0 cm")
        self._set_telemetry("Sonar Rechts", "0 cm")
        self._set_telemetry("Dichtste Afstand", "0 cm")
        self._set_telemetry("Navigatie Modus", "Offline")
        self._set_telemetry("Laatste Commando", "-")
        self._set_telemetry("RGB Status", "-")

        self.battery_bar.configure(value=0)
        self.response_label.configure(text="...")

        self._set_debug("Antwoord (PC)", "-")
        self._set_debug("LCD regel 1", " " * 16)
        self._set_debug("LCD regel 2", " " * 16)
        self._set_debug("RGB LED", "-")
        self._set_debug("Buzzer", "-")
        self._set_debug("LED matrix", "-")
        self._set_debug("Laatste TX", "-")
        self._set_debug("Laatste RX", "-")

        if self.lcd_scroll_after_id:
            self.root.after_cancel(self.lcd_scroll_after_id)
            self.lcd_scroll_after_id = None

        self.lcd_scroll_text = ""
        self.lcd_scroll_index = 0


    def _on_close(self) -> None:
        self._safe_stop()
        self.logger.log("APP_STOP", "Desktop app afgesloten")
        self.root.destroy()


class AppLogger:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        base_dir = Path(__file__).resolve().parents[2]
        self.log_dir = base_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = self.log_dir / f"session_{timestamp}.log"


    def log(self, category: str, message: str) -> None:
        if message is None:
            return
        line = f"{datetime.now().isoformat(timespec='seconds')} [{category}] {message}\n"
        with self.lock:
            self.log_path.open("a", encoding="utf-8").write(line)


def run_app() -> None:
    root = tk.Tk()
    app = NierDesktopApp(root)
    root.protocol("WM_DELETE_WINDOW", app._on_close)
    root.mainloop()
