from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from app.storage.db import db_get_accounts
from app.ui.style import create_card


def build_cookies_tab(main) -> QWidget:
    tab = QWidget()
    tab.setObjectName("PageViewport")
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(32, 28, 32, 28)
    layout.setSpacing(22)

    title = QLabel("Cookies")
    title.setProperty("class", "heroTitle")
    subtitle = QLabel("Inspect, import, export or clear profile cookies from real profile storage")
    subtitle.setProperty("class", "muted")
    layout.addWidget(title)
    layout.addWidget(subtitle)

    card, card_layout, _ = create_card(tab, "Profiles")
    main.cookies_profile_list = QListWidget(card)
    card_layout.addWidget(main.cookies_profile_list, 1)

    actions = QHBoxLayout()
    btn_open = QPushButton("Open cookies editor", card)
    btn_open.setProperty("class", "primary")
    btn_clear = QPushButton("Clear selected profile data", card)
    btn_clear.setProperty("class", "danger")
    btn_refresh = QPushButton("Refresh", card)
    btn_refresh.setProperty("class", "ghost")
    actions.addWidget(btn_open)
    actions.addWidget(btn_clear)
    actions.addWidget(btn_refresh)
    actions.addStretch(1)
    card_layout.addLayout(actions)
    layout.addWidget(card, 1)

    def selected_profile() -> str:
        item = main.cookies_profile_list.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole) or "") if item else ""

    def open_editor() -> None:
        account_name = selected_profile()
        if account_name:
            main._show_profile_settings(account_name)

    btn_open.clicked.connect(open_editor)
    btn_clear.clicked.connect(lambda: main._clear_profile_data(selected_profile()) if selected_profile() else None)
    btn_refresh.clicked.connect(main._refresh_cookies_profile_list)
    main._refresh_cookies_profile_list()
    return tab


def refresh_cookies_profile_list(main) -> None:
    widget = getattr(main, "cookies_profile_list", None)
    if widget is None:
        return
    current = widget.currentItem().data(Qt.ItemDataRole.UserRole) if widget.currentItem() else None
    widget.clear()
    for account in db_get_accounts():
        name = str(account.get("name") or account.get("email") or "").strip()
        if not name:
            continue
        stage = str(account.get("stage") or "No tag")
        proxy = str(account.get("proxy_pool") or "No proxy pool")
        item = QListWidgetItem(f"{name}  •  {stage}  •  {proxy}")
        item.setData(Qt.ItemDataRole.UserRole, name)
        widget.addItem(item)
        if current == name:
            widget.setCurrentItem(item)
