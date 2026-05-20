import QtQuick
import QtQuick.Layouts
import theme 1.0
import "../components"

Flickable {
    id: root
    property var bridge: typeof dashboardBridge !== "undefined" ? dashboardBridge : null
    contentWidth: width; contentHeight: content.height + 64; clip: true
    Column {
        id: content
        width: parent.width - 56
        x: 28; y: 24; spacing: 28
        PageHeader { width: parent.width; title: "Dashboard"; subtitle: "Monitor and control your browser automation empire" }
        GridLayout {
            width: parent.width; columns: 4; columnSpacing: 22; rowSpacing: 22
            StatCard { Layout.fillWidth: true; label: "Active Profiles"; value: root.bridge ? root.bridge.profiles : 0; change: "+12%"; icon: "user"; accent: Theme.primary }
            StatCard { Layout.fillWidth: true; label: "Running Browsers"; value: root.bridge ? root.bridge.running : 0; change: "+" + (root.bridge ? root.bridge.running : 0); icon: "globe"; accent: Theme.success }
            StatCard { Layout.fillWidth: true; label: "Scenarios"; value: root.bridge ? root.bridge.scenarios : 0; change: "ready"; icon: "play"; accent: Theme.warning }
            StatCard { Layout.fillWidth: true; label: "Proxies"; value: root.bridge ? root.bridge.proxies : 0; change: "pool"; icon: "zap"; accent: Theme.pink }
        }
        RowLayout {
            width: parent.width; spacing: 28
            GlassCard {
                Layout.fillWidth: true; Layout.preferredHeight: 520; padding: 28
                Row { id: liveHeader; anchors.left: parent.left; anchors.top: parent.top; spacing: 14
                    Rectangle { width: 42; height: 42; radius: 14; color: Theme.primary; LineIcon { anchors.centerIn: parent; name: "zap"; color: "white"; size: 22 } }
                    Column { Text { text: "Live Activity"; color: Theme.text; font.pixelSize: 18; font.bold: true } Text { text: "Real-time system events"; color: Theme.muted; font.pixelSize: 13 } }
                }
                ListView {
                    anchors.left: parent.left; anchors.right: parent.right; anchors.top: liveHeader.bottom; anchors.topMargin: 20; anchors.bottom: parent.bottom
                    spacing: 12; model: root.bridge ? root.bridge.activityModel : null; clip: true
                    delegate: Rectangle { width: ListView.view.width; height: 70; radius: 14; color: "#801a1a2e"; border.color: Theme.borderSubtle
                        Row { anchors.fill: parent; anchors.margins: 14; spacing: 14
                            Rectangle { width: 42; height: 42; radius: 13; color: model.type === "warning" ? "#33240d" : model.type === "success" ? "#0b2d38" : "#271f43"; LineIcon { anchors.centerIn: parent; name: model.type === "warning" ? "zap" : "dashboard"; color: model.type === "warning" ? Theme.warning : model.type === "success" ? Theme.success : Theme.primary; size: 20 } }
                            Column { width: parent.width - 100; spacing: 4; Text { text: model.title; color: Theme.text; font.pixelSize: 14; font.bold: true } Text { text: model.desc; color: Theme.muted; font.pixelSize: 12; elide: Text.ElideRight; width: parent.width } }
                            Text { text: model.time; color: Theme.dim; font.pixelSize: 11 }
                        }
                    }
                }
            }
            ColumnLayout {
                Layout.preferredWidth: 375; spacing: 22
                GlassCard { Layout.fillWidth: true; Layout.preferredHeight: 300; padding: 22
                    Row { id: qaHead; spacing: 12; Rectangle { width: 40; height: 40; radius: 14; color: Theme.emerald; LineIcon { anchors.centerIn: parent; name: "zap"; color: "white" } } Text { text: "Quick Actions"; color: Theme.text; font.bold: true; font.pixelSize: 16; anchors.verticalCenter: parent.verticalCenter } }
                    Column { anchors.left: parent.left; anchors.right: parent.right; anchors.top: qaHead.bottom; anchors.topMargin: 18; spacing: 12
                        PrimaryButton { width: parent.width; text: "New Profile"; icon: "plus"; onClicked: profilesBridge.createProfile() }
                        PrimaryButton { width: parent.width; text: "Scenarios"; icon: "play"; onClicked: appState.setPage("Scenarios") }
                        PrimaryButton { width: parent.width; text: "Add Proxy"; icon: "network"; secondary: true; onClicked: appState.setPage("Proxies") }
                        PrimaryButton { width: parent.width; text: "Open Logs"; icon: "logs"; secondary: true; onClicked: appState.setPage("Logs") }
                    }
                }
            }
        }
        GlassCard { width: parent.width; height: 250; padding: 28
            Text { id: rsTitle; text: "Running Sessions"; color: Theme.text; font.pixelSize: 18; font.bold: true }
            ListView { anchors.left: parent.left; anchors.right: parent.right; anchors.top: rsTitle.bottom; anchors.topMargin: 18; anchors.bottom: parent.bottom; orientation: ListView.Horizontal; spacing: 18; model: root.bridge ? root.bridge.runningModel : null
                delegate: GlassCard { width: 320; height: 150; padding: 18
                    Text { text: model.name; color: Theme.text; font.bold: true; font.pixelSize: 15 }
                    Text { y: 26; text: model.browser; color: Theme.muted; font.pixelSize: 12 }
                    Text { y: 70; text: "Proxy"; color: Theme.dim; font.pixelSize: 11 }
                    Text { y: 90; text: model.proxy; color: Theme.text; font.bold: true }
                }
            }
        }
    }
}
