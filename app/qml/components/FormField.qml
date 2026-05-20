import QtQuick
import QtQuick.Controls
import theme 1.0

Column {
    id: root
    property string label: "Label"
    property alias text: input.text
    property string placeholder: ""
    signal editingFinished()
    spacing: 8
    Text { text: root.label; color: Theme.text; font.pixelSize: 12; font.bold: true }
    Rectangle {
        width: parent.width; height: 40; radius: 11; color: Theme.subtle; border.color: Theme.border
        TextField { id: input; anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 14; color: Theme.text; placeholderText: root.placeholder; placeholderTextColor: Theme.dim; background: Item {} font.pixelSize: 13; onEditingFinished: root.editingFinished() }
    }
}
