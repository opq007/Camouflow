from typing import List, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QFormLayout,
    QCheckBox,
    QLineEdit,
    QListWidget,
    QPushButton,
    QDoubleSpinBox,
    QSpinBox,
    QTextEdit,
    QWidget,
)

from app.ui.icons import lucide_icon
from app.ui.scenario_editor import ScenarioEditor
from app.ui.style import create_card

ACTION_OPTIONS_FORM: List[Tuple[str, str]] = [
    ("Open URL", "goto"),
    ("HTTP request", "http_request"),
    ("Wait for element", "wait_element"),
    ("Wait for page load", "wait_for_load_state"),
    ("Sleep", "sleep"),
    ("Click element", "click"),
    ("Type text", "type"),
    ("Set variable", "set_var"),
    ("Parse variable", "parse_var"),
    ("Pop from shared", "pop_shared"),
    ("Extract text", "extract_text"),
    ("Write to file", "write_file"),
    ("Compare / if", "compare"),
    ("Open new tab", "new_tab"),
    ("Switch tab", "switch_tab"),
    ("Close tab", "close_tab"),
    ("Set tag", "set_tag"),
    ("Close browser", "end"),
    ("Run another scenario", "run_scenario"),
    ("Log / message", "log"),
]

ACTION_OPTIONS_DIALOG: List[Tuple[str, str]] = [("Start scenario", "start")] + ACTION_OPTIONS_FORM
ACTION_LABELS = {value: label for label, value in ACTION_OPTIONS_DIALOG}


