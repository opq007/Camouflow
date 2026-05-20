import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import theme 1.0
import "components"
import "pages"

ApplicationWindow {
    id: root
    width: 1460
    height: 900
    minimumWidth: 1180
    minimumHeight: 720
    visible: true
    title: "CamouFlow"
    color: Theme.background

    Rectangle {
        anchors.fill: parent
        color: Theme.background
        RowLayout {
            anchors.fill: parent
            spacing: 0
            Sidebar { Layout.preferredWidth: Theme.sidebarWidth; Layout.fillHeight: true }
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Theme.background
                gradient: Gradient {
                    GradientStop { position: 0; color: "#0b0b14" }
                    GradientStop { position: 1; color: "#10101d" }
                }
                Loader {
                    id: pageLoader
                    anchors.fill: parent
                    sourceComponent: {
                        if (!appState) return dashboardPage
                        if (appState.currentPage === "Profiles") return profilesPage
                        if (appState.currentPage === "Browser") return browserPage
                        if (appState.currentPage === "Proxies") return proxiesPage
                        if (appState.currentPage === "Scenarios") return scenariosPage
                        if (appState.currentPage === "Logs") return logsPage
                        if (appState.currentPage === "Settings") return settingsPage
                        return dashboardPage
                    }
                }
            }
        }
    }

    Component { id: dashboardPage; DashboardPage {} }
    Component { id: profilesPage; ProfilesPage {} }
    Component { id: browserPage; BrowserPage {} }
    Component { id: proxiesPage; ProxiesPage {} }
    Component { id: scenariosPage; ScenariosPage {} }
    Component { id: logsPage; LogsPage {} }
    Component { id: settingsPage; SettingsPage {} }
}
