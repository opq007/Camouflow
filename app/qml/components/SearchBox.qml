import QtQuick
import QtQuick.Controls
import theme 1.0

Rectangle {
    id: root
    property alias text: input.text
    property string placeholder: "Search..."
    height: 52
    radius: 14
    color: "#1a1a2e"
    border.color: Theme.border
    LineIcon { name: "search"; color: Theme.dim; size: 18; anchors.left: parent.left; anchors.leftMargin: 18; anchors.verticalCenter: parent.verticalCenter }
    TextField {
        id: input
        anchors.fill: parent
        anchors.leftMargin: 48
        anchors.rightMargin: 16
        placeholderText: root.placeholder
        color: Theme.text
        placeholderTextColor: Theme.dim
        font.pixelSize: 14
        background: Item {}
        selectionColor: Theme.primary
    }
}
