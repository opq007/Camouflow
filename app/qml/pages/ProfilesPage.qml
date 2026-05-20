import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import theme 1.0
import "../components"

Flickable {
    id: root
    contentWidth: width
    contentHeight: content.height + 48
    clip: true
    property string editingProfile: ""

    function openProfileModal(profileName) {
        var data = profilesBridge.getProfile(profileName, browserSettingsBridge.engine)
        editingProfile = profileName
        editName.text = data.name || profileName
        editStage.text = data.stage || ""
        editProxyHost.text = data.proxy_host || ""
        editProxyPort.text = data.proxy_port || ""
        editProxyUser.text = data.proxy_user || ""
        editProxyPassword.text = data.proxy_password || ""
        editLocale.text = data.locale || ""
        editTimezone.text = data.timezone || ""
        editUserAgent.text = data.user_agent || ""
        editWebgl.text = data.webgl_vendor || ""
        editCpu.text = data.hardware_concurrency || ""
        profileDialog.open()
    }
    function openTagsModal() {
        settingsBridge.refresh()
        tagName.text = ""
        tagsDialog.open()
    }

    Column {
        id: content
        width: parent.width - 56
        x: 28
        y: 24
        spacing: 22
        RowLayout {
            width: parent.width
            PageHeader { Layout.fillWidth: true; title: "Profiles"; subtitle: "Manage your browser profiles and sessions" }
            PrimaryButton { Layout.preferredWidth: 116; height: 42; text: "Tags"; icon: "settings"; secondary: true; onClicked: root.openTagsModal() }
            PrimaryButton { Layout.preferredWidth: 116; height: 42; text: "New Profile"; icon: "plus"; onClicked: profilesBridge.createProfile() }
        }
        SearchBox { id: search; width: parent.width; placeholder: "Search profiles or tags..." }
        ListView {
            width: parent.width
            height: 38
            orientation: ListView.Horizontal
            spacing: 8
            model: profilesBridge.stagesModel
            clip: true
            delegate: Rectangle {
                width: tagText.width + 34
                height: 34
                radius: 11
                color: model.selected ? Theme.primary : Theme.subtle
                border.color: model.selected ? Theme.primaryLight : Theme.border
                Text {
                    id: tagText
                    anchors.centerIn: parent
                    text: model.name + "  " + model.count
                    color: model.selected ? "white" : Theme.muted
                    font.pixelSize: 12
                    font.bold: true
                }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: profilesBridge.setStageFilter(model.name) }
            }
        }
        ListView {
            width: parent.width
            height: Math.max(520, count * 92)
            model: profilesBridge.model
            spacing: 14
            interactive: false
            delegate: ProfileRow {
                width: ListView.view.width
                name: model.name
                ident: model.id
                browser: model.browser
                proxy: model.proxy
                lastActive: model.lastActive
                status: model.status
                tags: model.tags
                running: model.running
                visible: search.text.length === 0 || (model.name + model.tags + model.proxy).toLowerCase().indexOf(search.text.toLowerCase()) >= 0
                height: visible ? 78 : 0
                onStartClicked: profilesBridge.startProfile(model.name)
                onStopClicked: profilesBridge.stopProfile(model.name)
                onSettingsClicked: root.openProfileModal(model.name)
                onDeleteClicked: profilesBridge.deleteProfile(model.name)
            }
        }
    }

    Dialog {
        id: tagsDialog
        modal: true
        width: Math.min(480, root.width - 80)
        height: 520
        anchors.centerIn: Overlay.overlay
        padding: 0
        background: Rectangle { color: Theme.elevated; radius: 22; border.color: Theme.border }
        contentItem: Column {
            spacing: 14
            padding: 22
            RowLayout {
                width: parent.width - 44
                Text { text: "Profile Tags"; color: Theme.text; font.pixelSize: 22; font.bold: true; Layout.fillWidth: true }
                PrimaryButton { Layout.preferredWidth: 40; text: ""; icon: "plus"; onClicked: tagCreateDialog.open() }
            }
            Text { width: parent.width - 44; text: "Create tags here, then assign them in profile settings."; color: Theme.muted; font.pixelSize: 12; wrapMode: Text.WordWrap }
            ListView {
                width: parent.width - 44
                height: 360
                model: settingsBridge.stagesModel
                spacing: 8
                clip: true
                delegate: Rectangle {
                    width: ListView.view.width
                    height: 42
                    radius: 11
                    color: Theme.subtle
                    border.color: Theme.border
                    Text { anchors.left: parent.left; anchors.leftMargin: 12; anchors.verticalCenter: parent.verticalCenter; text: model.name; color: Theme.text; font.pixelSize: 13; font.bold: true }
                    PrimaryButton { anchors.right: parent.right; anchors.rightMargin: 6; anchors.verticalCenter: parent.verticalCenter; width: 34; height: 28; text: ""; icon: "trash"; danger: true; onClicked: { settingsBridge.deleteStage(model.name); profilesBridge.refresh() } }
                }
            }
        }
    }

    Dialog {
        id: tagCreateDialog
        modal: true
        width: Math.min(420, root.width - 100)
        height: 210
        anchors.centerIn: Overlay.overlay
        padding: 0
        background: Rectangle { color: Theme.elevated; radius: 20; border.color: Theme.border }
        contentItem: Column {
            spacing: 14
            padding: 22
            Text { text: "New Tag"; color: Theme.text; font.pixelSize: 20; font.bold: true }
            FormField { id: tagName; width: parent.width - 44; label: "Tag name" }
            Row {
                spacing: 10
                PrimaryButton { width: 110; text: "Create"; icon: "plus"; onClicked: { settingsBridge.addStage(tagName.text); profilesBridge.refresh(); tagCreateDialog.close() } }
                PrimaryButton { width: 100; text: "Cancel"; secondary: true; onClicked: tagCreateDialog.close() }
            }
        }
    }

    Dialog {
        id: profileDialog
        modal: true
        width: Math.min(820, root.width - 80)
        height: Math.min(720, root.height - 80)
        anchors.centerIn: Overlay.overlay
        padding: 0
        background: Rectangle { color: Theme.elevated; radius: 22; border.color: Theme.border }
        contentItem: Flickable {
            contentWidth: width
            contentHeight: modalContent.height + 44
            clip: true
            Column {
                id: modalContent
                width: parent.width - 44
                x: 22
                y: 22
                spacing: 18
                Text { text: "Profile Settings"; color: Theme.text; font.pixelSize: 24; font.bold: true }
                Text { text: "Profile data + per-profile browser overrides for " + browserSettingsBridge.engine; color: Theme.muted; font.pixelSize: 13 }
                GridLayout {
                    width: parent.width
                    columns: 2
                    columnSpacing: 16
                    rowSpacing: 14
                    FormField { id: editName; Layout.fillWidth: true; label: "Name" }
                    FormField { id: editStage; Layout.fillWidth: true; label: "Tag / Scenario" }
                    FormField { id: editProxyHost; Layout.fillWidth: true; label: "Proxy host" }
                    FormField { id: editProxyPort; Layout.fillWidth: true; label: "Proxy port" }
                    FormField { id: editProxyUser; Layout.fillWidth: true; label: "Proxy user" }
                    FormField { id: editProxyPassword; Layout.fillWidth: true; label: "Proxy password" }
                }
                Rectangle { width: parent.width; height: 1; color: Theme.border }
                Text { text: "Browser Overrides"; color: Theme.text; font.pixelSize: 18; font.bold: true }
                GridLayout {
                    width: parent.width
                    columns: 2
                    columnSpacing: 16
                    rowSpacing: 14
                    FormField { id: editLocale; Layout.fillWidth: true; label: "Locale"; placeholder: "en-US" }
                    FormField { id: editTimezone; Layout.fillWidth: true; label: "Timezone"; placeholder: "America/New_York" }
                    FormField { id: editUserAgent; Layout.fillWidth: true; label: "User Agent" }
                    FormField { id: editWebgl; Layout.fillWidth: true; label: "WebGL / GPU vendor" }
                    FormField { id: editCpu; Layout.fillWidth: true; label: "CPU cores" }
                }
                Row {
                    spacing: 12
                    PrimaryButton {
                        width: 120
                        text: "Save"
                        icon: "save"
                        onClicked: {
                            profilesBridge.saveProfile(root.editingProfile, editName.text, editStage.text, editProxyHost.text, editProxyPort.text, editProxyUser.text, editProxyPassword.text, browserSettingsBridge.engine, editLocale.text, editTimezone.text, editUserAgent.text, editWebgl.text, editCpu.text)
                            profileDialog.close()
                        }
                    }
                    PrimaryButton { width: 110; text: "Cancel"; secondary: true; onClicked: profileDialog.close() }
                }
            }
        }
    }
}
