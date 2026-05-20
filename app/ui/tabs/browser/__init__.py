from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.ui.style import create_card


def build_browser_tab(main) -> QWidget:
    tab = QWidget()
    tab.setObjectName("PageViewport")
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)

    scroll = QScrollArea(tab)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    layout.addWidget(scroll)

    viewport = QWidget()
    scroll.setWidget(viewport)
    content = QVBoxLayout(viewport)
    content.setContentsMargins(32, 28, 32, 28)
    content.setSpacing(22)

    header = QFrame(viewport)
    header.setObjectName("pageHeader")
    header_layout = QVBoxLayout(header)
    header_layout.setContentsMargins(0, 0, 0, 0)
    title = QLabel("Browser")
    title.setProperty("class", "heroTitle")
    subtitle = QLabel("Configure Camoufox and CloakBrowser defaults applied to profiles")
    subtitle.setProperty("class", "muted")
    header_layout.addWidget(title)
    header_layout.addWidget(subtitle)
    content.addWidget(header)

    card, card_layout, _ = create_card(viewport, "Engine Defaults")
    controls, tabs_widget = main._build_camoufox_controls(card)
    card_layout.addWidget(tabs_widget)

    engine_combo = controls.get("browser_engine") if isinstance(controls, dict) else None
    if engine_combo is not None:
        engine_combo.currentIndexChanged.connect(
            lambda _: main._handle_browser_engine_selection(engine_combo.currentData())
        )

    buttons = QHBoxLayout()
    save_btn = QPushButton("Save defaults", card)
    save_btn.setProperty("class", "primary")
    reset_btn = QPushButton("Reset to recommended", card)
    reset_btn.setProperty("class", "ghost")
    buttons.addWidget(save_btn)
    buttons.addWidget(reset_btn)
    buttons.addStretch(1)
    card_layout.addLayout(buttons)
    content.addWidget(card)
    content.addStretch(1)

    main._camoufox_controls = controls
    main._apply_camoufox_defaults_to_form()
    save_btn.clicked.connect(main._save_camoufox_defaults)
    reset_btn.clicked.connect(main._reset_camoufox_defaults)
    return tab
