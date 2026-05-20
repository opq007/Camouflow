from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QCheckBox,
    QTextEdit,
    QPushButton,
    QListWidget,
    QSpinBox,
    QWidget,
    QLineEdit,
)

from app.ui.icons import lucide_icon
from app.ui.style import create_card


def build_run_tab(main) -> QWidget:
    """Build the profiles page following the newdesign layout."""
    tab = QWidget()
    tab.setObjectName("PageViewport")
    main_layout = QVBoxLayout(tab)
    main_layout.setContentsMargins(32, 28, 32, 28)
    main_layout.setSpacing(22)

    header = QHBoxLayout()
    title_box = QVBoxLayout()
    hero_header = QLabel("Profiles")
    hero_header.setProperty("class", "heroTitle")
    title_box.addWidget(hero_header)
    hero_caption = QLabel("Manage your browser profiles and sessions")
    hero_caption.setProperty("class", "muted")
    title_box.addWidget(hero_caption)
    header.addLayout(title_box, 1)
    share_btn = QPushButton("Shared variables")
    share_btn.setIcon(lucide_icon("settings"))
    share_btn.setProperty("class", "ghost")
    share_btn.clicked.connect(main._open_shared_vars_dialog)
    header.addWidget(share_btn)
    add_btn = QPushButton("Add Profile")
    add_btn.setIcon(lucide_icon("plus", "#ffffff"))
    add_btn.setProperty("class", "primary")
    add_btn.clicked.connect(main._open_import_dialog)
    header.addWidget(add_btn)
    main_layout.addLayout(header)

    stats = QHBoxLayout()
    stats.setSpacing(16)
    total_card, total_layout, _ = create_card(tab)
    total_label = QLabel("Total Profiles")
    total_label.setProperty("class", "statLabel")
    main.profile_count_label = QLabel("0 profiles")
    main.profile_count_label.setProperty("class", "statValue")
    total_layout.addWidget(total_label)
    total_layout.addWidget(main.profile_count_label)
    stats.addWidget(total_card)
    undefined_card, undefined_layout, _ = create_card(tab)
    undefined_label = QLabel("Undefined")
    undefined_label.setProperty("class", "statLabel")
    main.profile_status_label = QLabel("0 undefined")
    main.profile_status_label.setProperty("class", "statValue")
    undefined_layout.addWidget(undefined_label)
    undefined_layout.addWidget(main.profile_status_label)
    stats.addWidget(undefined_card)
    running_card, running_layout, _ = create_card(tab)
    running_label = QLabel("Running")
    running_label.setProperty("class", "statLabel")
    main.profile_running_label = QLabel("0")
    main.profile_running_label.setProperty("class", "statValue")
    running_layout.addWidget(running_label)
    running_layout.addWidget(main.profile_running_label)
    stats.addWidget(running_card)
    main_layout.addLayout(stats)

    list_card, list_layout, _ = create_card(tab)
    header_row = QHBoxLayout()
    header_label = QLabel("Profile Library")
    header_label.setProperty("class", "cardTitle")
    header_row.addWidget(header_label)
    header_row.addStretch()
    list_layout.addLayout(header_row)

    filter_block = QVBoxLayout()
    search_row = QHBoxLayout()
    main.accounts_search_input = QLineEdit()
    main.accounts_search_input.setPlaceholderText("Search profiles...")
    main.accounts_search_input.setProperty("class", "search")
    main.accounts_search_input.textChanged.connect(main._apply_accounts_filter)
    search_row.addWidget(main.accounts_search_input, 1)
    clear_btn = QPushButton("Clear")
    clear_btn.setProperty("class", "ghost")
    clear_btn.clicked.connect(lambda _: main.accounts_search_input.clear())
    search_row.addWidget(clear_btn)
    filter_block.addLayout(search_row)
    chips_row = QHBoxLayout()
    chips_caption = QLabel("Tags")
    chips_caption.setProperty("class", "muted")
    chips_row.addWidget(chips_caption)
    manage_btn = QPushButton("Manage tags")
    manage_btn.setIcon(lucide_icon("settings"))
    manage_btn.setProperty("class", "ghost")
    manage_btn.clicked.connect(main._open_stage_dialog)
    chips_row.addWidget(manage_btn)
    chips_row.addStretch()
    chips_row.addWidget(QLabel("Delete tag"))
    main.delete_tag_combo = QComboBox()
    main.delete_tag_combo.setMinimumWidth(180)
    chips_row.addWidget(main.delete_tag_combo)
    main.delete_tag_proxy_check = QCheckBox("Remove proxies")
    main.delete_tag_proxy_check.setChecked(False)
    chips_row.addWidget(main.delete_tag_proxy_check)
    delete_tag_btn = QPushButton("Delete profiles")
    delete_tag_btn.setIcon(lucide_icon("trash", "#fca5a5"))
    delete_tag_btn.setProperty("class", "danger")
    delete_tag_btn.clicked.connect(main._delete_profiles_by_tag)
    chips_row.addWidget(delete_tag_btn)
    filter_block.addLayout(chips_row)
    chips_widget = QWidget()
    chips_layout = QHBoxLayout(chips_widget)
    chips_layout.setContentsMargins(0, 0, 0, 0)
    chips_layout.setSpacing(8)
    main.stage_filter_layout = chips_layout
    filter_block.addWidget(chips_widget)
    list_layout.addLayout(filter_block)
    columns_row = QHBoxLayout()
    columns = [
        ("Name", 3, Qt.AlignmentFlag.AlignLeft),
        ("Proxy", 2, Qt.AlignmentFlag.AlignLeft),
        ("Tags", 2, Qt.AlignmentFlag.AlignLeft),
        ("Actions", 1, Qt.AlignmentFlag.AlignRight),
    ]
    for title, stretch, align in columns:
        lbl = QLabel(title)
        lbl.setProperty("class", "columnHeader")
        lbl.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        columns_row.addWidget(lbl, stretch)
    list_layout.addLayout(columns_row)
    main.accounts_list = QListWidget()
    main.accounts_list.setObjectName("accountsList")
    main.accounts_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
    main.accounts_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    main.accounts_list.customContextMenuRequested.connect(main._show_account_context_menu)
    main.accounts_list.itemSelectionChanged.connect(main._update_row_selection_styles)
    list_layout.addWidget(main.accounts_list)

    main_layout.addWidget(list_card)

    return tab
