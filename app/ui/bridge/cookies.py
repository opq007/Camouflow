"""Cookies page bridge."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from app.storage.db import clear_profile_cookies, db_get_accounts
from app.ui.bridge.models import DictListModel


class CookiesBridge(QObject):
    modelChanged = pyqtSignal()
    message = pyqtSignal(str)

    def __init__(self, app_state=None, parent=None) -> None:
        super().__init__(parent)
        self._app_state = app_state
        self._model = DictListModel(["name", "stage", "proxy"], parent=self)
        if app_state is not None:
            app_state.refreshRequested.connect(self.refresh)
        self.refresh()

    @pyqtProperty(QObject, constant=True)
    def model(self) -> QObject:
        return self._model

    def _emit_message(self, text: str) -> None:
        self.message.emit(text)
        if self._app_state is not None:
            self._app_state.notify(text)

    @pyqtSlot()
    def refresh(self) -> None:
        self._model.set_rows([
            {"name": str(acc.get("name") or ""), "stage": str(acc.get("stage") or "No tag"), "proxy": str(acc.get("proxy_pool") or "No proxy")}
            for acc in db_get_accounts()
        ])
        self.modelChanged.emit()

    @pyqtSlot(str)
    def clearCookies(self, name: str) -> None:  # noqa: N802
        name = str(name or "")
        if not name:
            return
        try:
            removed = clear_profile_cookies(name)
            self._emit_message(f"Profile data cleared for {name}" if removed else f"No profile data for {name}")
        except Exception as exc:
            self._emit_message(f"Cannot clear profile data: {exc}")
        self.refresh()
