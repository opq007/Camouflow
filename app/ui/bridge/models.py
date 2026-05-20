"""Qt models shared by the QML UI bridges."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from PyQt6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Qt, pyqtSlot


class DictListModel(QAbstractListModel):
    """A small role-based list model backed by dictionaries."""

    def __init__(self, roles: Sequence[str], rows: Iterable[Dict[str, Any]] | None = None, parent=None) -> None:
        super().__init__(parent)
        self._roles = list(dict.fromkeys(str(role) for role in roles))
        self._role_ids = {Qt.ItemDataRole.UserRole + index + 1: role for index, role in enumerate(self._roles)}
        self._rows: List[Dict[str, Any]] = list(rows or [])

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def data(self, index: QModelIndex, role: int = int(Qt.ItemDataRole.DisplayRole)) -> Any:
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._rows):
            return None
        if role == int(Qt.ItemDataRole.DisplayRole):
            return str(self._rows[index.row()].get(self._roles[0], "")) if self._roles else ""
        name = self._role_ids.get(role)
        if not name:
            return None
        return self._rows[index.row()].get(name)

    def roleNames(self) -> Dict[int, QByteArray]:  # noqa: N802
        return {role: QByteArray(name.encode("utf-8")) for role, name in self._role_ids.items()}

    def set_rows(self, rows: Iterable[Dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = [dict(row) for row in rows]
        self.endResetModel()

    def rows(self) -> List[Dict[str, Any]]:
        return [dict(row) for row in self._rows]

    @pyqtSlot(int, result="QVariant")
    def get(self, row: int) -> Any:
        if 0 <= int(row) < len(self._rows):
            return dict(self._rows[int(row)])
        return {}
