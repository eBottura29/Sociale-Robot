import argparse
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import serial
from serial.tools import list_ports


@dataclass
class TestStats:
    passed: int = 0
    failed: int = 0
    skipped: int = 0


def parse_count(line: str) -> Optional[int]:
    if ":" not in line:
        return None
    _, value = line.split(":", 1)
    value = value.strip()
    if not value.isdigit():
        return None
    return int(value)


def choose_port(user_port: Optional[str]) -> str:
    if user_port:
        return user_port

    ports = [p.device for p in list_ports.comports()]
    if not ports:
        raise RuntimeError("No serial ports found.")

    print("Available serial ports:")
    for i, port in enumerate(ports, start=1):
        print(f"{i}. {port}")

    selected = input(f"Select port [1-{len(ports)}] (default 1): ").strip()
    if not selected:
        return ports[0]

    if selected.isdigit():
        idx = int(selected)
        if 1 <= idx <= len(ports):
            return ports[idx - 1]

    raise RuntimeError("Invalid port selection.")


def run_monitor(
    port: str,
    baudrate: int,
    auto_ping: bool,
    continuous: bool,
) -> None:
    stats = TestStats()
    summary_started = False
    summary_pass: Optional[int] = None
    summary_fail: Optional[int] = None
    summary_skip: Optional[int] = None

    with serial.Serial(port=port, baudrate=baudrate, timeout=0.2) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print(f"Connected to {port} @ {baudrate}")
        print("Waiting for hardware test output...")
        print("Press Ctrl+C to stop.\n")

        while True:
            raw = ser.readline()
            if not raw:
                continue

            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {line}")

            if line.startswith("[PASS]"):
                stats.passed += 1
            elif line.startswith("[FAIL]"):
                stats.failed += 1
            elif line.startswith("[SKIP]"):
                stats.skipped += 1

            if auto_ping and ("Optional serial RX test" in line or "Send PING 8 sec" in line):
                ser.write(b"PING\n")
                print(f"[{timestamp}] [TX] PING")

            if "===== HARDWARE TEST SUMMARY =====" in line:
                summary_started = True
                summary_pass = None
                summary_fail = None
                summary_skip = None
                continue

            if summary_started:
                if line.startswith("PASS:"):
                    summary_pass = parse_count(line)
                elif line.startswith("FAIL:"):
                    summary_fail = parse_count(line)
                elif line.startswith("SKIP:"):
                    summary_skip = parse_count(line)
                elif line.startswith("================================="):
                    print("\nSummary:")
                    print(f"PASS: {summary_pass if summary_pass is not None else stats.passed}")
                    print(f"FAIL: {summary_fail if summary_fail is not None else stats.failed}")
                    print(f"SKIP: {summary_skip if summary_skip is not None else stats.skipped}")
                    print("")
                    summary_started = False
                    if not continuous:
                        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Terminal monitor for src/robot/testing/hardware_test.cpp output.")
    parser.add_argument("--port", help="Serial port (example: COM3)")
    parser.add_argument("--baud", type=int, default=9600, help="Baud rate (default: 9600)")
    parser.add_argument(
        "--no-auto-ping",
        action="store_true",
        help="Do not auto-send PING during the optional serial RX test step.",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Keep running after a summary (for repeated SW_C test cycles).",
    )
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="List available serial ports and exit.",
    )
    args = parser.parse_args()

    if args.list_ports:
        ports = [p.device for p in list_ports.comports()]
        if not ports:
            print("No serial ports found.")
            return
        for port in ports:
            print(port)
        return

    try:
        port = choose_port(args.port)
        run_monitor(
            port=port,
            baudrate=args.baud,
            auto_ping=not args.no_auto_ping,
            continuous=args.continuous,
        )
    except KeyboardInterrupt:
        print("\nStopped.")
    except (serial.SerialException, RuntimeError) as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
