from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout, QWidget


PREMIUM_DARK_STYLE_SHEET = """
* {
    font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
    color: #e8e8f0;
    font-size: 13px;
}
QMainWindow, QWidget#CentralContainer {
    background: #0b0b14;
}
QWidget#AppShell {
    background: #0b0b14;
}
QFrame#sidebar {
    background: #0d0d14;
    border-right: 1px solid rgba(255,255,255,0.06);
}
QFrame#sidebarLogo {
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
QLabel[class~="appTitle"] {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.4px;
}
QLabel[class~="logoMark"] {
    border-radius: 10px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #8b5cf6, stop:1 #06b6d4);
}
QPushButton[class~="nav"] {
    background: transparent;
    color: #b0b0c8;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
}
QPushButton[class~="nav"]:hover {
    background: rgba(255,255,255,0.05);
    color: #e8e8f0;
}
QPushButton[class~="nav"]:checked {
    background: rgba(139,92,246,0.16);
    color: #a78bfa;
    border-color: rgba(139,92,246,0.24);
}
QFrame#systemStatus {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
}
QWidget#PageViewport {
    background: transparent;
}
QFrame#scenarioLeftPanel, QFrame#scenarioRightPanel {
    background: #13131f;
    border: none;
}
QFrame#scenarioLeftPanel {
    border-right: 1px solid rgba(255,255,255,0.06);
}
QFrame#scenarioRightPanel {
    border-left: 1px solid rgba(255,255,255,0.06);
}
QFrame#scenarioCenterPanel {
    background: #16162a;
    border: none;
}
QFrame#scenarioMapHeader {
    background: #13131f;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
QPushButton#templateButton {
    text-align: left;
    min-height: 48px;
    padding: 8px 12px;
    border-radius: 12px;
    background: rgba(22,22,42,0.86);
    border: 1px solid rgba(255,255,255,0.08);
    color: #e8e8f0;
    font-weight: 700;
}
QPushButton#templateButton:hover {
    border-color: rgba(139,92,246,0.45);
    background: rgba(139,92,246,0.10);
}
QListWidget#scenarioLibrary, QListWidget#variablesList {
    background: transparent;
    border: none;
    padding: 0;
}
QListWidget#scenarioLibrary::item, QListWidget#variablesList::item {
    min-height: 32px;
    margin: 4px 0;
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(22,22,42,0.80);
    color: #b0b0c8;
}
QListWidget#scenarioLibrary::item:selected, QListWidget#variablesList::item:selected {
    background: rgba(139,92,246,0.18);
    color: #a78bfa;
    border: 1px solid rgba(139,92,246,0.30);
}
QLabel#nodePropertiesEmpty {
    background: rgba(22,22,42,0.78);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
}
QFrame#totalStepsCard {
    background: rgba(22,22,42,0.78);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
}
QLabel#totalStepsBadge {
    min-width: 38px;
    max-width: 38px;
    min-height: 38px;
    max-height: 38px;
    border-radius: 19px;
    background: #8b5cf6;
    color: #ffffff;
    font-size: 16px;
    font-weight: 800;
}
QFrame#pageHeader {
    background: transparent;
    border: none;
}
QFrame#card, QFrame#settingsCard, QFrame#statCard, QFrame#quickAction {
    background: rgba(22,22,42,0.72);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
}
QFrame#card:hover, QFrame#statCard:hover, QFrame#quickAction:hover {
    border-color: rgba(139,92,246,0.35);
}
QFrame#topBar {
    background: rgba(22,22,42,0.72);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
}
QWidget#profileRow {
    background: rgba(22,22,42,0.55);
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.07);
}
QWidget#profileRow[selected="true"] {
    background: rgba(139,92,246,0.14);
    border-color: rgba(139,92,246,0.35);
}
QWidget#profileRow:hover {
    border-color: rgba(139,92,246,0.35);
}
QLabel[class~="heroTitle"] {
    font-size: 34px;
    line-height: 44px;
    font-weight: 700;
    letter-spacing: -0.8px;
    color: #f4f4fb;
}
QLabel[class~="sectionTitle"] {
    font-size: 22px;
    font-weight: 700;
    color: #f4f4fb;
}
QLabel[class~="cardTitle"] {
    font-size: 15px;
    font-weight: 700;
    color: #f4f4fb;
}
QLabel[class~="muted"] {
    color: #b0b0c8;
}
QLabel[class~="subtle"] {
    color: #7a7a92;
}
QLabel[class~="statValue"] {
    font-size: 32px;
    font-weight: 800;
    color: #ffffff;
}
QLabel[class~="statLabel"] {
    color: #b0b0c8;
    font-weight: 600;
}
QLabel[class~="columnHeader"] {
    color: #7a7a92;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
}
QLabel[class~="avatarBadge"] {
    border-radius: 12px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #8b5cf6, stop:1 #06b6d4);
    color: #ffffff;
    font-weight: 800;
}
QLabel[class~="pillLabel"], QLabel[class~="tagLabel"] {
    padding: 5px 10px;
    border-radius: 10px;
    background: rgba(139,92,246,0.15);
    color: #c4b5fd;
}
QPushButton {
    border-radius: 12px;
    border: 1px solid rgba(139,92,246,0.22);
    padding: 9px 16px;
    font-weight: 700;
    background: rgba(139,92,246,0.14);
    color: #c4b5fd;
}
QPushButton:hover {
    background: rgba(139,92,246,0.22);
    border-color: rgba(139,92,246,0.45);
}
QPushButton:pressed {
    background: rgba(124,58,237,0.34);
}
QPushButton:disabled {
    background: rgba(255,255,255,0.03);
    color: #55556a;
    border-color: rgba(255,255,255,0.04);
}
QPushButton[class~="primary"] {
    background: #8b5cf6;
    color: #ffffff;
    border: 1px solid #8b5cf6;
}
QPushButton[class~="primary"]:hover {
    background: #a78bfa;
    border-color: #a78bfa;
}
QPushButton[class~="success"] {
    background: rgba(6,182,212,0.18);
    color: #67e8f9;
    border-color: rgba(6,182,212,0.32);
}
QPushButton[class~="danger"] {
    background: rgba(239,68,68,0.14);
    color: #fca5a5;
    border-color: rgba(239,68,68,0.26);
}
QPushButton[class~="danger"]:hover {
    background: rgba(239,68,68,0.22);
}
QPushButton[class~="ghost"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    color: #d7d7e7;
}
QPushButton[class~="tagChip"] {
    background: rgba(255,255,255,0.04);
    color: #b0b0c8;
    padding: 6px 12px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.08);
}
QPushButton[class~="tagChip"]:checked {
    background: rgba(139,92,246,0.22);
    color: #ffffff;
    border-color: rgba(139,92,246,0.5);
}
QPushButton[class~="actionCategoryBtn"],
QPushButton[class~="actionOptionBtn"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    color: #d7d7e7;
}
QPushButton[class~="actionCategoryBtn"]:checked,
QPushButton[class~="actionOptionBtn"]:checked {
    background: rgba(139,92,246,0.24);
    border-color: rgba(139,92,246,0.55);
    color: #ffffff;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QListWidget, QTableWidget, QSpinBox, QDoubleSpinBox {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 8px;
    selection-background-color: #8b5cf6;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QListWidget:focus, QTableWidget:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: rgba(139,92,246,0.55);
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #13131f;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    selection-background-color: rgba(139,92,246,0.24);
}
QListWidget {
    border-radius: 16px;
}
QListWidget::item {
    margin: 5px 6px;
    padding: 10px;
    border-radius: 12px;
}
QListWidget::item:selected {
    background: rgba(139,92,246,0.20);
}
QListWidget#accountsList::item:selected {
    background: transparent;
}
QHeaderView::section {
    background: rgba(255,255,255,0.04);
    color: #b0b0c8;
    border: none;
    padding: 8px;
    font-weight: 700;
}
QTableWidget {
    gridline-color: rgba(255,255,255,0.06);
}
QMenu {
    background: #13131f;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 12px;
    border-radius: 8px;
}
QMenu::item:selected {
    background: rgba(139,92,246,0.22);
}
QTabWidget::pane {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    background: rgba(22,22,42,0.45);
}
QTabBar::tab {
    background: transparent;
    color: #b0b0c8;
    padding: 9px 14px;
    border-radius: 10px;
}
QTabBar::tab:selected {
    background: rgba(139,92,246,0.20);
    color: #ffffff;
}
QCheckBox {
    spacing: 8px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 4px;
}
QScrollBar::handle:vertical {
    background-color: rgba(139,92,246,0.30);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: rgba(139,92,246,0.45);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    border: none;
    background: transparent;
}
#CamoufoxAutoSet QPushButton {
    padding: 5px 10px;
    border-radius: 8px;
}
"""


