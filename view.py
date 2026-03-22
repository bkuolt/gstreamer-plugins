import sys
from PySide6.QtGui import QGuiApplication, QKeyEvent, QMouseEvent
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot, QEvent, Qt

class Bridge(QObject):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        

    # Das ist der "Magische Filter", der alle Events im Fenster sieht
    def eventFilter(self, watched, event):
        # 1. TASTATUR Handling
        if event.type() == QEvent.KeyPress:
            key_event = QKeyEvent(event)
            print(f"Taste gedrückt: {key_event.text()} (Code: {key_event.key()})")
            
            if key_event.key() == Qt.Key_Escape:
                print("Programm beendet per ESC")
                QGuiApplication.quit()
            
            # Update zurück an QML senden
            self.update_qml_status(f"Taste: {key_event.text()}")
            return True # Event konsumiert

        # 2. MAUS Handling
        elif event.type() == QEvent.MouseButtonPress:
            mouse_event = QMouseEvent(event)
            pos = mouse_event.position()
            print(f"Mausklick bei: x={pos.x()}, y={pos.y()}")
            self.update_qml_status(f"Klick bei {int(pos.x())}/{int(pos.y())}")
            return True

        return super().eventFilter(watched, event)

    def update_qml_status(self, msg):
        root = self.engine.rootObjects()
        if root:
            # Ruft die QML-Funktion 'changeText' auf
            root[0].changeText(msg)

app = QGuiApplication(sys.argv)
engine = QQmlApplicationEngine()

bridge = Bridge(engine)
# Wir installieren den Filter auf der App, damit er ÜBERALL im Fenster lauscht
app.installEventFilter(bridge)

engine.rootContext().setContextProperty("bridge", bridge)
engine.load("view.qml")

if not engine.rootObjects():
    sys.exit(-1)

sys.exit(app.exec())