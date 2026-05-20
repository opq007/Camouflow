"""Settings bridge for QML."""

from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from app.storage.db import DATA_ROOT, db_get_setting, db_set_setting
from app.ui.bridge.models import DictListModel


class SettingsBridge(QObject):
    changed = pyqtSignal()
    message = pyqtSignal(str)

    def __init__(self, app_state=None, parent=None) -> None:
        super().__init__(parent)
        self._app_state = app_state
        self._vars_model = DictListModel(["key", "type", "value"], parent=self)
        self._stages_model = DictListModel(["name"], parent=self)
        if app_state is not None:
            app_state.refreshRequested.connect(self.refresh)
        self.refresh()

    @pyqtProperty(str, notify=changed)
    def dataRoot(self) -> str:  # noqa: N802
        return str(DATA_ROOT)

    @pyqtProperty(QObject, constant=True)
    def variablesModel(self) -> QObject:  # noqa: N802
        return self._vars_model

    @pyqtProperty(QObject, constant=True)
    def stagesModel(self) -> QObject:  # noqa: N802
        return self._stages_model

    @pyqtProperty(bool, notify=changed)
    def debugMode(self) -> bool:  # noqa: N802
        return (db_get_setting("general_debug_mode") or "").lower() in {"1", "true", "yes", "on"}

    def _emit_message(self, text: str) -> None:
        self.message.emit(text)
        if self._app_state is not None:
            self._app_state.notify(text)

    def _load_vars(self) -> dict:
        try:
            data = json.loads(db_get_setting("shared_variables") or "{}")
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _load_stages(self) -> list:
        try:
            data = json.loads(db_get_setting("stages_json") or "[]")
            return data if isinstance(data, list) else []
        except Exception:
            return []

    @pyqtSlot()
    def refresh(self) -> None:
        vars_data = self._load_vars()
        rows = []
        for key, payload in sorted(vars_data.items()):
            if isinstance(payload, dict):
                typ = str(payload.get("type") or "string")
                val = payload.get("value")
            else:
                typ = "string"
                val = payload
            if isinstance(val, list):
                val = ", ".join(map(str, val))
            rows.append({"key": str(key), "type": typ, "value": str(val or "")})
        self._vars_model.set_rows(rows)
        self._stages_model.set_rows([{"name": str(name)} for name in sorted(map(str, self._load_stages()))])
        self.changed.emit()

    @pyqtSlot(str, str, str)
    def saveVariable(self, key: str, typ: str, value: str) -> None:  # noqa: N802
        key = str(key or "").strip()
        if not key:
            self._emit_message("Variable key is empty")
            return
        typ = str(typ or "string")
        data = self._load_vars()
        val = [line.strip() for line in str(value or "").splitlines() if line.strip()] if typ == "list" else str(value or "")
        data[key] = {"type": typ, "value": val}
        db_set_setting("shared_variables", json.dumps(data, ensure_ascii=False))
        self._emit_message(f"Variable {key} saved")
        self.refresh()

    @pyqtSlot(str)
    def deleteVariable(self, key: str) -> None:  # noqa: N802
        data = self._load_vars()
        data.pop(str(key or ""), None)
        db_set_setting("shared_variables", json.dumps(data, ensure_ascii=False))
        self.refresh()

    @pyqtSlot(str, result="QVariant")
    def getVariable(self, key: str) -> dict:  # noqa: N802
        payload = self._load_vars().get(str(key or ""))
        if isinstance(payload, dict):
            value = payload.get("value", "")
            if isinstance(value, list):
                value = "\n".join(map(str, value))
            return {"key": str(key or ""), "type": str(payload.get("type") or "string"), "value": str(value or "")}
        if payload is None:
            return {}
        return {"key": str(key or ""), "type": "string", "value": str(payload)}

    @pyqtSlot(str)
    def addStage(self, name: str) -> None:  # noqa: N802
        name = str(name or "").strip()
        if not name:
            return
        stages = self._load_stages()
        if name not in stages:
            stages.append(name)
            db_set_setting("stages_json", json.dumps(stages, ensure_ascii=False))
        self.refresh()

    @pyqtSlot(str)
    def deleteStage(self, name: str) -> None:  # noqa: N802
        stages = [item for item in self._load_stages() if str(item) != str(name)]
        db_set_setting("stages_json", json.dumps(stages, ensure_ascii=False))
        self.refresh()

    @pyqtSlot(bool)
    def setDebugMode(self, enabled: bool) -> None:  # noqa: N802
        db_set_setting("general_debug_mode", "true" if enabled else "false")
        self.changed.emit()
