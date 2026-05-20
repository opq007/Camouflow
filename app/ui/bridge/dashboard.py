"""Dashboard bridge for QML."""

from __future__ import annotations

import json

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from app.storage.db import db_get_accounts, db_get_scenarios, db_get_setting
from app.ui.bridge.models import DictListModel
from app.ui.dashboard_data import build_dashboard_metrics


class DashboardBridge(QObject):
    changed = pyqtSignal()

    def __init__(self, profiles_bridge=None, app_state=None, parent=None) -> None:
        super().__init__(parent)
        self._profiles_bridge = profiles_bridge
        self._activity = DictListModel(["type", "title", "desc", "time"], parent=self)
        self._running = DictListModel(["name", "browser", "proxy", "uptime", "color"], parent=self)
        self._metrics = {}
        if app_state is not None:
            app_state.refreshRequested.connect(self.refresh)
        if profiles_bridge is not None:
            profiles_bridge.countsChanged.connect(self.refresh)
        self.refresh()

    @pyqtProperty(QObject, constant=True)
    def activityModel(self) -> QObject:  # noqa: N802
        return self._activity

    @pyqtProperty(QObject, constant=True)
    def runningModel(self) -> QObject:  # noqa: N802
        return self._running

    @pyqtProperty(int, notify=changed)
    def profiles(self) -> int:
        return int(self._metrics.get("profiles", 0))

    @pyqtProperty(int, notify=changed)
    def running(self) -> int:
        return int(self._metrics.get("running", 0))

    @pyqtProperty(int, notify=changed)
    def scenarios(self) -> int:
        return int(self._metrics.get("scenarios", 0))

    @pyqtProperty(int, notify=changed)
    def proxies(self) -> int:
        return int(self._metrics.get("proxy_total", 0))

    @pyqtSlot()
    def refresh(self) -> None:
        proxy_pools = {}
        try:
            proxy_pools = json.loads(db_get_setting("proxy_pools") or "{}")
        except Exception:
            proxy_pools = {}
        live = self._profiles_bridge.live_browsers() if self._profiles_bridge is not None else {}
        self._metrics = build_dashboard_metrics(db_get_accounts(), db_get_scenarios(), proxy_pools, live)
        self._activity.set_rows([
            {"type": "success", "title": "System ready", "desc": "CamouFlow QML interface loaded", "time": "now"},
            {"type": "info", "title": f"{self.profiles} profiles loaded", "desc": "Profiles storage synchronized", "time": "now"},
            {"type": "warning", "title": f"{self.proxies} proxies configured", "desc": "Proxy pools available", "time": "now"},
            {"type": "info", "title": f"{self.scenarios} scenarios", "desc": "Automation workflows ready", "time": "now"},
        ])
        rows = []
        for name, browser in live.items():
            rows.append({"name": name, "browser": getattr(browser, "browser_engine", "Camoufox"), "proxy": getattr(browser, "proxy", "None") or "None", "uptime": "live", "color": "#06b6d4"})
        self._running.set_rows(rows)
        self.changed.emit()
