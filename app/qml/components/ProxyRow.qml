import QtQuick
import QtQuick.Layouts
import theme 1.0
import "."

GlassCard {
    id: root
    property string pool: ""
    property int proxyIndex: -1
    property string name: "Proxy"
    property string location: "Location"
    property string address: "0.0.0.0:0"
    property string type: "HTTP"
    property string latency: "?"
    property string status: "Active"
    property color accent: Theme.success
    signal settingsClicked(string pool, int index)
    signal checkClicked(string pool, int index)
    height: 80
    padding: 18

    RowLayout {
        anchors.fill: parent
        spacing: Math.max(10, Math.min(24, root.width / 70))

        Rectangle {
            Layout.preferredWidth: 42
            Layout.preferredHeight: 42
            Layout.alignment: Qt.AlignVCenter
            radius: 14
            color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.16)
            LineIcon { anchors.centerIn: parent; name: "globe"; color: root.accent; size: 22 }
        }

        Column {
            Layout.preferredWidth: 220
            Layout.minimumWidth: 90
            Layout.maximumWidth: 340
            Layout.alignment: Qt.AlignVCenter
            spacing: 4
            Text { text: root.name; color: Theme.text; font.pixelSize: 15; font.bold: true; elide: Text.ElideRight; width: parent.width }
            Text { text: root.location; color: Theme.muted; font.pixelSize: 13; elide: Text.ElideRight; width: parent.width }
        }

        InfoColumn { title: "IP Address"; value: root.address; Layout.fillWidth: true; Layout.minimumWidth: 150; Layout.preferredWidth: 260 }
        InfoColumn { title: "Type"; value: root.type; Layout.minimumWidth: 52; Layout.preferredWidth: 70 }
        InfoColumn { title: "Latency"; value: root.latency; Layout.minimumWidth: 40; Layout.preferredWidth: 65 }

        Row {
            Layout.minimumWidth: 24
            Layout.preferredWidth: 96
            Layout.alignment: Qt.AlignVCenter
            spacing: 8
            Rectangle { width: 7; height: 7; radius: 4; color: root.accent; anchors.verticalCenter: parent.verticalCenter }
            Text { text: root.status; color: Theme.muted; font.pixelSize: 13; anchors.verticalCenter: parent.verticalCenter; elide: Text.ElideRight; width: parent.width - 15 }
        }

        Row {
            Layout.preferredWidth: 80
            Layout.minimumWidth: 80
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
            spacing: 8
            PrimaryButton {
                width: 36
                icon: "zap"
                text: ""
                secondary: true
                onClicked: root.checkClicked(root.pool, root.proxyIndex)
            }
            PrimaryButton {
                width: 36
                icon: "settings"
                text: ""
                secondary: true
                onClicked: root.settingsClicked(root.pool, root.proxyIndex)
            }
        }
    }
}
