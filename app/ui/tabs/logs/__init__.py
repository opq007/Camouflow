from PyQt6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from app.ui.style import create_card


def build_logs_tab(main) -> QWidget:
    tab = QWidget()
    tab.setObjectName("PageViewport")
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(32, 28, 32, 28)
    layout.setSpacing(22)
    header = QLabel("Logs")
    header.setProperty("class", "heroTitle")
    subtitle = QLabel("Monitor system events and browser activity")
    subtitle.setProperty("class", "muted")
    layout.addWidget(header)
    layout.addWidget(subtitle)
    log_card, log_layout, _ = create_card(tab, "System Events")
    main.log_edit = QTextEdit()
    main.log_edit.setReadOnly(True)
    main.log_edit.setObjectName("logView")
    log_layout.addWidget(main.log_edit)
    layout.addWidget(log_card)
    return tab
