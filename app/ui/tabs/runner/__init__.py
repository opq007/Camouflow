from __future__ import annotations

from PyQt6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget

from app.ui.style import create_card


def build_runner_tab(main) -> QWidget:
    tab = QWidget()
    tab.setObjectName("PageViewport")
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(32, 28, 32, 28)
    layout.setSpacing(22)

    title = QLabel("Run Scenarios")
    title.setProperty("class", "heroTitle")
    subtitle = QLabel("Execute automation workflows on selected profiles or whole tags")
    subtitle.setProperty("class", "muted")
    layout.addWidget(title)
    layout.addWidget(subtitle)

    config_card, config_layout, _ = create_card(tab, "Run Configuration")
    row = QHBoxLayout()
    row.addWidget(QLabel("Scenario"))
    main.scenario_run_combo = QComboBox(config_card)
    row.addWidget(main.scenario_run_combo, 2)
    row.addWidget(QLabel("Tag"))
    main.run_stage_combo = QComboBox(config_card)
    main.run_stage_combo.setMinimumWidth(180)
    row.addWidget(main.run_stage_combo, 1)
    row.addWidget(QLabel("Max profiles"))
    main.count_spin = QSpinBox(config_card)
    main.count_spin.setRange(1, 1000)
    main.count_spin.setValue(1)
    row.addWidget(main.count_spin)
    config_layout.addLayout(row)

    hint = QLabel("Use selected profiles from the Profiles page, or run a scenario for every profile in a tag.")
    hint.setProperty("class", "muted")
    config_layout.addWidget(hint)

    actions = QHBoxLayout()
    btn_selected = QPushButton("Run selected profiles", config_card)
    btn_selected.setProperty("class", "primary")
    btn_selected.clicked.connect(main.start_selected_scenario)
    main.btn_run_stage = QPushButton("Run for tag", config_card)
    main.btn_run_stage.setProperty("class", "success")
    main.btn_run_stage.clicked.connect(main.run_scenario_for_stage)
    actions.addWidget(btn_selected)
    actions.addWidget(main.btn_run_stage)
    actions.addStretch(1)
    config_layout.addLayout(actions)
    layout.addWidget(config_card)

    live_card, live_layout, _ = create_card(tab, "Running Sessions")
    main.runner_status_label = QLabel("No active runner tasks")
    main.runner_status_label.setProperty("class", "muted")
    live_layout.addWidget(main.runner_status_label)
    keep_open = QCheckBox("Keep browser windows open after scenario", live_card)
    keep_open.setChecked(True)
    keep_open.setEnabled(False)
    live_layout.addWidget(keep_open)
    layout.addWidget(live_card)
    layout.addStretch(1)
    return tab
