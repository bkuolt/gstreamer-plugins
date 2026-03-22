import QtQuick
import QtQuick.Controls

ApplicationWindow {
    visible: true
    width: 400
    height: 200
    title: "Python + QML"

    Column {
        anchors.centerIn: parent
        spacing: 20

        Text {
            id: label
            text: "Klick den Button!"
            font.pixelSize: 24
        }

        Button {
            text: "Drück mich"
            onClicked: bridge.updateText() // Aufruf der Python-Funktion
        }
    }

    // Funktion, die von Python aus aufgerufen werden kann
    function changeText(newText) {
        label.text = newText
    }
}