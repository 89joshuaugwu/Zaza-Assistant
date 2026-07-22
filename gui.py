import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen

# Global signal bus so any part of the app can change the UI state
class Signals(QObject):
    state_changed = pyqtSignal(str) # "sleeping", "listening", "thinking", "speaking"
    text_updated = pyqtSignal(str)  # Subtitles/text

signals = Signals()

class AssistantThread(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        # We import here to avoid circular imports during startup
        from main import run_voice_mode
        try:
            run_voice_mode()
        except Exception as e:
            print(f"Assistant thread crashed: {e}")


class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.radius = 30
        self.state = "sleeping" # sleeping, listening, thinking, speaking
        
        # Pulse animation for the orb
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)
        self.phase = 0.0

    def set_state(self, state):
        self.state = state
        self.update()

    def animate(self):
        import math
        self.phase += 0.2
        if self.state == "listening":
            self.radius = 30 + 10 * math.sin(self.phase)
        elif self.state == "thinking":
            self.radius = 30 + 5 * math.sin(self.phase * 2)
        elif self.state == "speaking":
            # Erratic, fast pulse representing voice waveform
            self.radius = 30 + 15 * math.fabs(math.sin(self.phase * 3))
        else:
            self.radius = 30 # sleeping
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Color logic based on state
        if self.state == "sleeping":
            color = QColor(100, 100, 100, 100)
        elif self.state == "listening":
            color = QColor(0, 255, 255, 200) # Cyan
        elif self.state == "thinking":
            color = QColor(148, 0, 211, 200) # Purple
        elif self.state == "speaking":
            color = QColor(255, 0, 128, 200) # Pink
            
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.width() // 2 - int(self.radius), 
                            self.height() // 2 - int(self.radius), 
                            int(self.radius * 2), int(self.radius * 2))


class FloatingWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Frameless and Always on Top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(300, 150)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Orb
        self.orb = OrbWidget()
        layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Text Label
        self.label = QLabel("Sleeping...")
        self.label.setFont(QFont("Inter", 12))
        self.label.setStyleSheet("color: white; background: rgba(0,0,0,150); border-radius: 10px; padding: 5px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
        
        # Connect Signals
        signals.state_changed.connect(self.on_state_changed)
        signals.text_updated.connect(self.on_text_updated)

    def on_state_changed(self, state):
        self.orb.set_state(state)
        
    def on_text_updated(self, text):
        self.label.setText(text)

    # Allow window dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_pos'):
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'drag_pos'):
            del self.drag_pos


def launch_gui():
    app = QApplication(sys.argv)
    
    # Show the floating widget
    widget = FloatingWidget()
    widget.show()
    
    # Place it at the bottom center of the screen
    screen = app.primaryScreen().geometry()
    widget.move(screen.width() // 2 - widget.width() // 2, screen.height() - widget.height() - 100)
    
    # Start the assistant logic in the background
    assistant_thread = AssistantThread()
    assistant_thread.start()
    
    sys.exit(app.exec())
