import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import theme 1.0
import "../components"

Flickable {
    id: root
    contentWidth: width
    contentHeight: Math.max(height + 1, content.implicitHeight + 90)
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    property string tab: "General"
    readonly property bool isCamoufox: browserSettingsBridge.engine === "camoufox"

    component TabButton: Rectangle {
        id: tb
        property string label: "Tab"
        property bool active: false
        signal clicked()
        height: 36; width: 118; radius: 11
        color: active ? Theme.primary : Theme.subtle
        border.color: active ? Theme.primaryLight : Theme.border
        Text { anchors.centerIn: parent; text: tb.label; color: active ? "white" : Theme.muted; font.pixelSize: 13; font.weight: Font.DemiBold }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: tb.clicked() }
    }

    component ToggleRow: Rectangle {
        id: tr
        property string label: "Toggle"
        property string hint: ""
        property bool checked: false
        signal toggled(bool value)
        width: parent ? parent.width : 300; height: 50; radius: 12
        color: Theme.subtle; border.color: Theme.border
        Column { anchors.left: parent.left; anchors.leftMargin: 14; anchors.verticalCenter: parent.verticalCenter; spacing: 2
            Text { text: tr.label; color: Theme.text; font.pixelSize: 13; font.bold: true }
            Text { visible: tr.hint !== ""; text: tr.hint; color: Theme.dim; font.pixelSize: 11 }
        }
        Rectangle { id: sw; width: 42; height: 24; radius: 12; anchors.right: parent.right; anchors.rightMargin: 14; anchors.verticalCenter: parent.verticalCenter; color: tr.checked ? Theme.primary : "#25233a"; border.color: tr.checked ? Theme.primaryLight : Theme.border
            Rectangle { width: 18; height: 18; radius: 9; y: 3; x: tr.checked ? 21 : 3; color: "white"; Behavior on x { NumberAnimation { duration: 120 } } }
        }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: tr.toggled(!tr.checked) }
    }

    component ModeButton: Rectangle {
        id: mb
        property string label: "Mode"
        property bool active: false
        signal clicked()
        height: 36; radius: 11
        color: active ? Theme.primary : Theme.subtle
        border.color: active ? Theme.primaryLight : Theme.border
        Text { anchors.centerIn: parent; text: mb.label; color: active ? "white" : Theme.text; font.pixelSize: 12; font.weight: Font.DemiBold }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: mb.clicked() }
    }

    component MultiField: Column {
        id: mf
        property string label: "Label"
        property alias text: input.text
        property string placeholder: ""
        property int fieldHeight: 92
        signal editingFinished()
        spacing: 8
        Text { text: mf.label; color: Theme.text; font.pixelSize: 12; font.bold: true }
        Rectangle { width: parent.width; height: mf.fieldHeight; radius: 11; color: Theme.subtle; border.color: Theme.border
            ScrollView { anchors.fill: parent; anchors.margins: 10; clip: true
                TextArea {
                    id: input
                    color: Theme.text
                    placeholderText: mf.placeholder
                    placeholderTextColor: Theme.dim
                    background: Item {}
                    wrapMode: TextArea.Wrap
                    font.pixelSize: 13
                    onActiveFocusChanged: if (!activeFocus) mf.editingFinished()
                }
            }
        }
    }

    Column {
        id: content
        width: parent.width - 56
        x: 28; y: 24; spacing: 22

        RowLayout { width: parent.width
            PageHeader { Layout.fillWidth: true; title: "Browser Engine"; subtitle: "New design, old full browser defaults" }
            PrimaryButton { width: 110; text: "Save"; icon: "save"; onClicked: browserSettingsBridge.save() }
            PrimaryButton { width: 110; text: "Reset"; secondary: true; onClicked: browserSettingsBridge.reset() }
        }

        RowLayout { width: parent.width; spacing: 22
            GlassCard { Layout.fillWidth: true; Layout.preferredHeight: 190; border.color: browserSettingsBridge.engine === "camoufox" ? Theme.primary : Theme.border; padding: 20
                Rectangle { width: 44; height: 44; radius: 14; color: Theme.primary; LineIcon { anchors.centerIn: parent; name: "globe"; color: "white"; size: 23 } }
                Text { y: 58; text: "Camoufox"; color: Theme.text; font.pixelSize: 21; font.bold: true }
                Text { y: 88; width: parent.width - 40; text: "Firefox-based anti-detect engine. Strong fingerprint masking, Camoufox config support, virtual/headless modes."; color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap }
                Row { y: 134; spacing: 8
                    Rectangle { width: 150; height: 30; radius: 9; color: Theme.subtle; border.color: Theme.border; Text { anchors.centerIn: parent; text: "Deep fingerprint"; color: Theme.muted; font.pixelSize: 11; font.bold: true } }
                    Rectangle { width: 132; height: 30; radius: 9; color: Theme.subtle; border.color: Theme.border; Text { anchors.centerIn: parent; text: "Virtual display"; color: Theme.muted; font.pixelSize: 11; font.bold: true } }
                }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: browserSettingsBridge.setEngine("camoufox") }
            }
            GlassCard { Layout.fillWidth: true; Layout.preferredHeight: 190; border.color: browserSettingsBridge.engine === "cloakbrowser" ? Theme.primary : Theme.border; padding: 20
                Rectangle { width: 44; height: 44; radius: 14; color: "#25233a"; LineIcon { anchors.centerIn: parent; name: "globe"; color: Theme.dim; size: 23 } }
                Text { y: 58; text: "CloakBrowser"; color: Theme.text; font.pixelSize: 21; font.bold: true }
                Text { y: 88; width: parent.width - 40; text: "Chromium-based engine. Better native window control, proxy geo detection, launch args and extension workflow."; color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap }
                Row { y: 134; spacing: 8
                    Rectangle { width: 125; height: 30; radius: 9; color: Theme.subtle; border.color: Theme.border; Text { anchors.centerIn: parent; text: "Chromium"; color: Theme.muted; font.pixelSize: 11; font.bold: true } }
                    Rectangle { width: 140; height: 30; radius: 9; color: Theme.subtle; border.color: Theme.border; Text { anchors.centerIn: parent; text: "Launch args"; color: Theme.muted; font.pixelSize: 11; font.bold: true } }
                }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: browserSettingsBridge.setEngine("cloakbrowser") }
            }
        }

        GlassCard { width: parent.width; height: 64; padding: 14
            Row { anchors.verticalCenter: parent.verticalCenter; spacing: 10
                TabButton { label: "General"; active: root.tab === label; onClicked: root.tab = label }
                TabButton { label: "Window"; active: root.tab === label; onClicked: root.tab = label }
                TabButton { label: "Navigator"; active: root.tab === label; onClicked: root.tab = label }
                TabButton { label: "Plugins"; active: root.tab === label; onClicked: root.tab = label }
            }
        }

        GridLayout {
            width: parent.width; columns: 2; columnSpacing: 22; rowSpacing: 22
            visible: root.tab === "General"
            SettingsSection { Layout.fillWidth: true; Layout.preferredHeight: 340; title: "Execution"; subtitle: root.isCamoufox ? "Camoufox window/headless/humanize" : "CloakBrowser headless/humanize"; icon: "play"; accent: Theme.primary
                Column { anchors.fill: parent; spacing: 14
                    Text { text: "Execution mode"; color: Theme.text; font.pixelSize: 12; font.bold: true }
                    Row { width: parent.width; spacing: 10
                        ModeButton { width: (parent.width - 20) / 3; label: "Standard"; active: browserSettingsBridge.headlessMode === "standard"; onClicked: browserSettingsBridge.setHeadlessMode("standard") }
                        ModeButton { width: (parent.width - 20) / 3; label: "Headless"; active: browserSettingsBridge.headlessMode === "headless"; onClicked: browserSettingsBridge.setHeadlessMode("headless") }
                        ModeButton { width: (parent.width - 20) / 3; label: "Virtual"; active: browserSettingsBridge.headlessMode === "virtual"; enabled: root.isCamoufox; opacity: enabled ? 1 : 0.35; onClicked: if (enabled) browserSettingsBridge.setHeadlessMode("virtual") }
                    }
                    ToggleRow { label: "Human-like cursor"; hint: "Enable natural mouse movement"; checked: browserSettingsBridge.humanize; onToggled: browserSettingsBridge.setHumanizeEnabled(value) }
                    Row { width: parent.width; spacing: 16
                        FormField { width: (parent.width - 16) / 2; label: "Cursor duration"; placeholder: "Auto"; text: browserSettingsBridge.humanizeDuration; onEditingFinished: browserSettingsBridge.setValue("humanize", text) }
                        FormField { width: (parent.width - 16) / 2; label: "Human preset"; text: browserSettingsBridge.humanPreset; onEditingFinished: browserSettingsBridge.setValue("human_preset", text) }
                    }
                }
            }
            SettingsSection { visible: root.isCamoufox; Layout.fillWidth: true; Layout.preferredHeight: 320; title: "Operating Systems"; subtitle: "Camoufox OS fingerprint pool"; icon: "globe"; accent: Theme.success
                Column { anchors.fill: parent; spacing: 12
                    ToggleRow { label: "Auto"; hint: "Use automatic OS selection"; checked: browserSettingsBridge.osAuto; onToggled: if (value) browserSettingsBridge.setOsEnabled("auto", true) }
                    ToggleRow { label: "Windows"; checked: browserSettingsBridge.osWindows; onToggled: browserSettingsBridge.setOsEnabled("windows", value) }
                    ToggleRow { label: "macOS"; checked: browserSettingsBridge.osMacos; onToggled: browserSettingsBridge.setOsEnabled("macos", value) }
                    ToggleRow { label: "Linux"; checked: browserSettingsBridge.osLinux; onToggled: browserSettingsBridge.setOsEnabled("linux", value) }
                }
            }
            SettingsSection { visible: !root.isCamoufox; Layout.fillWidth: true; Layout.preferredHeight: 320; title: "Cloak Fingerprint"; subtitle: "Chromium fingerprint arguments"; icon: "globe"; accent: Theme.success
                Column { anchors.fill: parent; spacing: 14
                    Text { text: "Platform"; color: Theme.text; font.pixelSize: 12; font.bold: true }
                    Row { width: parent.width; spacing: 10
                        ModeButton { width: (parent.width - 20) / 3; label: "Windows"; active: browserSettingsBridge.platform === "windows"; onClicked: browserSettingsBridge.setValue("platform", "windows") }
                        ModeButton { width: (parent.width - 20) / 3; label: "macOS"; active: browserSettingsBridge.platform === "macos"; onClicked: browserSettingsBridge.setValue("platform", "macos") }
                        ModeButton { width: (parent.width - 20) / 3; label: "Linux"; active: browserSettingsBridge.platform === "linux"; onClicked: browserSettingsBridge.setValue("platform", "linux") }
                    }
                    FormField { width: parent.width; label: "Fingerprint seed"; placeholder: "Auto per profile"; text: browserSettingsBridge.fingerprintSeed; onEditingFinished: browserSettingsBridge.setValue("fingerprint_seed", parseInt(text || "0")) }
                    Row { width: parent.width; spacing: 10
                        ModeButton { width: (parent.width - 10) / 2; label: "Default human"; active: browserSettingsBridge.humanPreset === "default"; onClicked: browserSettingsBridge.setValue("human_preset", "default") }
                        ModeButton { width: (parent.width - 10) / 2; label: "Careful human"; active: browserSettingsBridge.humanPreset === "careful"; onClicked: browserSettingsBridge.setValue("human_preset", "careful") }
                    }
                }
            }
            SettingsSection { Layout.fillWidth: true; Layout.preferredHeight: 310; title: "Locale & Timezone"; subtitle: root.isCamoufox ? "Camoufox locale/config overrides" : "CloakBrowser locale/timezone launch options"; icon: "globe"; accent: Theme.warning
                Column { anchors.fill: parent; spacing: 16
                    FormField { width: parent.width; label: "Locale override"; placeholder: "Auto / en-US"; text: browserSettingsBridge.locale; onEditingFinished: browserSettingsBridge.setValue("locale", text) }
                    FormField { width: parent.width; label: "Timezone override"; placeholder: "Auto / America/New_York"; text: browserSettingsBridge.timezone; onEditingFinished: browserSettingsBridge.setValue("timezone", text) }
                    Row { width: parent.width; spacing: 10
                        ModeButton { width: (parent.width - 20) / 3; label: "Auto"; active: browserSettingsBridge.locale === "" && browserSettingsBridge.timezone === ""; onClicked: { browserSettingsBridge.setValue("locale", ""); browserSettingsBridge.setValue("timezone", "") } }
                        ModeButton { width: (parent.width - 20) / 3; label: "en-US / NY"; active: browserSettingsBridge.locale === "en-US"; onClicked: { browserSettingsBridge.setValue("locale", "en-US"); browserSettingsBridge.setValue("timezone", "America/New_York") } }
                        ModeButton { width: (parent.width - 20) / 3; label: "ru-RU / Moscow"; active: browserSettingsBridge.locale === "ru-RU"; onClicked: { browserSettingsBridge.setValue("locale", "ru-RU"); browserSettingsBridge.setValue("timezone", "Europe/Moscow") } }
                    }
                }
            }
            SettingsSection { Layout.fillWidth: true; Layout.preferredHeight: root.isCamoufox ? 270 : 390; title: root.isCamoufox ? "Camoufox Storage" : "Cloak Runtime"; subtitle: root.isCamoufox ? "Profile persistence" : "Persistent context / stealth / backend"; icon: "save"; accent: Theme.primary
                Column { anchors.fill: parent; spacing: 12
                    ToggleRow { label: "Persistent context"; hint: "Keep browser session data"; checked: browserSettingsBridge.persistentContext; onToggled: browserSettingsBridge.setBool("persistent_context", value) }
                    ToggleRow { visible: root.isCamoufox; label: "Enable cache"; hint: "Camoufox disk/network cache"; checked: browserSettingsBridge.enableCache; onToggled: browserSettingsBridge.setBool("enable_cache", value) }
                    ToggleRow { visible: !root.isCamoufox; label: "GeoIP locale/timezone"; hint: "CloakBrowser proxy-based detection"; checked: browserSettingsBridge.geoip; onToggled: browserSettingsBridge.setBool("geoip", value) }
                    ToggleRow { visible: !root.isCamoufox; label: "Stealth args"; hint: "Use cloakbrowser default stealth args"; checked: browserSettingsBridge.stealthArgs; onToggled: browserSettingsBridge.setBool("stealth_args", value) }
                    FormField { visible: !root.isCamoufox; width: parent.width; label: "Backend"; placeholder: "Auto"; text: browserSettingsBridge.backend; onEditingFinished: browserSettingsBridge.setValue("backend", text) }
                }
            }
        }

        GridLayout {
            width: parent.width; columns: 2; columnSpacing: 22; rowSpacing: 22
            visible: root.tab === "Window"
            SettingsSection { Layout.fillWidth: true; Layout.preferredHeight: 310; title: "Window Size"; subtitle: "Browser viewport defaults"; icon: "dashboard"; accent: Theme.primary
                Column { anchors.fill: parent; spacing: 16
                    Row { width: parent.width; spacing: 16
                        FormField { width: (parent.width - 16) / 2; label: "Window width"; text: browserSettingsBridge.windowWidth; onEditingFinished: browserSettingsBridge.setValue("window_width", parseInt(text)) }
                        FormField { width: (parent.width - 16) / 2; label: "Window height"; text: browserSettingsBridge.windowHeight; onEditingFinished: browserSettingsBridge.setValue("window_height", parseInt(text)) }
                    }
                    Row { width: parent.width; spacing: 16
                        FormField { width: (parent.width - 16) / 2; label: "Screen width"; text: browserSettingsBridge.screenWidth; onEditingFinished: browserSettingsBridge.setValue("screen_width", parseInt(text)) }
                        FormField { width: (parent.width - 16) / 2; label: "Screen height"; text: browserSettingsBridge.screenHeight; onEditingFinished: browserSettingsBridge.setValue("screen_height", parseInt(text)) }
                    }
                    PrimaryButton { width: 110; text: "Auto size"; secondary: true; onClicked: { browserSettingsBridge.setValue("window_width", 0); browserSettingsBridge.setValue("window_height", 0); browserSettingsBridge.setValue("screen_width", 0); browserSettingsBridge.setValue("screen_height", 0) } }
                }
            }
            SettingsSection { visible: root.isCamoufox; Layout.fillWidth: true; Layout.preferredHeight: 310; title: "Camoufox Runtime Protection"; subtitle: "Network/rendering restrictions"; icon: "zap"; accent: Theme.warning
                Column { anchors.fill: parent; spacing: 12
                    ToggleRow { label: "Block WebRTC"; checked: browserSettingsBridge.blockWebrtc; onToggled: browserSettingsBridge.setBool("block_webrtc", value) }
                    ToggleRow { label: "Block images"; checked: browserSettingsBridge.blockImages; onToggled: browserSettingsBridge.setBool("block_images", value) }
                    ToggleRow { label: "Disable COOP"; checked: browserSettingsBridge.disableCoop; onToggled: browserSettingsBridge.setBool("disable_coop", value) }
                }
            }
            SettingsSection { visible: root.isCamoufox; Layout.fillWidth: true; Layout.preferredHeight: 280; title: "Camoufox Window Overrides"; subtitle: "window_overrides JSON passed to config"; icon: "settings"; accent: Theme.success
                Column { anchors.fill: parent; spacing: 12
                    MultiField { width: parent.width; fieldHeight: 170; label: "window_overrides JSON"; placeholder: "{\n  \"screen\": {\"availWidth\": 1920}\n}"; text: browserSettingsBridge.windowOverridesText; onEditingFinished: browserSettingsBridge.setValue("window_overrides", text) }
                }
            }
        }

        GridLayout {
            width: parent.width; columns: 2; columnSpacing: 22; rowSpacing: 22
            visible: root.tab === "Navigator"
            SettingsSection { Layout.fillWidth: true; Layout.preferredHeight: root.isCamoufox ? 540 : 500; title: root.isCamoufox ? "Camoufox Navigator" : "CloakBrowser Navigator"; subtitle: root.isCamoufox ? "navigator_overrides + Accept-Language" : "Chromium context options"; icon: "user"; accent: Theme.primary
                ColumnLayout { anchors.fill: parent; spacing: 16
                    RowLayout { Layout.fillWidth: true; spacing: 12
                        FormField { Layout.fillWidth: true; Layout.preferredHeight: 62; label: "User Agent"; placeholder: "Auto"; text: browserSettingsBridge.userAgent; onEditingFinished: browserSettingsBridge.setValue("user_agent", text) }
                        PrimaryButton { text: "Auto UA"; secondary: true; Layout.preferredWidth: 110; Layout.alignment: Qt.AlignBottom; onClicked: browserSettingsBridge.setValue("user_agent", "") }
                    }
                    RowLayout { Layout.fillWidth: true; spacing: 16
                        FormField { Layout.fillWidth: true; Layout.preferredHeight: 62; label: "CPU cores"; text: browserSettingsBridge.cpuCores; onEditingFinished: browserSettingsBridge.setValue("hardware_concurrency", parseInt(text)) }
                        PrimaryButton { text: "Auto CPU"; secondary: true; Layout.preferredWidth: 110; Layout.alignment: Qt.AlignBottom; onClicked: browserSettingsBridge.setValue("hardware_concurrency", 0) }
                    }
                    Text { visible: !root.isCamoufox; text: "Platform"; color: Theme.text; font.pixelSize: 12; font.bold: true }
                    RowLayout { visible: !root.isCamoufox; Layout.fillWidth: true; spacing: 10
                        ModeButton { Layout.fillWidth: true; label: "Windows"; active: browserSettingsBridge.platform === "windows"; onClicked: browserSettingsBridge.setValue("platform", "windows") }
                        ModeButton { Layout.fillWidth: true; label: "macOS"; active: browserSettingsBridge.platform === "macos"; onClicked: browserSettingsBridge.setValue("platform", "macos") }
                        ModeButton { Layout.fillWidth: true; label: "Linux"; active: browserSettingsBridge.platform === "linux"; onClicked: browserSettingsBridge.setValue("platform", "linux") }
                    }
                    MultiField { visible: root.isCamoufox; width: parent.width; fieldHeight: 170; label: "navigator_overrides JSON"; placeholder: "{\n  \"platform\": \"Win32\",\n  \"languages\": [\"en-US\", \"en\"]\n}"; text: browserSettingsBridge.navigatorOverridesText; onEditingFinished: browserSettingsBridge.setValue("navigator_overrides", text) }
                }
            }
            SettingsSection { Layout.fillWidth: true; Layout.preferredHeight: root.isCamoufox ? 350 : 500; title: root.isCamoufox ? "Camoufox WebGL" : "CloakBrowser GPU"; subtitle: root.isCamoufox ? "Validated webgl_config pair" : "Fingerprint GPU launch args"; icon: "settings"; accent: Theme.success
                ColumnLayout { anchors.fill: parent; spacing: 16
                    FormField { Layout.fillWidth: true; label: "WebGL / GPU vendor"; placeholder: "Auto"; text: browserSettingsBridge.webglVendor; onEditingFinished: browserSettingsBridge.setValue("webgl_vendor", text) }
                    FormField { Layout.fillWidth: true; label: "WebGL / GPU renderer"; placeholder: "Auto"; text: browserSettingsBridge.webglRenderer; onEditingFinished: browserSettingsBridge.setValue("webgl_renderer", text) }
                    RowLayout { Layout.fillWidth: true; spacing: 10
                        ModeButton { Layout.fillWidth: true; label: "Auto GPU"; active: browserSettingsBridge.webglVendor === "" && browserSettingsBridge.webglRenderer === ""; onClicked: { browserSettingsBridge.setValue("webgl_vendor", ""); browserSettingsBridge.setValue("webgl_renderer", "") } }
                        ModeButton { Layout.fillWidth: true; label: "NVIDIA"; active: browserSettingsBridge.webglVendor.indexOf("NVIDIA") >= 0; onClicked: { browserSettingsBridge.setValue("webgl_vendor", "NVIDIA Corporation"); browserSettingsBridge.setValue("webgl_renderer", "NVIDIA GeForce RTX") } }
                        ModeButton { Layout.fillWidth: true; label: "Intel"; active: browserSettingsBridge.webglVendor.indexOf("Intel") >= 0; onClicked: { browserSettingsBridge.setValue("webgl_vendor", "Intel Inc."); browserSettingsBridge.setValue("webgl_renderer", "Intel Iris OpenGL Engine") } }
                    }
                    RowLayout { visible: !root.isCamoufox; Layout.fillWidth: true; spacing: 10
                        ModeButton { Layout.fillWidth: true; label: "Auto"; active: browserSettingsBridge.colorScheme === ""; onClicked: browserSettingsBridge.setValue("color_scheme", "") }
                        ModeButton { Layout.fillWidth: true; label: "Light"; active: browserSettingsBridge.colorScheme === "light"; onClicked: browserSettingsBridge.setValue("color_scheme", "light") }
                        ModeButton { Layout.fillWidth: true; label: "Dark"; active: browserSettingsBridge.colorScheme === "dark"; onClicked: browserSettingsBridge.setValue("color_scheme", "dark") }
                    }
                    ToggleRow { visible: root.isCamoufox; width: parent.width; label: "Block WebGL"; checked: browserSettingsBridge.blockWebgl; onToggled: browserSettingsBridge.setBool("block_webgl", value) }
                }
            }
        }

        GridLayout {
            width: parent.width; columns: 2; columnSpacing: 22; rowSpacing: 22
            visible: root.tab === "Plugins"
            SettingsSection { visible: root.isCamoufox; Layout.fillWidth: true; Layout.preferredHeight: 520; title: "Camoufox Addons"; subtitle: "fonts/addons/exclude_addons"; icon: "plus"; accent: Theme.primary
                Column { anchors.fill: parent; spacing: 16
                    MultiField { width: parent.width; label: "Fonts"; placeholder: "One font per line"; text: browserSettingsBridge.fontsText; onEditingFinished: browserSettingsBridge.setValue("fonts", text) }
                    MultiField { width: parent.width; label: "Addons"; placeholder: "Path or addon id per line"; text: browserSettingsBridge.addonsText; onEditingFinished: browserSettingsBridge.setValue("addons", text) }
                    MultiField { width: parent.width; label: "Exclude addons"; placeholder: "Addon ids to exclude"; text: browserSettingsBridge.excludeAddonsText; onEditingFinished: browserSettingsBridge.setValue("exclude_addons", text) }
                }
            }
            SettingsSection { visible: !root.isCamoufox; Layout.fillWidth: true; Layout.preferredHeight: 390; title: "CloakBrowser Launch"; subtitle: "extension_paths and launch_args"; icon: "settings"; accent: Theme.success
                Column { anchors.fill: parent; spacing: 16
                    MultiField { width: parent.width; label: "Extension paths"; placeholder: "One extension path per line"; text: browserSettingsBridge.extensionPathsText; onEditingFinished: browserSettingsBridge.setValue("extension_paths", text) }
                    MultiField { width: parent.width; label: "Launch arguments"; placeholder: "--flag=value"; text: browserSettingsBridge.launchArgsText; onEditingFinished: browserSettingsBridge.setValue("launch_args", text) }
                }
            }
        }
    }
}
