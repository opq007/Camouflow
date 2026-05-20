import QtQuick
import theme 1.0

Rectangle {
    id: root
    color: "#b316162a"
    border.color: Theme.border
    border.width: 1
    radius: Theme.radiusLg
    property alias content: content.data
    default property alias contentData: content.data
    property int padding: 24
    clip: true
    layer.enabled: true
    layer.smooth: true
    gradient: Gradient {
        GradientStop { position: 0; color: "#cc18172b" }
        GradientStop { position: 1; color: "#8013131f" }
    }
    Item {
        id: content
        anchors.fill: parent
        anchors.margins: root.padding
    }
}
