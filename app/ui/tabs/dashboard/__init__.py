from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from app.ui.icons import icon_pixmap, lucide_icon
from app.ui.style import create_card


def _stat_card(parent: QWidget, title: str, value: str, icon_name: str, color: str) -> tuple[QFrame, QLabel]:
    card = QFrame(parent)
    card.setObjectName("statCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(10)

    icon = QLabel(card)
    icon.setPixmap(icon_pixmap(icon_name, "#ffffff", 24))
    icon.setFixedSize(52, 52)
    icon.setProperty("class", "pillLabel")
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignLeft)

    value_label = QLabel(value, card)
    value_label.setProperty("class", "statValue")
    layout.addWidget(value_label)

    title_label = QLabel(title, card)
    title_label.setProperty("class", "statLabel")
    layout.addWidget(title_label)
    return card, value_label


def build_dashboard_tab(main) -> QWidget:
    tab = QWidget()
    tab.setObjectName("PageViewport")
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(32, 28, 32, 28)
    layout.setSpacing(26)

    header = QFrame(tab)
    header.setObjectName("pageHeader")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(0, 0, 0, 0)

    title_box = QVBoxLayout()
    title = QLabel("Dashboard")
    title.setProperty("class", "heroTitle")
    subtitle = QLabel("Monitor and control your browser automation workspace")
    subtitle.setProperty("class", "muted")
    title_box.addWidget(title)
    title_box.addWidget(subtitle)
    header_layout.addLayout(title_box, 1)

    status = QLabel("● All systems online")
    status.setProperty("class", "pillLabel")
    header_layout.addWidget(status, 0, Qt.AlignmentFlag.AlignTop)
    layout.addWidget(header)

    stats_grid = QGridLayout()
    stats_grid.setSpacing(18)
    main.dashboard_metric_labels = {}
    for idx, (key, label, icon, color) in enumerate(
        [
            ("profiles", "Active Profiles", "user", "#8b5cf6"),
            ("running", "Running Browsers", "globe", "#06b6d4"),
            ("scenarios", "Scenarios", "play", "#f59e0b"),
            ("proxy_healthy", "Healthy Proxies", "network", "#10b981"),
        ]
    ):
        card, value_label = _stat_card(tab, label, "0", icon, color)
        main.dashboard_metric_labels[key] = value_label
        stats_grid.addWidget(card, 0, idx)
    layout.addLayout(stats_grid)

    body = QHBoxLayout()
    body.setSpacing(18)

    activity_card, activity_layout, _ = create_card(tab, "Live Activity")
    activity_hint = QLabel("Recent application events")
    activity_hint.setProperty("class", "muted")
    activity_layout.addWidget(activity_hint)
    main.dashboard_activity_list = QListWidget(activity_card)
    activity_layout.addWidget(main.dashboard_activity_list, 1)
    body.addWidget(activity_card, 2)

    actions_card, actions_layout, _ = create_card(tab, "Quick Actions")
    actions = [
        ("New Profile", main._open_import_dialog, "primary"),
        ("Run Scenario", lambda: main._stack.setCurrentIndex(getattr(main, "_runner_tab_index", 0)), "success"),
        ("Add Proxy Pool", main._add_proxy_pool, "ghost"),
        ("Open Logs", lambda: main._stack.setCurrentIndex(getattr(main, "_logs_tab_index", 0)), "ghost"),
    ]
    for label, callback, css_class in actions:
        btn = QPushButton(label, actions_card)
        if label == "New Profile":
            btn.setIcon(lucide_icon("plus", "#ffffff"))
        elif label == "Run Scenario":
            btn.setIcon(lucide_icon("play", "#ffffff"))
        elif label == "Add Proxy Pool":
            btn.setIcon(lucide_icon("network"))
        else:
            btn.setIcon(lucide_icon("file-text"))
        btn.setProperty("class", css_class)
        btn.clicked.connect(callback)
        actions_layout.addWidget(btn)
    actions_layout.addStretch(1)

    proxy_card, proxy_layout, _ = create_card(actions_card, "Proxy Health")
    main.dashboard_proxy_summary = QLabel("0 proxies")
    main.dashboard_proxy_summary.setProperty("class", "muted")
    proxy_layout.addWidget(main.dashboard_proxy_summary)
    actions_layout.addWidget(proxy_card)
    body.addWidget(actions_card, 1)

    layout.addLayout(body, 1)
    return tab
