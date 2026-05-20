import QtQuick
import theme 1.0

GlassCard {
    id: root
    property string label: "Metric"
    property string value: "0"
    property string change: ""
    property string icon: "dashboard"
    property color accent: Theme.primary
    property bool compact: height < 120
    implicitHeight: 184
    height: implicitHeight
    padding: compact ? 18 : 24

    Rectangle {
        id: iconBadge
        width: root.compact ? 38 : 50
        height: width
        radius: root.compact ? 13 : 16
        color: root.accent
        anchors.left: parent.left
        anchors.top: parent.top
        LineIcon { anchors.centerIn: parent; name: root.icon; color: "white"; size: root.compact ? 20 : 28; lineWidth: 2.3 }
    }

    Text {
        visible: !root.compact
        anchors.right: parent.right
        anchors.top: parent.top
        text: root.change
        color: Theme.success
        font.pixelSize: 13
        font.bold: true
    }

    Column {
        visible: root.compact
        anchors.left: parent.left
        anchors.leftMargin: 56
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: 5
        Text { text: root.label; color: Theme.muted; font.pixelSize: 12; elide: Text.ElideRight; width: parent.width }
        Text { text: root.value; color: Theme.text; font.pixelSize: 24; font.bold: true; width: parent.width }
    }

    Column {
        visible: !root.compact
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: iconBadge.bottom
        anchors.topMargin: 16
        spacing: 8
        Text { text: root.label; color: Theme.muted; font.pixelSize: 13; width: parent.width; elide: Text.ElideRight }
        Text { text: root.value; color: Theme.text; font.pixelSize: 32; font.bold: true; width: parent.width }
    }
}
