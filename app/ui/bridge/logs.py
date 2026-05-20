"""Logs bridge for QML."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from app.storage.db import DATA_ROOT
from app.ui.bridge.models import DictListModel


class _QmlLogHandler(logging.Handler):
    def __init__(self, bridge: "LogsBridge") -> None:
        super().__init__()
        self._bridge = bridge

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._bridge.append(self.format(record), record.levelname)
        except Exception:
            pass


class LogsBridge(QObject):
    modelChanged = pyqtSignal()
    textChanged = pyqtSignal()

    def __init__(self, app_state=None, parent=None) -> None:
        super().__init__(parent)
        self._model = DictListModel(["level", "text", "time"], parent=self)
        self._rows: List[dict] = []
        self._text = ""
        self._app_state = app_state
        self._install_handler()
        self.refresh()
        if app_state is not None:
            app_state.refreshRequested.connect(self.refresh)

    @pyqtProperty(QObject, constant=True)
    def model(self) -> QObject:
        return self._model

    @pyqtProperty(str, notify=textChanged)
    def text(self) -> str:
        return self._text

    def _install_handler(self) -> None:
        root = logging.getLogger()
        for handler in root.handlers:
            if isinstance(handler, _QmlLogHandler):
                return
        handler = _QmlLogHandler(self)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        root.addHandler(handler)

    def append(self, text: str, level: str = "INFO") -> None:
        row = {"level": str(level), "text": str(text), "time": str(text)[:19]}
        self._rows.append(row)
        self._rows = self._rows[-500:]
        self._model.set_rows(list(reversed(self._rows[-200:])))
        self._text = "\n".join(r["text"] for r in self._rows[-500:])
        self.modelChanged.emit()
        self.textChanged.emit()

    @pyqtSlot()
    def refresh(self) -> None:
        rows: List[dict] = []
        logs_dir = DATA_ROOT / "logs"
        if logs_dir.exists():
            for path in sorted(logs_dir.glob("*.log")):
                try:
                    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
                except Exception:
                    lines = []
                for line in lines:
                    level = "ERROR" if "ERROR" in line else "WARNING" if "WARN" in line else "INFO"
                    rows.append({"level": level, "text": line, "time": line[:19]})
        self._rows = rows[-500:]
        self._model.set_rows(list(reversed(self._rows[-200:])))
        self._text = "\n".join(r["text"] for r in self._rows[-500:])
        self.modelChanged.emit()
        self.textChanged.emit()

    @pyqtSlot()
    def clear(self) -> None:
        self._rows = []
        self._text = ""
        self._model.set_rows([])
        self.modelChanged.emit()
        self.textChanged.emit()
