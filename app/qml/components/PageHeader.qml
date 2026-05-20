import QtQuick
import theme 1.0

Item {
    id: root
    property string title: "Page"
    property string subtitle: ""
    property string badge: ""
    height: 76
    Column {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        spacing: 4
        Text { text: root.title; color: Theme.text; font.pixelSize: 34; font.bold: true; font.letterSpacing: -1.0 }
        Text { text: root.subtitle; color: Theme.muted; font.pixelSize: 14 }
    }
    Rectangle {
        visible: root.badge.length > 0
        anchors.right: parent.right
        anchors.top: parent.top
        width: badgeText.width + 36
        height: 42
        radius: 18
        color: "#2210303a"
        border.color: "#3342d6ee"
        Row { anchors.centerIn: parent; spacing: 10; Rectangle { width: 10; height: 10; radius: 5; color: Theme.success } Text { id: badgeText; text: root.badge; color: Theme.success; font.pixelSize: 13; font.bold: true } }
    }
}
