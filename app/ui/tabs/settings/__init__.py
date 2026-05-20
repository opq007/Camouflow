"""Settings tab for global configuration."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.storage.db import db_get_setting, db_set_setting
from app.ui.style import available_themes


def build_settings_tab(main) -> QWidget:
    tab = QWidget()
    tab.setObjectName("PageViewport")
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    scroll = QScrollArea(tab)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    layout.addWidget(scroll)

    viewport = QWidget()
    scroll.setWidget(viewport)

    content_layout = QVBoxLayout(viewport)
    content_layout.setContentsMargins(32, 28, 32, 28)
    content_layout.setSpacing(22)

    title = QLabel("Settings")
    title.setProperty("class", "heroTitle")
    subtitle = QLabel("Configure global application preferences")
    subtitle.setProperty("class", "muted")
    content_layout.addWidget(title)
    content_layout.addWidget(subtitle)

    card = QFrame(viewport)
    card.setObjectName("settingsCard")
    card_layout = QVBoxLayout(card)
    card_layout.setSpacing(16)

    intro = QLabel("Configure global application preferences.")
    intro.setWordWrap(True)
    card_layout.addWidget(intro)

    debug_mode_row = QHBoxLayout()
    debug_mode_label = QLabel("General")
    debug_mode_label.setProperty("class", "cardTitle")
    debug_mode_row.addWidget(debug_mode_label)
    debug_mode_row.addStretch(1)
    card_layout.addLayout(debug_mode_row)

    debug_check = QCheckBox("General debug mode (scenario debugger)", card)
    debug_check.setToolTip(
        "When enabled, running a scenario opens a separate debugger window with pause/stop/jump and hot-reload."
    )
    raw_debug = (db_get_setting("general_debug_mode") or "").strip().lower()
    debug_check.setChecked(raw_debug in {"1", "true", "yes", "on"})
    debug_check.stateChanged.connect(
        lambda state: db_set_setting(
            "general_debug_mode",
            "1"
            if (state == Qt.CheckState.Checked or state == Qt.CheckState.Checked.value)
            else "0",
        )
    )
    card_layout.addWidget(debug_check)

    appearance_row = QHBoxLayout()
    appearance_label = QLabel("Appearance")
    appearance_label.setProperty("class", "cardTitle")
    appearance_row.addWidget(appearance_label)
    theme_combo = QComboBox(card)
    for value, label in available_themes():
        theme_combo.addItem(label, value)
    current_theme = getattr(main, "current_theme", None)
    if current_theme:
        idx = theme_combo.findData(current_theme)
        if idx >= 0:
            theme_combo.setCurrentIndex(idx)
    theme_combo.currentIndexChanged.connect(lambda _: main._handle_theme_selection(theme_combo.currentData()))
    appearance_row.addWidget(theme_combo, 0)
    appearance_row.addStretch(1)
    card_layout.addLayout(appearance_row)
    main._theme_combo = theme_combo

    content_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignTop)
    content_layout.addStretch(1)
    return tab