def build_scenarios_tab(main) -> QWidget:
    tab = QWidget()
    tab.setObjectName("PageViewport")
    scenario_layout = QVBoxLayout(tab)
    scenario_layout.setContentsMargins(0, 0, 0, 0)
    scenario_layout.setSpacing(0)

    content = QHBoxLayout()
    content.setContentsMargins(0, 0, 0, 0)
    content.setSpacing(0)
    scenario_layout.addLayout(content, 1)

    left_panel = QFrame(tab)
    left_panel.setObjectName("scenarioLeftPanel")
    left_panel.setFixedWidth(280)
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(16, 16, 14, 16)
    left_layout.setSpacing(14)

    scenario_title = QLabel("Scenario library", left_panel)
    scenario_title.setProperty("class", "cardTitle")
    left_layout.addWidget(scenario_title)

    main.scenario_list_widget = QListWidget()
    main.scenario_list_widget.setObjectName("scenarioLibrary")
    main.scenario_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    main.scenario_list_widget.itemSelectionChanged.connect(main._on_scenario_selected)
    main.scenario_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    main.scenario_list_widget.customContextMenuRequested.connect(main._show_scenario_context_menu)
    main.scenario_list_widget.setMinimumHeight(170)
    left_layout.addWidget(main.scenario_list_widget)

    scenario_buttons = QGridLayout()
    scenario_buttons.setHorizontalSpacing(8)
    scenario_buttons.setVerticalSpacing(8)
    btn_new_scenario = QPushButton("New")
    btn_new_scenario.setProperty("class", "ghost")
    btn_new_scenario.clicked.connect(main._new_scenario)
    btn_load_scenario = QPushButton("Load")
    btn_load_scenario.setProperty("class", "ghost")
    btn_load_scenario.clicked.connect(main._load_selected_scenario)
    btn_save_scenario = QPushButton("Save")
    btn_save_scenario.setIcon(lucide_icon("save"))
    btn_save_scenario.setProperty("class", "success")
    btn_save_scenario.clicked.connect(main._save_scenario)
    btn_duplicate_scenario = QPushButton("Duplicate")
    btn_duplicate_scenario.setProperty("class", "ghost")
    btn_duplicate_scenario.clicked.connect(main._duplicate_selected_scenario)
    btn_delete_scenario = QPushButton("Delete")
    btn_delete_scenario.setProperty("class", "danger")
    btn_delete_scenario.clicked.connect(main._delete_selected_scenario)
    scenario_buttons.addWidget(btn_new_scenario, 0, 0)
    scenario_buttons.addWidget(btn_load_scenario, 0, 1)
    scenario_buttons.addWidget(btn_save_scenario, 1, 0)
    scenario_buttons.addWidget(btn_duplicate_scenario, 1, 1)
    scenario_buttons.addWidget(btn_delete_scenario, 2, 0, 1, 2)
    left_layout.addLayout(scenario_buttons)

    templates_title = QLabel("Action Templates", left_panel)
    templates_title.setProperty("class", "cardTitle")
    left_layout.addWidget(templates_title)
    template_specs = [
        ("🌐", "Navigate", "goto", "goto"),
        ("👆", "Click", "click", "click"),
        ("⌨", "Type Text", "type", "type"),
        ("⏱", "Wait", "wait", "sleep"),
        ("📡", "HTTP Request", "fetch", "http_request"),
        ("🗂", "Tab Control", "tab", "new_tab"),
        ("💾", "Variable", "var", "set_var"),
        ("?", "Condition", "condition", "compare"),
    ]
    for icon, label, fn_name, action in template_specs:
        btn = QPushButton(f"{icon}  {label}\n     {fn_name}()", left_panel)
        btn.setObjectName("templateButton")
        btn.clicked.connect(
            lambda _, value=action: main._insert_step(
                len(main.current_steps),
                {"action": value, "_no_default_links": True, "_ok_links": [], "_err_links": []},
            )
        )
        left_layout.addWidget(btn)
    left_layout.addStretch(1)
    content.addWidget(left_panel)

    center_panel = QFrame(tab)
    center_panel.setObjectName("scenarioCenterPanel")
    center_layout = QVBoxLayout(center_panel)
    center_layout.setContentsMargins(0, 0, 0, 0)
    center_layout.setSpacing(0)
    map_header = QFrame(center_panel)
    map_header.setObjectName("scenarioMapHeader")
    map_header_layout = QHBoxLayout(map_header)
    map_header_layout.setContentsMargins(22, 14, 22, 14)
    action_map_title = QLabel("Action Map", map_header)
    action_map_title.setProperty("class", "sectionTitle")
    map_header_layout.addWidget(action_map_title, 1)
    map_save_btn = QPushButton("Save", map_header)
    map_save_btn.setIcon(lucide_icon("save"))
    map_save_btn.setProperty("class", "ghost")
    map_save_btn.clicked.connect(main._save_scenario)
    map_header_layout.addWidget(map_save_btn)
    map_run_btn = QPushButton("Run Scenario", map_header)
    map_run_btn.setIcon(lucide_icon("play", "#ffffff"))
    map_run_btn.setProperty("class", "primary")
    map_run_btn.clicked.connect(main.start_selected_scenario)
    map_header_layout.addWidget(map_run_btn)
    center_layout.addWidget(map_header)

    main.map_view = ScenarioEditor()
    main.map_view.set_action_labels(ACTION_LABELS)
    main.map_view.on_select = main._on_map_select
    main.map_view.on_add_after = main._on_map_add_after
    main.map_view.on_move = main._on_map_move
    main.map_view.on_drag_end = main._on_map_drag_end
    main.map_view.on_edit = main._on_map_edit
    main.map_view.on_delete = main._on_map_delete
    main.map_view.on_add_detached = main._on_map_add_detached
    center_layout.addWidget(main.map_view, 1)
    content.addWidget(center_panel, 1)

    right_panel = QFrame(tab)
    right_panel.setObjectName("scenarioRightPanel")
    right_panel.setFixedWidth(330)
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(22, 22, 18, 18)
    right_layout.setSpacing(14)
    details_title = QLabel("Details", right_panel)
    details_title.setProperty("class", "cardTitle")
    right_layout.addWidget(details_title)

    name_label = QLabel("Name:", right_panel)
    name_label.setProperty("class", "muted")
    right_layout.addWidget(name_label)
    main.scenario_name_input = QLineEdit()
    right_layout.addWidget(main.scenario_name_input)
    desc_label = QLabel("Description:", right_panel)
    desc_label.setProperty("class", "muted")
    right_layout.addWidget(desc_label)
    main.scenario_description_input = QLineEdit()
    right_layout.addWidget(main.scenario_description_input)

    vars_label = QLabel("Variables in scenario:", right_panel)
    vars_label.setProperty("class", "cardTitle")
    right_layout.addWidget(vars_label)
    main.vars_list = QListWidget()
    main.vars_list.setObjectName("variablesList")
    right_layout.addWidget(main.vars_list)
    add_var_btn = QPushButton("＋  Add Variable", right_panel)
    add_var_btn.setProperty("class", "ghost")
    right_layout.addWidget(add_var_btn)
    props_label = QLabel("Node Properties", right_panel)
    props_label.setProperty("class", "cardTitle")
    right_layout.addWidget(props_label)
    props_empty = QLabel("Select a node to edit its properties", right_panel)
    props_empty.setObjectName("nodePropertiesEmpty")
    props_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
    props_empty.setProperty("class", "muted")
    props_empty.setMinimumHeight(110)
    right_layout.addWidget(props_empty)
    right_layout.addStretch(1)
    total_card = QFrame(right_panel)
    total_card.setObjectName("totalStepsCard")
    total_layout = QHBoxLayout(total_card)
    total_layout.setContentsMargins(14, 12, 14, 12)
    total_badge = QLabel("0", total_card)
    total_badge.setObjectName("totalStepsBadge")
    total_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main.scenario_total_steps_label = total_badge
    total_layout.addWidget(total_badge)
    total_text = QLabel("Total Steps\nin this scenario", total_card)
    total_text.setProperty("class", "muted")
    total_layout.addWidget(total_text, 1)
    right_layout.addWidget(total_card)
    content.addWidget(right_panel)

    # Hidden container keeps logic-only widgets parented so they don't pop as floating windows
    hidden_container = QWidget(tab)
    hidden_container.setVisible(False)
    hidden_layout = QVBoxLayout(hidden_container)

    # Hidden steps list (logic only)
    main.steps_list = QListWidget()
    main.steps_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    main.steps_list.itemSelectionChanged.connect(main._fill_step_form_from_selection)
    main.steps_list.itemActivated.connect(lambda _: None)
    hidden_layout.addWidget(main.steps_list)

    # Hidden form (logic only)
    form = QFormLayout()
    main.step_tag_input = QLineEdit()
    main.row_tag = (QLabel("Tag:"), main.step_tag_input)
    form.addRow(*main.row_tag)

    main.step_action_combo = QComboBox()
    for label, value in ACTION_OPTIONS_FORM:
        main.step_action_combo.addItem(label, value)
    main.step_action_combo.currentIndexChanged.connect(main._handle_action_combo_change)
    form.addRow("Action:", main.step_action_combo)

    main.step_selector_input = QLineEdit()
    main.row_selector = (QLabel("Selector:"), main.step_selector_input)
    form.addRow(*main.row_selector)

    main.step_selector_type_input = QComboBox()
    main.step_selector_type_input.addItems(["css", "text", "xpath", "id", "name", "test_id"])
    main.row_selector_type = (QLabel("Selector type:"), main.step_selector_type_input)
    form.addRow(*main.row_selector_type)

    main.step_selector_index = QSpinBox()
    main.step_selector_index.setRange(0, 50)
    main.row_selector_index = (QLabel("Selector index (nth):"), main.step_selector_index)
    form.addRow(*main.row_selector_index)

    main.step_targets_input = QLineEdit()
    main.row_targets = (QLabel("Targets / pattern:"), main.step_targets_input)
    form.addRow(*main.row_targets)

    main.step_frame_input = QLineEdit()
    main.row_frame = (QLabel("Iframe selector:"), main.step_frame_input)
    form.addRow(*main.row_frame)

    main.step_value_input = QLineEdit()
    main.row_value = (QLabel("Value:"), main.step_value_input)
    form.addRow(*main.row_value)

    main.step_parse_update_account = QCheckBox("Update account (save to profile)")
    main.step_parse_update_account.setChecked(True)
    main.row_parse_update_account = (QLabel(""), main.step_parse_update_account)
    form.addRow(*main.row_parse_update_account)

    main.step_compare_op_input = QComboBox()
    main.step_compare_op_input.addItems(
        [
            "equals",
            "not_equals",
            "contains",
            "not_contains",
            "startswith",
            "endswith",
            "regex",
            "is_empty",
            "not_empty",
            "gt",
            "gte",
            "lt",
            "lte",
        ]
    )
    main.row_compare_op = (QLabel("Compare operator:"), main.step_compare_op_input)
    form.addRow(*main.row_compare_op)

    main.step_compare_right_var_input = QLineEdit()
    main.step_compare_right_var_input.setPlaceholderText("right_var (optional)")
    main.row_compare_right_var = (QLabel("Right variable:"), main.step_compare_right_var_input)
    form.addRow(*main.row_compare_right_var)

    main.step_compare_result_var_input = QLineEdit()
    main.step_compare_result_var_input.setPlaceholderText("result_var (optional)")
    main.row_compare_result_var = (QLabel("Result variable:"), main.step_compare_result_var_input)
    form.addRow(*main.row_compare_result_var)

    main.step_compare_case_sensitive = QCheckBox("Case sensitive")
    main.row_compare_case_sensitive = (QLabel(""), main.step_compare_case_sensitive)
    form.addRow(*main.row_compare_case_sensitive)

    main.step_http_method_combo = QComboBox()
    main.step_http_method_combo.addItems(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
    main.row_http_method = (QLabel("HTTP method:"), main.step_http_method_combo)
    form.addRow(*main.row_http_method)

    main.step_http_headers_input = QTextEdit()
    main.step_http_headers_input.setPlaceholderText("Authorization: Bearer {{token}}\nAccept: application/json")
    main.step_http_headers_input.setFixedHeight(70)
    main.row_http_headers = (QLabel("HTTP headers:"), main.step_http_headers_input)
    form.addRow(*main.row_http_headers)

    main.step_http_params_input = QTextEdit()
    main.step_http_params_input.setPlaceholderText("q={{login}}\npage=1")
    main.step_http_params_input.setFixedHeight(60)
    main.row_http_params = (QLabel("Query params:"), main.step_http_params_input)
    form.addRow(*main.row_http_params)

    main.step_http_body_input = QTextEdit()
    main.step_http_body_input.setPlaceholderText("Request body (text) or JSON")
    main.step_http_body_input.setFixedHeight(90)
    main.row_http_body = (QLabel("Body:"), main.step_http_body_input)
    form.addRow(*main.row_http_body)

    main.step_http_body_is_json = QCheckBox("Parse body as JSON")
    main.row_http_body_is_json = (QLabel(""), main.step_http_body_is_json)
    form.addRow(*main.row_http_body_is_json)

    main.step_http_save_as_input = QLineEdit()
    main.step_http_save_as_input.setPlaceholderText("http (prefix for variables)")
    main.row_http_save_as = (QLabel("Save as:"), main.step_http_save_as_input)
    form.addRow(*main.row_http_save_as)

    main.step_http_response_var_input = QLineEdit()
    main.step_http_response_var_input.setPlaceholderText("last_response (optional)")
    main.row_http_response_var = (QLabel("Response var:"), main.step_http_response_var_input)
    form.addRow(*main.row_http_response_var)

    main.step_http_extract_input = QTextEdit()
    main.step_http_extract_input.setPlaceholderText("token=$.token\nuser_id=$.user.id")
    main.step_http_extract_input.setFixedHeight(70)
    main.row_http_extract = (QLabel("Extract JSON:"), main.step_http_extract_input)
    form.addRow(*main.row_http_extract)

    main.step_http_require_success = QCheckBox("Stop if status is not 2xx")
    main.row_http_require_success = (QLabel(""), main.step_http_require_success)
    form.addRow(*main.row_http_require_success)

    main.step_http_fail_on_status_code = QCheckBox("Fail on non-2xx (Playwright)")
    main.row_http_fail_on_status_code = (QLabel(""), main.step_http_fail_on_status_code)
    form.addRow(*main.row_http_fail_on_status_code)

    main.step_http_ignore_https_errors = QCheckBox("Ignore HTTPS errors")
    main.row_http_ignore_https_errors = (QLabel(""), main.step_http_ignore_https_errors)
    form.addRow(*main.row_http_ignore_https_errors)

    main.step_http_max_redirects = QSpinBox()
    main.step_http_max_redirects.setRange(0, 50)
    main.row_http_max_redirects = (QLabel("Max redirects:"), main.step_http_max_redirects)
    form.addRow(*main.row_http_max_redirects)

    main.step_http_max_retries = QSpinBox()
    main.step_http_max_retries.setRange(0, 20)
    main.row_http_max_retries = (QLabel("Max retries:"), main.step_http_max_retries)
    form.addRow(*main.row_http_max_retries)

    main.step_variable_input = QLineEdit()
    main.row_variable = (QLabel("Variable name:"), main.step_variable_input)
    form.addRow(*main.row_variable)

    main.step_attribute_input = QLineEdit()
    main.row_attribute = (QLabel("Attribute (for extract):"), main.step_attribute_input)
    form.addRow(*main.row_attribute)


    main.step_state_input = QComboBox()
    main.step_state_input.addItems(
        ["", "load", "domcontentloaded", "networkidle", "commit", "visible", "attached", "hidden"]
    )
    main.row_state = (QLabel("State / status:"), main.step_state_input)
    form.addRow(*main.row_state)

    main.step_timeout_input = QSpinBox()
    main.step_timeout_input.setRange(0, 600000)
    main.step_timeout_input.setValue(60000)
    main.row_timeout = (QLabel("Timeout, ms:"), main.step_timeout_input)
    form.addRow(*main.row_timeout)

    main.step_sleep_input = QDoubleSpinBox()
    main.step_sleep_input.setDecimals(3)
    main.step_sleep_input.setRange(0, 300)
    main.row_sleep = (QLabel("Sleep, sec:"), main.step_sleep_input)
    form.addRow(*main.row_sleep)

    main.step_tab_index = QSpinBox()
    main.step_tab_index.setRange(0, 20)
    main.row_tab = (QLabel("Tab index:"), main.step_tab_index)
    form.addRow(*main.row_tab)

    main.step_jump_missing_input = QLineEdit()
    main.row_jump_missing = (QLabel("Jump if missing:"), main.step_jump_missing_input)
    form.addRow(*main.row_jump_missing)
    main.step_jump_found_input = QLineEdit()
    main.row_jump_found = (QLabel("Jump if found:"), main.step_jump_found_input)
    form.addRow(*main.row_jump_found)
    hidden_layout.addLayout(form)

    scenario_layout.addWidget(hidden_container)

    return tab
