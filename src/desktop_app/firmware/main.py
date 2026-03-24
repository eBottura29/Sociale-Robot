import faulthandler
from datetime import datetime
from pathlib import Path

from app import run_app


def _enable_native_crash_logging() -> None:
    try:
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_path = log_dir / f"native_crash_{ts}.log"
        crash_file = crash_path.open("a", encoding="utf-8")
        faulthandler.enable(file=crash_file, all_threads=True)
    except Exception:
        # Keep startup robust if crash logging can't be configured.
        pass


if __name__ == "__main__":
    _enable_native_crash_logging()
    run_app()
