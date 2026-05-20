"""Shared QML application state."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot


class AppState(QObject):
    currentPageChanged = pyqtSignal()
    messageChanged = pyqtSignal()
    refreshRequested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_page = "Dashboard"
        self._message = "Ready"

    @pyqtProperty(str, notify=currentPageChanged)
    def currentPage(self) -> str:  # noqa: N802
        return self._current_page

    @pyqtProperty(str, notify=messageChanged)
    def message(self) -> str:
        return self._message

    @pyqtSlot(str)
    def setPage(self, page: str) -> None:  # noqa: N802
        page = str(page or "Dashboard")
        if page == self._current_page:
            return
        self._current_page = page
        self.currentPageChanged.emit()

    @pyqtSlot(str)
    def notify(self, message: str) -> None:
        self._message = str(message or "")
        self.messageChanged.emit()

    @pyqtSlot()
    def refreshAll(self) -> None:  # noqa: N802
        self.refreshRequested.emit()
