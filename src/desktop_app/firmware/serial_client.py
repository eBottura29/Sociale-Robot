import serial
from serial.tools import list_ports

from config import SERIAL_BAUD, SERIAL_TIMEOUT


class SerialManager:
    def __init__(self, debug_cb=None) -> None:
        self.serial_port = None
        self.debug_cb = debug_cb

    def refresh_ports(self) -> list:
        ports = [port.device for port in list_ports.comports()]
        return ports if ports else [""]

    def connect(self, port: str) -> tuple:
        try:
            self.serial_port = serial.Serial(port=port, baudrate=SERIAL_BAUD, timeout=SERIAL_TIMEOUT)
            return True, ""
        except serial.SerialException as exc:
            self.serial_port = None
            return False, str(exc)

    def disconnect(self) -> None:
        if self.serial_port:
            try:
                self.serial_port.close()
            finally:
                self.serial_port = None

    def safe_stop(self) -> None:
        if self.serial_port and self.serial_port.is_open:
            try:
                self.send_line("STOP")
            except serial.SerialException:
                pass
        self.disconnect()

    def send_line(self, line: str) -> None:
        if not self.serial_port or not self.serial_port.is_open:
            return
        payload = (line + "\n").encode("utf-8")
        self.serial_port.write(payload)
        if self.debug_cb:
            self.debug_cb(line)
