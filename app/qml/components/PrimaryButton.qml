import QtQuick
import theme 1.0

Rectangle {
    id: root
    property string text: "Button"
    property string icon: ""
    property bool danger: false
    property bool secondary: false
    signal clicked()
    height: 36
    radius: 11
    opacity: enabled ? 1 : 0.45
    color: secondary ? "#1a1a2e" : danger ? "#3a1720" : Theme.primary
    border.color: secondary ? Theme.border : danger ? "#7f2430" : Theme.primaryLight
    border.width: 1
    gradient: Gradient {
        GradientStop { position: 0; color: secondary ? "#1a1a2e" : danger ? "#4a1c28" : Theme.primaryLight }
        GradientStop { position: 1; color: secondary ? "#151526" : danger ? "#32151d" : Theme.primary }
    }
    Row {
        anchors.centerIn: parent
        spacing: 8
        LineIcon { visible: root.icon !== ""; name: root.icon; color: root.danger ? "#ff6b6b" : root.secondary ? Theme.muted : "white"; size: 16 }
        Text { text: root.text; color: root.danger ? "#ff8a8a" : root.secondary ? Theme.text : "white"; font.pixelSize: 13; font.weight: Font.DemiBold }
    }
    MouseArea { anchors.fill: parent; enabled: root.enabled; cursorShape: Qt.PointingHandCursor; onClicked: root.clicked() }
}
