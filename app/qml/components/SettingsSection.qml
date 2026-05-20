import QtQuick
import theme 1.0
import "."

GlassCard {
    id: root
    property string title: "Section"
    property string subtitle: ""
    property string icon: "settings"
    property color accent: Theme.primary
    height: 250
    padding: 22
    default property alias body: body.data
    Row { id: header; anchors.left: parent.left; anchors.top: parent.top; spacing: 14
        Rectangle { width: 42; height: 42; radius: 14; color: root.accent; LineIcon { anchors.centerIn: parent; name: root.icon; color: "white"; size: 22 } }
        Column { anchors.verticalCenter: parent.verticalCenter; spacing: 2
            Text { text: root.title; color: Theme.text; font.pixelSize: 15; font.bold: true }
            Text { text: root.subtitle; color: Theme.muted; font.pixelSize: 12 }
        }
    }
    Item { id: body; anchors.left: parent.left; anchors.right: parent.right; anchors.top: header.bottom; anchors.topMargin: 24; anchors.bottom: parent.bottom }
}
