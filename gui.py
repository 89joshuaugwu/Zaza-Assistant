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

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zaza Settings Dashboard")
        self.setFixedSize(500, 480)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1f; color: #fff; }
            QLabel { color: #fff; font-family: 'Segoe UI'; font-size: 13px; font-weight: 500; }
            QTabWidget::pane { border: 1px solid #444; border-radius: 8px; background: #1f1f26; }
            QTabBar::tab { background: #23232c; color: #aaa; padding: 10px 20px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
            QTabBar::tab:selected { background: #0088ff; color: #fff; font-weight: bold; }
            QComboBox, QLineEdit { 
                background-color: #23232c; color: #fff; 
                border: 1px solid #444; border-radius: 6px; padding: 6px; font-size: 13px;
            }
            QComboBox:focus, QLineEdit:focus { border: 1px solid #0088ff; }
            QPushButton { 
                background-color: #0088ff; color: #fff; 
                border-radius: 8px; padding: 12px; font-size: 14px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #0077dd; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        from config import (WAKE_MODE, WAKE_MODEL, WAKE_WORD, WHISPER_MODEL_SIZE, 
                            OLLAMA_MODEL, ASSISTANT_NAME, SECURITY_PIN, OLLAMA_URL,
                            WAKE_THRESHOLD, SAMPLE_RATE, WHISPER_COMPUTE_TYPE,
                            MAX_COMMAND_SECONDS, SILENCE_THRESHOLD, SILENCE_DURATION, 
                            CONVERSATION_TIMEOUT, HF_TOKEN)

        self.tabs = QTabWidget()
        
        # TAB 1: Identity & Security
        tab1 = QWidget()
        layout1 = QFormLayout(tab1)
        layout1.setSpacing(12)
        
        self.assistant_name = QLineEdit(ASSISTANT_NAME)
        self.security_pin = QLineEdit(str(SECURITY_PIN))
        self.hf_token = QLineEdit(HF_TOKEN if HF_TOKEN else "")
        self.hf_token.setPlaceholderText("hf_...")
        
        layout1.addRow("Assistant Name:", self.assistant_name)
        layout1.addRow("Security PIN:", self.security_pin)
        layout1.addRow("Hugging Face Token:", self.hf_token)
        self.tabs.addTab(tab1, "Identity")

        # TAB 2: Voice & Wake
        tab2 = QWidget()
        layout2 = QFormLayout(tab2)
        layout2.setSpacing(12)
        
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
        self.tabs.addTab(tab2, "Voice Engine")

        # TAB 3: Advanced Tweaks
        tab3 = QWidget()
        layout3 = QFormLayout(tab3)
        layout3.setSpacing(12)
        
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
        self.tabs.addTab(tab3, "Advanced")

        layout.addWidget(self.tabs)

        self.wake_mode.currentTextChanged.connect(self.toggle_wake)
        self.toggle_wake(self.wake_mode.currentText())

        save_btn = QPushButton("Save Settings & Close")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

    def toggle_wake(self, text):
        tab2_layout = self.tabs.widget(1).layout()
        if text == "model":
            self.wake_model.show()
            self.wake_word.hide()
            tab2_layout.labelForField(self.wake_word).hide()
            tab2_layout.labelForField(self.wake_model).show()
        else:
            self.wake_model.hide()
            self.wake_word.show()
            tab2_layout.labelForField(self.wake_model).hide()
            tab2_layout.labelForField(self.wake_word).show()

    def save_settings(self):
        env_path = os.path.join(os.path.dirname(__file__), '.env')
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
        self.resize(350, 200)

        self.state = "sleeping"
        self.phase = 0.0
        self.radius = 40

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Spacer for the orb drawing area
        layout.addSpacing(130)

        self.label = QLabel("Sleeping...")
        self.label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.label.setStyleSheet("color: white; background: rgba(30, 30, 40, 0.7); border-radius: 12px; padding: 10px 20px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Wrap label in a layout to center it
        hbox = QHBoxLayout()
        hbox.addWidget(self.label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(hbox)

        # Settings button
        self.btn = QPushButton("⚙ Settings", self)
        self.btn.setStyleSheet("""
            QPushButton {
                background: rgba(40,40,50,0.8); color: white; border-radius: 10px; padding: 5px 10px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(60,60,70,0.9); }
        """)
        self.btn.move(250, 15)
        self.btn.resize(90, 30)
        self.btn.clicked.connect(self.open_settings)
        self.btn.hide()

        signals.state_changed.connect(self.set_state)
        signals.text_updated.connect(self.label.setText)

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def enterEvent(self, event):
        self.btn.show()

    def leaveEvent(self, event):
        # Only hide if the mouse actually left the entire window bounds
        from PyQt6.QtGui import QCursor
        pos = self.mapFromGlobal(QCursor.pos())
        if not self.rect().contains(pos):
            self.btn.hide()

    def set_state(self, state):
        self.state = state
        self.update()

    def animate(self):
        self.phase += 0.2
        if self.state == "listening":
            self.radius = 40 + 8 * math.sin(self.phase)
        elif self.state == "thinking":
            self.radius = 40 + 4 * math.sin(self.phase * 2)
        elif self.state == "speaking":
            self.radius = 40 + 12 * math.fabs(math.sin(self.phase * 3))
        else:
            self.radius = 40
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.state == "sleeping":
            base_color = QColor(80, 80, 80, 255)
            glow_color = QColor(80, 80, 80, 30)
        elif self.state == "listening":
            base_color = QColor(0, 136, 255, 255) # Bright cyan/blue
            glow_color = QColor(0, 136, 255, 60)
        elif self.state == "thinking":
            base_color = QColor(148, 0, 211, 255) # Purple
            glow_color = QColor(148, 0, 211, 60)
        elif self.state == "speaking":
            base_color = QColor(255, 0, 128, 255) # Neon pink
            glow_color = QColor(255, 0, 128, 60)
            
        painter.setPen(Qt.PenStyle.NoPen)
        cx, cy = self.width() // 2, 70
        
        # We will draw 7 vertical bars for the waveform
        num_bars = 7
        bar_width = 8
        spacing = 4
        total_width = num_bars * (bar_width + spacing) - spacing
        start_x = cx - (total_width // 2)
        
        import math
        for i in range(num_bars):
            # Calculate height modulation based on state and phase
            if self.state == "sleeping":
                height = 10
            else:
                # Math magic to make the waveform ripple beautifully
                offset = i * 0.5
                intensity = 15 if self.state == "listening" else (30 if self.state == "speaking" else 20)
                height = 20 + intensity * math.fabs(math.sin(self.phase * 3 + offset))
            
            x = start_x + i * (bar_width + spacing)
            y = cy - (height / 2)
            
            # Draw glow for each bar
            if self.state != "sleeping":
                for g in range(3, 0, -1):
                    painter.setBrush(QBrush(glow_color))
                    glow_w = bar_width + g * 4
                    glow_h = height + g * 8
                    painter.drawRoundedRect(int(x - g * 2), int(y - g * 4), int(glow_w), int(glow_h), 4, 4)
            
            # Draw core bar
            painter.setBrush(QBrush(base_color))
            painter.drawRoundedRect(int(x), int(y), bar_width, int(height), bar_width // 2, bar_width // 2)

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
