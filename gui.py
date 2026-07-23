import sys
import os
import math
import dotenv
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QPushButton, QDialog, QHBoxLayout, QComboBox, 
                             QLineEdit, QFormLayout, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush

class Signals(QObject):
    state_changed = pyqtSignal(str)
    text_updated = pyqtSignal(str)

signals = Signals()

from PyQt6.QtWidgets import QStackedWidget, QListWidget, QFrame

class DraggableHeader(QWidget):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            
    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_pos'):
            delta = event.globalPosition().toPoint() - self.drag_pos
            window = self.window()
            window.move(window.x() + delta.x(), window.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        if hasattr(self, 'drag_pos'):
            del self.drag_pos

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zaza Dashboard")
        self.setFixedSize(700, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setStyleSheet("""
            QDialog { background: transparent; }
            #MainFrame {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #1a3379, stop: 0.5 #0f172a, stop: 1 black);
                border-radius: 15px; border: 1px solid #38bdf8;
            }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 13px; font-weight: 500; }
            QListWidget {
                background: transparent; border: none; outline: none;
            }
            QListWidget::item {
                color: #94a3b8; padding: 15px 20px; font-size: 14px; font-weight: bold; border-radius: 8px; margin-bottom: 5px;
            }
            QListWidget::item:selected {
                background-color: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.5);
            }
            QListWidget::item:hover:!selected {
                background-color: rgba(255, 255, 255, 0.05); color: white;
            }
            QComboBox, QLineEdit { 
                background-color: rgba(0, 0, 0, 0.4); color: white; 
                border: 1px solid #334155; border-radius: 6px; padding: 8px; font-size: 13px;
            }
            QComboBox:focus, QLineEdit:focus { border: 1px solid #38bdf8; background-color: rgba(15, 23, 42, 0.8); }
            QPushButton#SaveBtn { 
                background-color: #0284c7; color: white; border-radius: 8px; padding: 12px; font-size: 14px; font-weight: bold; 
            }
            QPushButton#SaveBtn:hover { background-color: #38bdf8; }
            QPushButton#CloseBtn {
                background-color: transparent; color: #94a3b8; font-size: 16px; font-weight: bold; border: none;
            }
            QPushButton#CloseBtn:hover { color: #ef4444; }
        """)

        # Main wrapper
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setGeometry(0, 0, 700, 500)
        
        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom Header
        header = DraggableHeader(self.main_frame)
        header.setFixedHeight(40)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 15, 0)
        
        title = QLabel("Zaza Assistant Dashboard")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseBtn")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        main_layout.addWidget(header)
        
        # Content Area (Sidebar + Pages)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 10, 20, 20)
        content_layout.setSpacing(20)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(180)
        self.sidebar.addItems(["Identity", "Voice Engine", "Advanced Tools", "Memory"])
        self.sidebar.setCurrentRow(0)
        
        # Stacked Pages
        self.pages = QStackedWidget()
        
        from config import (WAKE_MODE, WAKE_MODEL, WAKE_WORD, WHISPER_MODEL_SIZE, 
                            OLLAMA_MODEL, ASSISTANT_NAME, SECURITY_PIN, OLLAMA_URL,
                            WAKE_THRESHOLD, SAMPLE_RATE, WHISPER_COMPUTE_TYPE,
                            MAX_COMMAND_SECONDS, SILENCE_THRESHOLD, SILENCE_DURATION, 
                            CONVERSATION_TIMEOUT, HF_TOKEN)

        # PAGE 1: Identity
        page1 = QWidget()
        layout1 = QFormLayout(page1)
        layout1.setSpacing(15)
        self.assistant_name = QLineEdit(ASSISTANT_NAME)
        self.security_pin = QLineEdit(str(SECURITY_PIN))
        self.hf_token = QLineEdit(HF_TOKEN if HF_TOKEN else "")
        self.hf_token.setPlaceholderText("hf_...")
        layout1.addRow("Assistant Name:", self.assistant_name)
        layout1.addRow("Security PIN:", self.security_pin)
        layout1.addRow("Hugging Face Token:", self.hf_token)
        self.pages.addWidget(page1)

        # PAGE 2: Voice
        page2 = QWidget()
        layout2 = QFormLayout(page2)
        layout2.setSpacing(15)
        self.wake_mode = QComboBox()
        self.wake_mode.addItems(["model", "custom"])
        self.wake_mode.setCurrentText(WAKE_MODE)
        self.wake_model = QComboBox()
        self.wake_model.addItems(["hey_jarvis", "alexa", "hey_mycroft"])
        self.wake_model.setCurrentText(WAKE_MODEL)
        self.wake_word = QLineEdit(WAKE_WORD)
        self.wake_threshold = QLineEdit(str(WAKE_THRESHOLD))
        self.whisper_model = QComboBox()
        self.whisper_model.addItems(["tiny.en", "base.en", "small.en", "medium.en", 
                                     "Systran/faster-distil-whisper-large-v3", 
                                     "deepdml/faster-whisper-large-v3-turbo-ct2"])
        self.whisper_model.setCurrentText(WHISPER_MODEL_SIZE)
        self.whisper_compute = QComboBox()
        self.whisper_compute.addItems(["int8", "float16", "float32"])
        self.whisper_compute.setCurrentText(WHISPER_COMPUTE_TYPE)
        layout2.addRow("Wake Mode:", self.wake_mode)
        layout2.addRow("Neural Wake Word:", self.wake_model)
        layout2.addRow("Custom Phrase:", self.wake_word)
        layout2.addRow("Wake Threshold (0-1):", self.wake_threshold)
        layout2.addRow("Whisper Model:", self.whisper_model)
        layout2.addRow("Compute Type:", self.whisper_compute)
        self.pages.addWidget(page2)

        # PAGE 3: Advanced
        page3 = QWidget()
        layout3 = QFormLayout(page3)
        layout3.setSpacing(15)
        self.ollama_model = QComboBox()
        self.ollama_model.addItems(["qwen2.5:3b", "llama3.2:3b", "llama3.2:1b"])
        self.ollama_model.setCurrentText(OLLAMA_MODEL)
        self.ollama_url = QLineEdit(OLLAMA_URL)
        self.max_cmd_sec = QLineEdit(str(MAX_COMMAND_SECONDS))
        self.conv_timeout = QLineEdit(str(CONVERSATION_TIMEOUT))
        self.silence_dur = QLineEdit(str(SILENCE_DURATION))
        self.silence_thresh = QLineEdit(str(SILENCE_THRESHOLD))
        self.sample_rate = QLineEdit(str(SAMPLE_RATE))
        layout3.addRow("Ollama Model:", self.ollama_model)
        layout3.addRow("Ollama URL:", self.ollama_url)
        layout3.addRow("Max Command Length (s):", self.max_cmd_sec)
        layout3.addRow("Conversation Timeout (s):", self.conv_timeout)
        layout3.addRow("Silence Cutoff (s):", self.silence_dur)
        layout3.addRow("Silence Threshold (db):", self.silence_thresh)
        layout3.addRow("Microphone Sample Rate:", self.sample_rate)
        self.pages.addWidget(page3)
        
        # PAGE 4: Memory
        page4 = QWidget()
        layout4 = QVBoxLayout(page4)
        layout4.setSpacing(15)
        
        mem_title = QLabel("Memory Management")
        mem_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout4.addWidget(mem_title)
        
        mem_desc = QLabel("If the AI gets confused or starts hallucinating, you can wipe its memory array to start a fresh conversation. This will NOT delete your settings.")
        mem_desc.setWordWrap(True)
        mem_desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout4.addWidget(mem_desc)
        
        layout4.addStretch()
        
        self.wipe_mem_btn = QPushButton("Wipe Memory (Start New Session)")
        self.wipe_mem_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444; color: white; border-radius: 8px; padding: 12px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        self.wipe_mem_btn.clicked.connect(self.wipe_memory)
        layout4.addWidget(self.wipe_mem_btn)
        
        self.pages.addWidget(page4)

        # Connect Sidebar to Pages
        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        
        # Add to content layout
        content_layout.addWidget(self.sidebar)
        
        # Wrap pages in a layout with a save button at bottom
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.addWidget(self.pages)
        
        right_layout.addStretch()
        save_btn = QPushButton("Save & Apply")
        save_btn.setObjectName("SaveBtn")
        save_btn.clicked.connect(self.save_settings)
        right_layout.addWidget(save_btn)
        
        content_layout.addWidget(right_panel)
        main_layout.addWidget(content_widget)

        self.wake_mode.currentTextChanged.connect(self.toggle_wake)
        self.toggle_wake(self.wake_mode.currentText())

    def toggle_wake(self, text):
        layout = self.pages.widget(1).layout()
        if text == "model":
            self.wake_model.show()
            self.wake_word.hide()
            layout.labelForField(self.wake_word).hide()
            layout.labelForField(self.wake_model).show()
        else:
            self.wake_model.hide()
            self.wake_word.show()
            layout.labelForField(self.wake_model).hide()
            layout.labelForField(self.wake_word).show()

    def save_settings(self):
        from config import USER_DATA_DIR
        import os
        env_path = os.path.join(USER_DATA_DIR, '.env')
        new_settings = {
            'ASSISTANT_NAME': self.assistant_name.text(),
            'SECURITY_PIN': self.security_pin.text(),
            'HF_TOKEN': self.hf_token.text(),
            'WAKE_MODE': self.wake_mode.currentText(),
            'WAKE_MODEL': self.wake_model.currentText(),
            'WAKE_WORD': self.wake_word.text(),
            'WAKE_THRESHOLD': self.wake_threshold.text(),
            'WHISPER_MODEL_SIZE': self.whisper_model.currentText(),
            'WHISPER_COMPUTE_TYPE': self.whisper_compute.currentText(),
            'OLLAMA_MODEL': self.ollama_model.currentText(),
            'OLLAMA_URL': self.ollama_url.text(),
            'MAX_COMMAND_SECONDS': self.max_cmd_sec.text(),
            'CONVERSATION_TIMEOUT': self.conv_timeout.text(),
            'SILENCE_DURATION': self.silence_dur.text(),
            'SILENCE_THRESHOLD': self.silence_thresh.text(),
            'SAMPLE_RATE': self.sample_rate.text(),
        }
        for key, value in new_settings.items():
            if value.strip() != "":
                dotenv.set_key(env_path, key, value)
        self.accept()

    def wipe_memory(self):
        from memory import clear_history
        clear_history()
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Memory Wiped")
        msg.setText("The AI's memory has been completely wiped. You are now starting a fresh session!")
        msg.setStyleSheet("QLabel{color: white; font-size: 13px;} QMessageBox{background-color: #0f172a; border: 1px solid #38bdf8;}")
        msg.exec()

class AssistantThread(QThread):
    def run(self):
        from main import run_voice_mode
        try:
            run_voice_mode()
        except Exception as e:
            print(f"Assistant thread crashed: {e}")

class FloatingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(350, 250)

        self.state = "sleeping"
        self.phase = 0.0
        self.current_text = "Sleeping..."

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30) # slightly faster for smooth rotation

        # Settings button
        self.btn = QPushButton("⚙ Settings", self)
        self.btn.setStyleSheet("""
            QPushButton {
                background: rgba(40,40,50,0.8); color: white; border-radius: 10px; padding: 5px 10px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(60,60,70,0.9); }
        """)
        self.btn.move(240, 15)
        self.btn.resize(90, 30)
        self.btn.clicked.connect(self.open_settings)
        self.btn.hide()

        # Exit button
        self.exit_btn = QPushButton("✖ Exit App", self)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239,68,68,0.8); color: white; border-radius: 10px; padding: 5px 10px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(220,38,38,0.9); }
        """)
        self.exit_btn.move(140, 15)
        self.exit_btn.resize(90, 30)
        self.exit_btn.clicked.connect(self.close_app)
        self.exit_btn.hide()

        signals.state_changed.connect(self.set_state)
        signals.text_updated.connect(self.set_text)

    def set_text(self, text):
        self.current_text = text

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def close_app(self):
        import os, signal
        QApplication.quit()
        os.kill(os.getpid(), signal.SIGTERM)

    def enterEvent(self, event):
        self.btn.show()
        self.exit_btn.show()

    def leaveEvent(self, event):
        # Only hide if the mouse actually left the entire window bounds
        from PyQt6.QtGui import QCursor
        pos = self.mapFromGlobal(QCursor.pos())
        if not self.rect().contains(pos):
            self.btn.hide()
            self.exit_btn.hide()

    def set_state(self, state):
        self.state = state
        self.update()

    def animate(self):
        self.phase += 0.1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Transparent background fill
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        cx, cy = self.width() // 2, 90
        base_radius = 45

        # Draw the 3D rotating ring (loaderCircle)
        painter.save()
        painter.translate(cx, cy)
        
        if self.state == "listening":
            speed = 8
            colors = [QColor(56, 189, 248), QColor(0, 93, 255), QColor(30, 64, 175)] # Light blue, bright blue, deep blue
        elif self.state == "speaking":
            speed = 10
            colors = [QColor(255, 105, 180), QColor(255, 20, 147), QColor(199, 21, 133)] # Neon pinks
        elif self.state == "thinking":
            speed = 6
            colors = [QColor(216, 191, 216), QColor(148, 0, 211), QColor(75, 0, 130)] # Purples
        else:
            speed = 2
            colors = [QColor(150, 150, 150), QColor(100, 100, 100), QColor(60, 60, 60)] # Grays

        painter.rotate(self.phase * speed * 10)

        import math
        from PyQt6.QtGui import QPen
        
        # We draw 3 arcs with different rotation lengths and thicknesses to simulate the 3D inset box-shadow
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i, c in enumerate(colors):
            pen = QPen(c)
            pen.setWidth(4 + i * 3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            c.setAlpha(180 - i * 40)
            pen.setColor(c)
            
            painter.setPen(pen)
            rect_offset = i * 1.5
            radius = base_radius - rect_offset
            # Draw sweeping arcs
            start_angle = int(16 * (i * 60))
            span_angle = int(16 * (270 - i * 40))
            painter.drawArc(int(-radius), int(-radius), int(radius * 2), int(radius * 2), start_angle, span_angle)

        painter.restore()

        # Draw bouncing text (loaderLetter)
        text = self.current_text
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        text_width = painter.fontMetrics().horizontalAdvance(text)
        start_x = cx - (text_width // 2)
        y = cy + base_radius + 40
        
        current_x = start_x
        for i, char in enumerate(text):
            char_width = painter.fontMetrics().horizontalAdvance(char)
            if self.state == "sleeping":
                y_offset = 0
                opacity = 180
            else:
                wave = math.sin(self.phase * 4 - i * 0.5)
                y_offset = wave * -4 # subtle bounce up/down
                opacity = int(255 if wave > 0 else 120)

            painter.setPen(QColor(255, 255, 255, opacity))
            painter.drawText(int(current_x), int(y + y_offset), char)
            current_x += char_width

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
    
    widget = FloatingWidget()
    widget.show()
    
    screen = app.primaryScreen().geometry()
    widget.move(screen.width() // 2 - widget.width() // 2, screen.height() - widget.height() - 150)
    
    thread = AssistantThread()
    thread.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_gui()
