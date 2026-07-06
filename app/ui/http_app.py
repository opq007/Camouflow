"""HTTP application bootstrap for CamouFlow (replaces QML)."""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path

import uvicorn

LOGGER = logging.getLogger(__name__)


def _resource_path(relative: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve() / relative
    return Path(__file__).resolve().parents[2] / relative


def _find_free_port(start: int = 8520, max_attempts: int = 20) -> int:
    for port in range(start, start + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 8520


def run_http_app(argv: list[str] | None = None) -> int:
    """Start the FastAPI server and open the system browser."""

    static_dir = _resource_path("app/static")
    if not static_dir.exists():
        static_dir.mkdir(parents=True, exist_ok=True)

    port = _find_free_port()
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    # Mount static files before starting
    from app.server import app, mount_static
    mount_static(static_dir)

    LOGGER.info("CamouFlow server starting at %s", url)

    # Open browser after a short delay
    def _open_browser() -> None:
        import time
        time.sleep(0.5)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()

    # Run uvicorn in the main thread
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="warning",
            access_log=False,
        )
    except KeyboardInterrupt:
        pass
    return 0