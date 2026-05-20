"""Run page bridge."""

from __future__ import annotations

import logging
import threading

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from app.services.scenario_engine import run_scenario
from app.storage.db import db_get_accounts, db_get_scenario, db_get_scenario_path, db_get_scenarios
from app.ui.bridge.models import DictListModel

LOGGER = logging.getLogger(__name__)


class RunBridge(QObject):
    changed = pyqtSignal()
    message = pyqtSignal(str)

    def __init__(self, app_state=None, parent=None) -> None:
        super().__init__(parent)
        self._app_state = app_state
        self._scenarios = DictListModel(["name", "description"], parent=self)
        self._profiles = DictListModel(["name", "stage"], parent=self)
        self._running = False
        self._status = "Idle"
        if app_state is not None:
            app_state.refreshRequested.connect(self.refresh)
        self.refresh()

    @pyqtProperty(QObject, constant=True)
    def scenariosModel(self) -> QObject:  # noqa: N802
        return self._scenarios

    @pyqtProperty(QObject, constant=True)
    def profilesModel(self) -> QObject:  # noqa: N802
        return self._profiles

    @pyqtProperty(bool, notify=changed)
    def running(self) -> bool:
        return self._running

    @pyqtProperty(str, notify=changed)
    def status(self) -> str:
        return self._status

    def _emit_message(self, text: str) -> None:
        self.message.emit(text)
        if self._app_state is not None:
            self._app_state.notify(text)

    @pyqtSlot()
    def refresh(self) -> None:
        self._scenarios.set_rows([{"name": s.name, "description": s.description or ""} for s in db_get_scenarios()])
        self._profiles.set_rows([{"name": str(a.get("name") or ""), "stage": str(a.get("stage") or "")} for a in db_get_accounts()])
        self.changed.emit()

    @pyqtSlot(str, str, int)
    def run(self, scenario_name: str, profile_name: str, limit: int) -> None:
        if self._running:
            return
        scenario = db_get_scenario(str(scenario_name or ""))
        if not scenario:
            self._emit_message("Select scenario first")
            return
        accounts = db_get_accounts()
        profile_name = str(profile_name or "")
        if profile_name:
            accounts = [a for a in accounts if str(a.get("name") or "") == profile_name]
        max_accounts = max(1, int(limit or 1))
        accounts = accounts[:max_accounts]
        if not accounts:
            self._emit_message("No profiles to run")
            return
        self._running = True
        self._status = f"Running {scenario.name} for {len(accounts)} profile(s)"
        self.changed.emit()
        self._emit_message(self._status)

        def worker() -> None:
            try:
                processed = run_scenario(accounts, scenario, max_accounts=max_accounts, scenario_path=db_get_scenario_path(scenario.name))
                self._status = f"Finished: {len(processed)} profile(s)"
            except Exception as exc:
                LOGGER.exception("Run failed")
                self._status = f"Failed: {exc}"
            self._running = False
            self._emit_message(self._status)
            self.changed.emit()

        threading.Thread(target=worker, daemon=True).start()