DEFAULT_THEME = "premium_dark"

_PREMIUM_DARK_PALETTE = {
    QPalette.ColorRole.Window: "#0b0b14",
    QPalette.ColorRole.Base: "#13131f",
    QPalette.ColorRole.AlternateBase: "#1a1a2e",
    QPalette.ColorRole.Text: "#e8e8f0",
    QPalette.ColorRole.Button: "#1a1a2e",
    QPalette.ColorRole.ButtonText: "#e8e8f0",
    QPalette.ColorRole.Highlight: "#8b5cf6",
    QPalette.ColorRole.HighlightedText: "#ffffff",
}

_THEMES: Dict[str, Dict[str, object]] = {
    "premium_dark": {
        "label": "Premium Dark",
        "stylesheet": PREMIUM_DARK_STYLE_SHEET,
        "palette": _PREMIUM_DARK_PALETTE,
    },
    "camouflow_dark": {
        "label": "Premium Dark",
        "stylesheet": PREMIUM_DARK_STYLE_SHEET,
        "palette": _PREMIUM_DARK_PALETTE,
    },
    "camouflow_light": {
        "label": "Premium Dark",
        "stylesheet": PREMIUM_DARK_STYLE_SHEET,
        "palette": _PREMIUM_DARK_PALETTE,
    },
}


def available_themes() -> List[Tuple[str, str]]:
    return [("premium_dark", "Premium Dark")]


def normalize_theme(theme: Optional[str]) -> str:
    key = str(theme or "").strip().lower()
    return key if key in _THEMES else DEFAULT_THEME


def apply_modern_theme(app: QApplication, theme: str = DEFAULT_THEME) -> str:
    key = normalize_theme(theme)
    theme_data = _THEMES[key]
    palette = QPalette()
    palette_data: Dict[QPalette.ColorRole, str] = theme_data["palette"]  # type: ignore[assignment]
    for role, color in palette_data.items():
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(theme_data["stylesheet"])
    return key


def create_card(
    parent: Optional[QWidget] = None, title: Optional[str] = None
) -> Tuple[QFrame, QVBoxLayout, Optional[QLabel]]:
    frame = QFrame(parent)
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(14)
    heading = None
    if title:
        heading = QLabel(title)
        heading.setProperty("class", "cardTitle")
        layout.addWidget(heading)
    return frame, layout, heading


__all__ = [
    "apply_modern_theme",
    "create_card",
    "available_themes",
    "normalize_theme",
    "DEFAULT_THEME",
]
