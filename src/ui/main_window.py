"""
VoGenFlow Modernized Desktop Application (PyQt6)
Industrial-Grade Desktop Client featuring Monolith Luxury Aesthetics (Onyx Black & Vellum Light),
Voice Dictation & Audio Visualizer, 6-Seat Council Deliberation Chamber, Multi-Tab Specification Studio,
ProjectIR Telemetry & Schema Inspector, and 1-Click Client-Side Word (.docx) Export.
"""

import datetime
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, QRegularExpression, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QIcon, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.audio_recorder import AudioRecorder
from src.config import Config, DOCS_DIR, OUTPUT_DIR, TEMP_AUDIO_DIR, has_groq_key
from src.export_service import ExportService
from src.ui.audio_visualizer import AudioVisualizer
from src.ui.syntax_highlighter import MarkdownHighlighter

logger = logging.getLogger("vogenflow.desktop")

# =============================================================================
# MONOLITH LUXURY STYLESHEETS (ONYX TRUE BLACK & VELLUM LUXURY LIGHT)
# =============================================================================

ONYX_STYLESHEET = """
QMainWindow, QWidget#centralWidget {
    background-color: #000000;
    color: #f3f4f6;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Header & Panels */
QFrame#headerFrame {
    background-color: #0c0c0e;
    border-bottom: 1px solid #26262b;
    padding: 8px 16px;
}
QFrame#cardFrame {
    background-color: #0e0e12;
    border: 1px solid #26262b;
    border-radius: 8px;
}
QFrame#agentCard {
    background-color: #0f0f13;
    border: 1px solid #26262b;
    border-radius: 8px;
}
QFrame#agentCard:hover {
    border-color: #d4af37;
}

/* Group Boxes */
QGroupBox {
    background-color: #0a0a0c;
    border: 1px solid #26262b;
    border-radius: 8px;
    margin-top: 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.05em;
    color: #d4af37;
    padding-top: 16px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #0a0a0c;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #26262b;
    background-color: #0a0a0c;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #121216;
    color: #9ca3af;
    padding: 9px 18px;
    border: 1px solid #26262b;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
    font-weight: 600;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: #1c1c22;
    color: #ffffff;
    border-bottom: 2px solid #d4af37;
}
QTabBar::tab:hover {
    color: #f3f4f6;
    background-color: #16161b;
}

/* Buttons */
QPushButton {
    background-color: #16161b;
    color: #f3f4f6;
    border: 1px solid #2e2e38;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #22222a;
    border-color: #d4af37;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #101014;
}
QPushButton:disabled {
    background-color: #121215;
    color: #52525b;
    border-color: #1f1f23;
}
QPushButton#primaryGoldBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d4af37, stop:1 #f59e0b);
    color: #000000;
    font-weight: 700;
    border: none;
    padding: 9px 18px;
}
QPushButton#primaryGoldBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e5be48, stop:1 #fbbf24);
}
QPushButton#primaryGoldBtn:disabled {
    background: #332b14;
    color: #786432;
}
QPushButton#exportDocxBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
    color: #ffffff;
    font-weight: 700;
    border: none;
    padding: 8px 16px;
}
QPushButton#exportDocxBtn:hover {
    background: #3b82f6;
}
QPushButton#stopRecordBtn {
    background-color: #dc2626;
    color: #ffffff;
    font-weight: 700;
    border: none;
    padding: 8px 16px;
}
QPushButton#stopRecordBtn:hover {
    background-color: #ef4444;
}

/* Text & Inputs */
QTextEdit, QPlainTextEdit, QLineEdit {
    background-color: #060608;
    border: 1px solid #222228;
    border-radius: 6px;
    color: #e5e7eb;
    padding: 8px;
    selection-background-color: #3f3112;
    selection-color: #fef08a;
    font-size: 12px;
}
QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {
    border-color: #d4af37;
}

/* Combobox */
QComboBox {
    background-color: #121216;
    border: 1px solid #26262b;
    border-radius: 6px;
    padding: 5px 10px;
    color: #f3f4f6;
    font-size: 12px;
    min-height: 22px;
}
QComboBox:hover {
    border-color: #d4af37;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #141418;
    border: 1px solid #26262b;
    selection-background-color: #24242c;
    selection-color: #d4af37;
    color: #f3f4f6;
}

/* Tree & Tables */
QTreeWidget, QTableWidget {
    background-color: #070709;
    border: 1px solid #222228;
    border-radius: 6px;
    color: #f3f4f6;
    gridline-color: #1a1a20;
    font-size: 12px;
}
QTreeWidget::item:selected, QTableWidget::item:selected {
    background-color: #22222a;
    color: #d4af37;
}
QHeaderView::section {
    background-color: #101014;
    color: #9ca3af;
    padding: 6px;
    border: 1px solid #1f1f25;
    font-weight: 600;
    font-size: 11px;
}

/* Progress & Scrollbars */
QProgressBar {
    background-color: #101014;
    border: 1px solid #26262b;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
    font-weight: 600;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d4af37, stop:1 #f59e0b);
    border-radius: 3px;
}
QScrollBar:vertical {
    background: #08080a;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #27272a;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #d4af37;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

VELLUM_STYLESHEET = """
QMainWindow, QWidget#centralWidget {
    background-color: #f7f6f2;
    color: #0a0a0a;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Header & Panels */
QFrame#headerFrame {
    background-color: #f2eee6;
    border-bottom: 1px solid #ded8cb;
    padding: 8px 16px;
}
QFrame#cardFrame {
    background-color: #ffffff;
    border: 1px solid #e2ddd3;
    border-radius: 8px;
}
QFrame#agentCard {
    background-color: #ffffff;
    border: 1px solid #e2ddd3;
    border-radius: 8px;
}
QFrame#agentCard:hover {
    border-color: #b8860b;
}

/* Group Boxes */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e2ddd3;
    border-radius: 8px;
    margin-top: 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.05em;
    color: #b8860b;
    padding-top: 16px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #ffffff;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #e2ddd3;
    background-color: #ffffff;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #ede9e0;
    color: #525252;
    padding: 9px 18px;
    border: 1px solid #e2ddd3;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
    font-weight: 600;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0a0a0a;
    border-bottom: 2px solid #b8860b;
}
QTabBar::tab:hover {
    color: #171717;
    background-color: #f4efe6;
}

/* Buttons */
QPushButton {
    background-color: #fdfbf7;
    color: #0a0a0a;
    border: 1px solid #d5cebf;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #f0ece3;
    border-color: #b8860b;
    color: #0a0a0a;
}
QPushButton:pressed {
    background-color: #e4dfd3;
}
QPushButton:disabled {
    background-color: #f1ede5;
    color: #a8a29e;
    border-color: #ded9cd;
}
QPushButton#primaryGoldBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b8860b, stop:1 #d97706);
    color: #ffffff;
    font-weight: 700;
    border: none;
    padding: 9px 18px;
}
QPushButton#primaryGoldBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9a6f08, stop:1 #b45309);
}
QPushButton#primaryGoldBtn:disabled {
    background: #e2ddd3;
    color: #a8a29e;
}
QPushButton#exportDocxBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
    color: #ffffff;
    font-weight: 700;
    border: none;
    padding: 8px 16px;
}
QPushButton#exportDocxBtn:hover {
    background: #1d4ed8;
}
QPushButton#stopRecordBtn {
    background-color: #dc2626;
    color: #ffffff;
    font-weight: 700;
    border: none;
    padding: 8px 16px;
}
QPushButton#stopRecordBtn:hover {
    background-color: #b91c1c;
}

/* Text & Inputs */
QTextEdit, QPlainTextEdit, QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d5cebf;
    border-radius: 6px;
    color: #0a0a0a;
    padding: 8px;
    selection-background-color: #fef3c7;
    selection-color: #78350f;
    font-size: 12px;
}
QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {
    border-color: #b8860b;
}

/* Combobox */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #d5cebf;
    border-radius: 6px;
    padding: 5px 10px;
    color: #0a0a0a;
    font-size: 12px;
    min-height: 22px;
}
QComboBox:hover {
    border-color: #b8860b;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d5cebf;
    selection-background-color: #f5f0e6;
    selection-color: #b8860b;
    color: #0a0a0a;
}

/* Tree & Tables */
QTreeWidget, QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e2ddd3;
    border-radius: 6px;
    color: #0a0a0a;
    gridline-color: #f0ece3;
    font-size: 12px;
}
QTreeWidget::item:selected, QTableWidget::item:selected {
    background-color: #f4efe4;
    color: #b8860b;
}
QHeaderView::section {
    background-color: #f3efe8;
    color: #44403c;
    padding: 6px;
    border: 1px solid #ded8cb;
    font-weight: 600;
    font-size: 11px;
}

/* Progress & Scrollbars */
QProgressBar {
    background-color: #ede9e0;
    border: 1px solid #d5cebf;
    border-radius: 4px;
    text-align: center;
    color: #0a0a0a;
    font-size: 11px;
    font-weight: 600;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b8860b, stop:1 #d97706);
    border-radius: 3px;
}
QScrollBar:vertical {
    background: #f7f6f2;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #d5cebf;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #b8860b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

# =============================================================================
# WORKER SIGNALS & THREADS (NON-BLOCKING ASYNC ENGINE)
# =============================================================================

class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str, object)


class TranscriptionWorker(QThread):
    """Speech-to-Text inference background worker supporting local STT or HTTP Gateway."""

    def __init__(self, audio_path: str, model: str = "whisper-large-v3-turbo", mode: str = "auto", gateway_url: str = "http://127.0.0.1:8080"):
        super().__init__()
        self.audio_path = audio_path
        self.model = model
        self.mode = mode
        self.gateway_url = gateway_url.rstrip("/")
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit("Transcribing audio...", {"status": "starting"})
            # Try Gateway if mode is http
            if self.mode == "http":
                try:
                    import urllib.request
                    boundary = f"----VoGenFlow{time.time()}"
                    with open(self.audio_path, "rb") as f:
                        file_bytes = f.read()
                    data = (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; name="file"; filename="{Path(self.audio_path).name}"\r\n'
                        f"Content-Type: audio/wav\r\n\r\n"
                    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
                    req = urllib.request.Request(
                        f"{self.gateway_url}/api/stt/transcribe",
                        data=data,
                        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
                    )
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        self.signals.finished.emit(res_json)
                        return
                except Exception as net_err:
                    logger.warning("Gateway STT transcription failed, falling back to local STT: %s", str(net_err))

            # Local fallback
            from src.stt_service import STTService
            stt = STTService()
            res = stt.transcribe(self.audio_path, model=self.model)
            res_dict = res.to_dict() if hasattr(res, "to_dict") else {"text": str(res), "duration_seconds": 0.0, "latency_seconds": 0.0}
            self.signals.finished.emit(res_dict)
        except Exception as e:
            self.signals.error.emit(str(e))


class CouncilDeliberationWorker(QThread):
    """Scatter-Gather Council Deliberation worker supporting HTTP Gateway or local CouncilEngine."""

    def __init__(self, transcript: str, preset: str = "standard", mode: str = "auto", gateway_url: str = "http://127.0.0.1:8080"):
        super().__init__()
        self.transcript = transcript
        self.preset = preset
        self.mode = mode
        self.gateway_url = gateway_url.rstrip("/")
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.signals.progress.emit("Council convened. Deliberation starting...", {"role": "system"})

            # Attempt HTTP Gateway if mode is http or auto
            if self.mode in ("http", "auto"):
                try:
                    payload = json.dumps({"transcript": self.transcript, "preset": self.preset}).encode("utf-8")
                    req = urllib.request.Request(
                        f"{self.gateway_url}/api/council/deliberate",
                        data=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=45) as resp:
                        result = json.loads(resp.read().decode("utf-8"))
                        self.signals.finished.emit(result)
                        return
                except Exception as net_err:
                    if self.mode == "http":
                        logger.warning("Live Gateway unavailable: %s", str(net_err))
                        # Fall through to local engine rather than hard failing

            # Local In-Process CouncilEngine execution
            from src.council_engine import CouncilEngine

            def progress_cb(role: str, data: Dict[str, Any]):
                self.signals.progress.emit(data.get("message", f"{role} working..."), data)

            engine = CouncilEngine()
            result = engine.deliberate(
                transcript=self.transcript,
                preset=self.preset,
                progress_callback=progress_cb
            )
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


# =============================================================================
# WIDGETS: DRAG & DROP ZONE & 6-SEAT AGENT CARD
# =============================================================================

class DropZoneWidget(QFrame):
    """Luxury Drag-and-drop file target widget."""

    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(64)
        self.setObjectName("cardFrame")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.label = QLabel("📥 Drag & Drop Audio File (.wav, .mp3, .m4a, .ogg, .flac)", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #a0aec0; font-size: 11px; font-weight: 500;")
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            ext = Path(file_path).suffix.lower()
            valid_exts = [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"]
            if ext in valid_exts:
                self.file_dropped.emit(file_path)
            else:
                QMessageBox.warning(self, "Unsupported Format", f"Format {ext} is not supported.")


class CouncilAgentCard(QFrame):
    """Interactive dossier card for an individual Council Member."""

    def __init__(
        self,
        role_key: str,
        title: str,
        role_desc: str,
        seat_badge: str,
        target_doc: str,
        default_model: str,
        parent=None,
    ):
        super().__init__(parent)
        self.role_key = role_key
        self.title = title
        self.target_doc = target_doc
        self.default_model = default_model
        self.setObjectName("agentCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Top Bar: Seat Badge & Status Indicator
        top_layout = QHBoxLayout()
        self.seat_label = QLabel(seat_badge)
        self.seat_label.setStyleSheet("font-size: 10px; font-weight: 700; color: #d4af37;")
        self.status_pill = QLabel("IDLE")
        self.status_pill.setStyleSheet(
            "font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; "
            "background-color: #27272a; color: #a1a1aa;"
        )
        top_layout.addWidget(self.seat_label)
        top_layout.addStretch()
        top_layout.addWidget(self.status_pill)
        layout.addLayout(top_layout)

        # Member Name & Role
        name_label = QLabel(title)
        name_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        self.name_label = name_label
        layout.addWidget(name_label)

        role_label = QLabel(f"{role_desc} ➔ {target_doc}")
        role_label.setStyleSheet("font-size: 10px; color: #9ca3af;")
        self.role_label = role_label
        layout.addWidget(role_label)

        # Telemetry info
        self.telemetry_label = QLabel(f"Model: {default_model} | 0 tokens | 0.0s")
        self.telemetry_label.setStyleSheet("font-size: 10px; color: #71717a; font-family: monospace;")
        layout.addWidget(self.telemetry_label)

        # Thoughts / Reasoning Area
        self.thoughts_edit = QTextEdit()
        self.thoughts_edit.setReadOnly(True)
        self.thoughts_edit.setMaximumHeight(85)
        self.thoughts_edit.setPlaceholderText("Awaiting architectural deliberation...")
        self.thoughts_edit.setStyleSheet(
            "font-size: 11px; background-color: #060608; border: 1px solid #1f1f23; border-radius: 4px; padding: 4px;"
        )
        layout.addWidget(self.thoughts_edit)

    def set_status(self, status: str, message: str = "", tokens: int = 0, latency: float = 0.0, thoughts: str = ""):
        """Update agent deliberation status and telemetry."""
        status_upper = status.upper()
        self.status_pill.setText(status_upper)

        if "DELIBERAT" in status_upper or "THINK" in status_upper:
            self.status_pill.setStyleSheet(
                "font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; "
                "background-color: #78350f; color: #fef08a;"
            )
        elif "COMPLETE" in status_upper or "READY" in status_upper:
            self.status_pill.setStyleSheet(
                "font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; "
                "background-color: #064e3b; color: #6ee7b7;"
            )
        else:
            self.status_pill.setStyleSheet(
                "font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; "
                "background-color: #27272a; color: #a1a1aa;"
            )

        if tokens > 0 or latency > 0.0:
            self.telemetry_label.setText(f"Model: {self.default_model} | {tokens} tokens | {latency:.2f}s")

        if thoughts:
            self.thoughts_edit.setPlainText(thoughts)
        elif message:
            self.thoughts_edit.setPlainText(message)


# =============================================================================
# MAIN WINDOW: MODERNIZED LUXURY VOGENFLOW CLIENT
# =============================================================================

class MainWindow(QMainWindow):
    """VoGenFlow Modernized Desktop Application Window."""

    def __init__(self, default_theme: str = "onyx", default_backend: str = "auto"):
        super().__init__()
        self.setWindowTitle("VoGenFlow // Autonomous Architecture & Multi-Agent Council Studio")
        self.resize(1440, 920)
        self.setMinimumSize(1100, 750)

        # Core State
        self.current_theme = default_theme.lower()
        self.backend_mode = default_backend
        self.gateway_online = False
        self.current_audio_file: Optional[str] = None
        self.active_worker: Optional[QThread] = None

        # Data Cache
        self.artifacts: Dict[str, str] = {}
        self.project_ir: Optional[Dict[str, Any]] = None
        self.seat_dossier: Dict[str, Any] = {}

        # Services & Recorder
        self.recorder = AudioRecorder(amplitude_callback=self._on_audio_amplitude)
        self.record_timer = QTimer(self)
        self.record_timer.timeout.connect(self._update_record_clock)

        # Gateway ping timer
        self.ping_timer = QTimer(self)
        self.ping_timer.timeout.connect(self._check_gateway_health)
        self.ping_timer.start(5000)

        self._init_ui()
        self.set_theme(self.current_theme)
        QTimer.singleShot(200, self._check_gateway_health)

    def closeEvent(self, event):
        """Safely stop background timers and workers upon window closure."""
        try:
            if hasattr(self, "ping_timer") and self.ping_timer.isActive():
                self.ping_timer.stop()
            if hasattr(self, "record_timer") and self.record_timer.isActive():
                self.record_timer.stop()
            if hasattr(self, "visualizer") and hasattr(self.visualizer, "decay_timer") and self.visualizer.decay_timer.isActive():
                self.visualizer.decay_timer.stop()
            if hasattr(self, "active_worker") and self.active_worker is not None:
                if self.active_worker.isRunning():
                    self.active_worker.requestInterruption()
                    self.active_worker.quit()
                    self.active_worker.wait(1500)
        except Exception:
            pass
        super().closeEvent(event)

    def _init_ui(self):
        """Build top-level UI with Header Bar and Navigation Views."""
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Luxury Header Bar
        header = self._build_header_bar()
        root_layout.addWidget(header)

        # 2. Main Workspace View Switcher (Tabs)
        self.main_nav_tabs = QTabWidget()
        self.main_nav_tabs.setContentsMargins(12, 10, 12, 10)

        # View 1: Voice & Ingress
        self.voice_tab = self._build_voice_panel()
        self.main_nav_tabs.addTab(self.voice_tab, "🎙️ Voice & Audio Ingress")

        # View 2: Live Council Deliberation Chamber
        self.council_tab = self._build_council_chamber_panel()
        self.main_nav_tabs.addTab(self.council_tab, "🏛️ Council Deliberation Chamber")

        # View 3: Multi-Tab Specification Studio
        self.studio_tab = self._build_specification_studio_panel()
        self.main_nav_tabs.addTab(self.studio_tab, "📑 Specification Studio")

        # View 4: ProjectIR Telemetry & Schema Inspector
        self.project_ir_tab = self._build_project_ir_panel()
        self.main_nav_tabs.addTab(self.project_ir_tab, "⚡ ProjectIR Telemetry & Schema")

        root_layout.addWidget(self.main_nav_tabs, 1)

        # 3. Bottom Status Strip
        status_bar_layout = QHBoxLayout()
        status_bar_layout.setContentsMargins(16, 6, 16, 8)
        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("color: #71717a; font-size: 11px;")
        self.global_progress = QProgressBar()
        self.global_progress.setRange(0, 0)
        self.global_progress.setVisible(False)
        self.global_progress.setMaximumWidth(220)
        self.global_progress.setFixedHeight(12)

        status_bar_layout.addWidget(self.status_label, 1)
        status_bar_layout.addWidget(self.global_progress)
        root_layout.addLayout(status_bar_layout)

    # -------------------------------------------------------------------------
    # HEADER BAR
    # -------------------------------------------------------------------------
    def _build_header_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("headerFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Title & Luxury Brand Badge
        title_box = QHBoxLayout()
        logo_label = QLabel("⚡ VOGENFLOW")
        logo_font = QFont()
        logo_font.setBold(True)
        logo_font.setPointSize(13)
        logo_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        logo_label.setFont(logo_font)
        logo_label.setStyleSheet("color: #d4af37;")

        badge = QLabel("DESKTOP v2.0")
        badge.setStyleSheet(
            "font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; "
            "background-color: #26262b; color: #a1a1aa;"
        )

        title_box.addWidget(logo_label)
        title_box.addWidget(badge)
        layout.addLayout(title_box)

        layout.addStretch()

        # Connection Mode Selector & Status Pill
        self.gateway_pill = QLabel("○ CHECKING GATEWAY...")
        self.gateway_pill.setStyleSheet(
            "font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 12px; "
            "background-color: #1f1f23; color: #a1a1aa;"
        )
        layout.addWidget(self.gateway_pill)

        self.backend_combo = QComboBox()
        self.backend_combo.addItems([
            "Live HTTP Gateway (127.0.0.1:8080)",
            "In-Process Council Engine",
        ])
        self.backend_combo.currentIndexChanged.connect(self._on_backend_mode_changed)
        layout.addWidget(self.backend_combo)

        # Council Preset Combo
        layout.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Standard Monolith Council (6-Seat)",
            "Hardcore Security Pentest Council",
            "Lean MVP Sprint Council"
        ])
        layout.addWidget(self.preset_combo)

        # Theme Switcher Button
        self.theme_btn = QPushButton("☀️ Vellum Light")
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        # API Keys Button
        self.api_btn = QPushButton("🔑 API Keys")
        self.api_btn.clicked.connect(self._prompt_api_key)
        layout.addWidget(self.api_btn)

        return frame

    # -------------------------------------------------------------------------
    # VIEW 1: VOICE DICTATION & INGRESS
    # -------------------------------------------------------------------------
    def _build_voice_panel(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Left Column: Audio Input, Visualizer, Files
        left_box = QGroupBox("1. AUDIO CAPTURE & ACOUSTIC INGRESS")
        left_layout = QVBoxLayout(left_box)
        left_layout.setSpacing(12)

        # Real-time Visualizer
        self.visualizer = AudioVisualizer(num_bars=32)
        left_layout.addWidget(self.visualizer)

        # High-Contrast Recording Clock
        self.record_time_label = QLabel("00:00.0")
        self.record_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.record_time_label.setStyleSheet("font-size: 26px; font-weight: 800; font-family: monospace; color: #f3f4f6;")
        left_layout.addWidget(self.record_time_label)

        # Recording Action Buttons
        record_btns = QHBoxLayout()
        self.record_btn = QPushButton("🎙️ Start Recording")
        self.record_btn.setStyleSheet("font-weight: 700; padding: 10px;")
        self.record_btn.clicked.connect(self._toggle_recording)

        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._toggle_pause)

        record_btns.addWidget(self.record_btn, 2)
        record_btns.addWidget(self.pause_btn, 1)
        left_layout.addLayout(record_btns)

        # Drag and Drop Target Zone
        self.drop_zone = DropZoneWidget()
        self.drop_zone.file_dropped.connect(self._on_audio_file_selected)
        left_layout.addWidget(self.drop_zone)

        # Browse & Sample Loader Buttons
        file_actions = QHBoxLayout()
        self.browse_btn = QPushButton("📂 Browse Audio File...")
        self.browse_btn.clicked.connect(self._browse_audio_file)

        self.sample_btn = QPushButton("✨ Load Sample Voice Memo")
        self.sample_btn.clicked.connect(self.load_sample_voice_memo)

        file_actions.addWidget(self.browse_btn)
        file_actions.addWidget(self.sample_btn)
        left_layout.addLayout(file_actions)

        # Active File Label
        self.selected_file_label = QLabel("No audio selected.")
        self.selected_file_label.setWordWrap(True)
        self.selected_file_label.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        left_layout.addWidget(self.selected_file_label)

        # STT Model & Transcribe Trigger
        stt_box = QHBoxLayout()
        stt_box.addWidget(QLabel("STT Model:"))
        self.stt_model_combo = QComboBox()
        self.stt_model_combo.addItems(["whisper-large-v3-turbo", "whisper-large-v3"])
        stt_box.addWidget(self.stt_model_combo)
        left_layout.addLayout(stt_box)

        self.transcribe_btn = QPushButton("⚡ Transcribe Audio to Text")
        self.transcribe_btn.setObjectName("primaryGoldBtn")
        self.transcribe_btn.clicked.connect(self.transcribe_audio)
        left_layout.addWidget(self.transcribe_btn)

        left_layout.addStretch()
        layout.addWidget(left_box, 4)

        # Right Column: Spoken Transcript & Prompt Workspace
        right_box = QGroupBox("2. SPOKEN TRANSCRIPT & CANONICAL PROMPT WORKSPACE")
        right_layout = QVBoxLayout(right_box)
        right_layout.setSpacing(10)

        self.transcript_edit = QTextEdit()
        self.transcript_edit.setPlaceholderText(
            "Speak into microphone or load an audio file...\n"
            "Your recognized architecture brainstorm will appear here automatically.\n"
            "You can also freely paste or edit your project concept here directly."
        )
        self.transcript_edit.textChanged.connect(self._update_transcript_telemetry)
        right_layout.addWidget(self.transcript_edit, 1)

        # Telemetry info
        self.transcript_stats_label = QLabel("Words: 0 | Estimated Duration: 0.0s")
        self.transcript_stats_label.setStyleSheet("color: #71717a; font-size: 11px; font-family: monospace;")
        right_layout.addWidget(self.transcript_stats_label)

        # RAG Grounding Section
        rag_group = QFrame()
        rag_group.setObjectName("cardFrame")
        rag_layout = QHBoxLayout(rag_group)
        rag_layout.setContentsMargins(10, 8, 10, 8)
        self.rag_checkbox = QCheckBox("Enable Codebase / Curated RAG Grounding")
        self.rag_checkbox.setChecked(True)
        self.index_repo_btn = QPushButton("📁 Index Directory...")
        self.index_repo_btn.clicked.connect(self._index_rag_directory)
        self.rag_stats_label = QLabel("Grounded in 16 Curated Blueprints")
        self.rag_stats_label.setStyleSheet("color: #a1a1aa; font-size: 10px;")

        rag_layout.addWidget(self.rag_checkbox)
        rag_layout.addWidget(self.index_repo_btn)
        rag_layout.addWidget(self.rag_stats_label)
        right_layout.addWidget(rag_group)

        # PRIMARY CTA: Convene Council
        self.convene_btn = QPushButton("🚀 Convene 6-Seat Council & Synthesize Architecture")
        self.convene_btn.setObjectName("primaryGoldBtn")
        self.convene_btn.setStyleSheet("font-size: 14px; padding: 12px; font-weight: 800;")
        self.convene_btn.clicked.connect(self.convene_council)
        right_layout.addWidget(self.convene_btn)

        layout.addWidget(right_box, 6)
        return container

    # -------------------------------------------------------------------------
    # VIEW 2: LIVE COUNCIL DELIBERATION CHAMBER
    # -------------------------------------------------------------------------
    def _build_council_chamber_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Chamber Header Strip
        chamber_header = QHBoxLayout()
        self.chamber_status_label = QLabel("COUNCIL STATUS: IDLE // READY TO DELIBERATE")
        self.chamber_status_label.setStyleSheet("font-size: 13px; font-weight: 800; color: #d4af37; letter-spacing: 0.08em;")

        self.chamber_progress_bar = QProgressBar()
        self.chamber_progress_bar.setRange(0, 100)
        self.chamber_progress_bar.setValue(0)
        self.chamber_progress_bar.setFixedHeight(14)
        self.chamber_progress_bar.setMaximumWidth(280)

        chamber_header.addWidget(self.chamber_status_label)
        chamber_header.addStretch()
        chamber_header.addWidget(self.chamber_progress_bar)
        layout.addLayout(chamber_header)

        # 6-Seat Grid
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(12)

        self.agent_cards: Dict[str, CouncilAgentCard] = {}

        # 1. Product Manager
        self.agent_cards["pm_agent"] = CouncilAgentCard(
            role_key="pm_agent",
            title="1. Product Manager",
            role_desc="Strategy, Personas, P0/P1 SLAs, STRIDE Threat Model",
            seat_badge="SEAT 1 // CANONICAL CORE",
            target_doc="PRD.md",
            default_model="openai/gpt-oss-120b"
        )
        grid.addWidget(self.agent_cards["pm_agent"], 0, 0)

        # 2. System Architect
        self.agent_cards["architect_agent"] = CouncilAgentCard(
            role_key="architect_agent",
            title="2. System Architect",
            role_desc="Microservice Topology, C4 DDL, Partitioned PostgreSQL 16",
            seat_badge="SEAT 2 // PARALLEL FAN-OUT",
            target_doc="Architecture.md",
            default_model="openai/gpt-oss-120b"
        )
        grid.addWidget(self.agent_cards["architect_agent"], 0, 1)

        # 3. UI/UX Engineer
        self.agent_cards["ui_agent"] = CouncilAgentCard(
            role_key="ui_agent",
            title="3. UI/UX Engineer",
            role_desc="Monolith Luxury Design Tokens, Brutalist Components",
            seat_badge="SEAT 3 // PARALLEL FAN-OUT",
            target_doc="design.md",
            default_model="meta-llama/llama-3.3-70b-versatile"
        )
        grid.addWidget(self.agent_cards["ui_agent"], 0, 2)

        # 4. Lifecycle Engineer
        self.agent_cards["systems_agent"] = CouncilAgentCard(
            role_key="systems_agent",
            title="4. Systems Lifecycle Engineer",
            role_desc="Sequence Flows, State Transitions, Failure Recovery Matrix",
            seat_badge="SEAT 4 // PARALLEL FAN-OUT",
            target_doc="Flow.md",
            default_model="openai/gpt-oss-120b"
        )
        grid.addWidget(self.agent_cards["systems_agent"], 1, 0)

        # 5. Agile Delivery Lead
        self.agent_cards["agile_agent"] = CouncilAgentCard(
            role_key="agile_agent",
            title="5. Agile Delivery Lead",
            role_desc="Milestones M1-M4, Phased Tasks, Verification Suite",
            seat_badge="SEAT 5 // PARALLEL FAN-OUT",
            target_doc="tasks.md",
            default_model="meta-llama/llama-3.3-70b-versatile"
        )
        grid.addWidget(self.agent_cards["agile_agent"], 1, 1)

        # 6. Delta Refiner
        self.agent_cards["diff_agent"] = CouncilAgentCard(
            role_key="diff_agent",
            title="6. Delta Refiner",
            role_desc="Zero-shot IR, Master Execution Bundle, Downstream Contracts",
            seat_badge="SEAT 6 // MASTER GATHER",
            target_doc="master_execution_bundle.md",
            default_model="openai/gpt-oss-120b"
        )
        grid.addWidget(self.agent_cards["diff_agent"], 1, 2)

        layout.addWidget(grid_widget, 1)

        # Bottom Deliberation Event Log & Action Bar
        bottom_box = QHBoxLayout()
        self.chamber_log_edit = QTextEdit()
        self.chamber_log_edit.setReadOnly(True)
        self.chamber_log_edit.setMaximumHeight(85)
        self.chamber_log_edit.setPlaceholderText("Council activity event log will stream here...")
        self.chamber_log_edit.setStyleSheet("font-size: 11px; font-family: monospace; color: #a1a1aa;")
        bottom_box.addWidget(self.chamber_log_edit, 1)

        self.open_studio_btn = QPushButton("Open in Specification Studio ➔")
        self.open_studio_btn.setObjectName("primaryGoldBtn")
        self.open_studio_btn.clicked.connect(lambda: self.main_nav_tabs.setCurrentIndex(2))
        bottom_box.addWidget(self.open_studio_btn)

        layout.addLayout(bottom_box)
        return container

    # -------------------------------------------------------------------------
    # VIEW 3: MULTI-TAB SPECIFICATION STUDIO
    # -------------------------------------------------------------------------
    def _build_specification_studio_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Top Action Bar: Word (.docx) Export & Directory Export
        action_bar = QHBoxLayout()
        studio_title = QLabel("SPECIFICATION STUDIO")
        studio_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #d4af37; letter-spacing: 0.08em;")
        action_bar.addWidget(studio_title)

        action_bar.addStretch()

        # CLIENT-SIDE WORD (.DOCX) EXPORT BUTTON
        self.export_docx_btn = QPushButton("📄 Export to Word (.docx)")
        self.export_docx_btn.setObjectName("exportDocxBtn")
        self.export_docx_btn.setToolTip("Bundle all 5 specifications into a clean, luxury Word document via python-docx")
        self.export_docx_btn.clicked.connect(self.export_to_docx)
        action_bar.addWidget(self.export_docx_btn)

        self.export_dir_btn = QPushButton("💾 Save All to Folder...")
        self.export_dir_btn.clicked.connect(self._export_to_directory)
        action_bar.addWidget(self.export_dir_btn)

        layout.addLayout(action_bar)

        # Multi-Tab Specifications
        self.spec_tabs = QTabWidget()
        self.spec_editors: Dict[str, QTextEdit] = {}
        self.spec_previews: Dict[str, QTextEdit] = {}
        self.spec_stacks: Dict[str, QStackedWidget] = {}
        self.highlighters: Dict[str, MarkdownHighlighter] = {}

        specs = [
            ("PRD.md", "PRD.md", "Executive Problem Statement, Target Personas, P0/P1 SLAs, STRIDE Threat Matrix"),
            ("Architecture.md", "Architecture.md", "Microservices Topology, PostgreSQL 16 DDL with RLS, API Contracts"),
            ("Flow.md", "Flow.md", "Sequence Flows, State Transitions, Failure Recovery Matrix"),
            ("tasks.md", "tasks.md", "Milestones M1-M4, Concrete Engineering Checklists"),
            ("design.md", "design.md", "Monolith Luxury Design Tokens, Brutalist Components"),
            ("Bundle", "master_execution_bundle.md", "Master Execution Bundle & Downstream Contracts"),
        ]

        for tab_label, file_key, tooltip in specs:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            tab_layout.setContentsMargins(8, 8, 8, 8)
            tab_layout.setSpacing(6)

            # Sub-header toolbar for tab
            sub_bar = QHBoxLayout()
            doc_desc = QLabel(tooltip)
            doc_desc.setStyleSheet("color: #71717a; font-size: 11px;")
            sub_bar.addWidget(doc_desc)
            sub_bar.addStretch()

            # Raw vs Preview Toggle
            toggle_btn = QPushButton("👁️ Toggle Markdown Preview")
            copy_btn = QPushButton("📋 Copy")
            save_single_btn = QPushButton("💾 Save As...")

            sub_bar.addWidget(toggle_btn)
            sub_bar.addWidget(copy_btn)
            sub_bar.addWidget(save_single_btn)
            tab_layout.addLayout(sub_bar)

            # Stacked widget with index 0: Raw Editor, index 1: Rendered Preview
            stack = QStackedWidget()

            raw_editor = QTextEdit()
            raw_editor.setFont(QFont("Consolas", 10))
            raw_editor.setPlaceholderText(f"{file_key} will be synthesized here upon Council deliberation...")
            highlighter = MarkdownHighlighter(raw_editor.document(), theme=self.current_theme)
            self.highlighters[file_key] = highlighter

            preview = QTextEdit()
            preview.setReadOnly(True)
            preview.setPlaceholderText(f"Rendered preview of {file_key}...")

            stack.addWidget(raw_editor)
            stack.addWidget(preview)
            tab_layout.addWidget(stack, 1)

            # Wire buttons
            toggle_btn.clicked.connect(lambda checked, s=stack, r=raw_editor, p=preview: self._toggle_preview_mode(s, r, p))
            copy_btn.clicked.connect(lambda checked, r=raw_editor: self._copy_to_clipboard(r.toPlainText()))
            save_single_btn.clicked.connect(lambda checked, fk=file_key, r=raw_editor: self._save_single_file(fk, r.toPlainText()))

            self.spec_editors[file_key] = raw_editor
            self.spec_previews[file_key] = preview
            self.spec_stacks[file_key] = stack
            self.spec_tabs.addTab(tab_widget, tab_label)

        layout.addWidget(self.spec_tabs, 1)
        return container

    def _toggle_preview_mode(self, stack: QStackedWidget, raw_editor: QTextEdit, preview: QTextEdit):
        """Toggle between Raw Markdown Editor and Native Rendered Markdown Preview."""
        if stack.currentIndex() == 0:
            md_text = raw_editor.toPlainText()
            preview.setMarkdown(md_text)
            stack.setCurrentIndex(1)
        else:
            stack.setCurrentIndex(0)

    # -------------------------------------------------------------------------
    # VIEW 4: PROJECTIR TELEMETRY & SCHEMA INSPECTOR
    # -------------------------------------------------------------------------
    def _build_project_ir_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("PROJECT INTERMEDIATE REPRESENTATION (PROJECTIR) AST INSPECTOR")
        header.setStyleSheet("font-size: 13px; font-weight: 800; color: #d4af37; letter-spacing: 0.08em;")
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Outline Tree
        self.ir_tree = QTreeWidget()
        self.ir_tree.setHeaderLabels(["ProjectIR Components"])
        self.ir_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.ir_tree.itemClicked.connect(self._on_ir_tree_item_clicked)
        splitter.addWidget(self.ir_tree)

        # Right: Detail Inspector View
        self.ir_stack = QStackedWidget()

        # View 0: Overview
        self.ir_overview_edit = QTextEdit()
        self.ir_overview_edit.setReadOnly(True)
        self.ir_stack.addWidget(self.ir_overview_edit)

        # View 1: PostgreSQL DDL
        self.ir_ddl_edit = QTextEdit()
        self.ir_ddl_edit.setReadOnly(True)
        self.ir_ddl_edit.setFont(QFont("Consolas", 10))
        self.ir_stack.addWidget(self.ir_ddl_edit)

        # View 2: SLAs / Tables
        self.ir_table_widget = QTableWidget()
        self.ir_stack.addWidget(self.ir_table_widget)

        # View 3: Raw JSON
        self.ir_json_edit = QTextEdit()
        self.ir_json_edit.setReadOnly(True)
        self.ir_json_edit.setFont(QFont("Consolas", 10))
        self.ir_stack.addWidget(self.ir_json_edit)

        splitter.addWidget(self.ir_stack)
        splitter.setSizes([320, 880])
        layout.addWidget(splitter, 1)

        self._populate_empty_ir_tree()
        return container

    def _populate_empty_ir_tree(self):
        self.ir_tree.clear()
        nodes = [
            "📋 Project Overview",
            "👥 Target Personas",
            "🎯 Functional Requirements",
            "⏱️ Non-Functional SLAs",
            "🛡️ STRIDE Threat Matrix",
            "🗄️ PostgreSQL Database DDL",
            "🌐 API Contracts",
            "🔄 Lifecycle & Recovery Matrix",
            "✅ Phased Milestones",
            "{} Raw ProjectIR JSON",
        ]
        for name in nodes:
            item = QTreeWidgetItem(self.ir_tree, [name])
        self.ir_overview_edit.setPlainText("No ProjectIR loaded yet. Deliberate with the Council or load sample artifacts.")

    def _on_ir_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        text = item.text(0)
        if "PostgreSQL" in text:
            self.ir_stack.setCurrentIndex(1)
        elif any(k in text for k in ["SLAs", "STRIDE", "Recovery", "Requirements", "Personas"]):
            self.ir_stack.setCurrentIndex(2)
            self._render_ir_table_view(text)
        elif "Raw ProjectIR" in text:
            self.ir_stack.setCurrentIndex(3)
        else:
            self.ir_stack.setCurrentIndex(0)

    def _render_ir_table_view(self, category: str):
        if not self.project_ir or not isinstance(self.project_ir, dict):
            self.ir_table_widget.setRowCount(1)
            self.ir_table_widget.setColumnCount(1)
            self.ir_table_widget.setHorizontalHeaderLabels(["Notice"])
            self.ir_table_widget.setItem(0, 0, QTableWidgetItem("ProjectIR not yet synthesized."))
            return

        def _field(obj: Any, key: str, default: Any = "") -> Any:
            if isinstance(obj, dict):
                val = obj.get(key, default)
            elif obj is not None:
                val = getattr(obj, key, default)
            else:
                val = default
            return default if val is None else val

        if "SLAs" in category:
            slas = (self.project_ir.get("non_functional_slas") or []) if isinstance(self.project_ir, dict) else []
            self.ir_table_widget.setColumnCount(3)
            self.ir_table_widget.setHorizontalHeaderLabels(["Metric", "Target", "Verification Method"])
            self.ir_table_widget.setRowCount(len(slas))
            for i, sla in enumerate(slas):
                self.ir_table_widget.setItem(i, 0, QTableWidgetItem(str(_field(sla, "metric", "") or "")))
                self.ir_table_widget.setItem(i, 1, QTableWidgetItem(str(_field(sla, "target", "") or "")))
                self.ir_table_widget.setItem(i, 2, QTableWidgetItem(str(_field(sla, "verification_method", "") or "")))
        elif "STRIDE" in category:
            threats = (self.project_ir.get("security_threat_matrix") or []) if isinstance(self.project_ir, dict) else []
            self.ir_table_widget.setColumnCount(3)
            self.ir_table_widget.setHorizontalHeaderLabels(["Category", "Threat Description", "Mitigation"])
            self.ir_table_widget.setRowCount(len(threats))
            for i, t in enumerate(threats):
                self.ir_table_widget.setItem(i, 0, QTableWidgetItem(str(_field(t, "threat_category", "") or "")))
                self.ir_table_widget.setItem(i, 1, QTableWidgetItem(str(_field(t, "threat_description", "") or "")))
                self.ir_table_widget.setItem(i, 2, QTableWidgetItem(str(_field(t, "mitigation", "") or "")))
        elif "Recovery" in category:
            lifecycle = (self.project_ir.get("lifecycle") or {}) if isinstance(self.project_ir, dict) else {}
            recovery = (lifecycle.get("failure_recovery_matrix") or []) if isinstance(lifecycle, dict) else []
            self.ir_table_widget.setColumnCount(3)
            self.ir_table_widget.setHorizontalHeaderLabels(["Component", "Detection SLA", "Recovery Mechanism"])
            self.ir_table_widget.setRowCount(len(recovery))
            for i, r in enumerate(recovery):
                self.ir_table_widget.setItem(i, 0, QTableWidgetItem(str(_field(r, "component", "") or "")))
                self.ir_table_widget.setItem(i, 1, QTableWidgetItem(str(_field(r, "detection_sla", "") or "")))
                self.ir_table_widget.setItem(i, 2, QTableWidgetItem(str(_field(r, "recovery_mechanism", "") or "")))
        elif "Requirements" in category:
            reqs = (self.project_ir.get("requirements") or []) if isinstance(self.project_ir, dict) else []
            self.ir_table_widget.setColumnCount(4)
            self.ir_table_widget.setHorizontalHeaderLabels(["ID", "Priority", "Title", "Acceptance Criteria"])
            self.ir_table_widget.setRowCount(len(reqs))
            for i, rq in enumerate(reqs):
                self.ir_table_widget.setItem(i, 0, QTableWidgetItem(str(_field(rq, "id", "") or "")))
                self.ir_table_widget.setItem(i, 1, QTableWidgetItem(str(_field(rq, "priority", "") or "")))
                self.ir_table_widget.setItem(i, 2, QTableWidgetItem(str(_field(rq, "title", "") or "")))
                raw_criteria = _field(rq, "acceptance_criteria", [])
                if isinstance(raw_criteria, list):
                    criteria = "; ".join(str(c) for c in raw_criteria if c)
                else:
                    criteria = str(raw_criteria or "")
                self.ir_table_widget.setItem(i, 3, QTableWidgetItem(criteria))
        elif "Personas" in category:
            personas = (self.project_ir.get("target_personas") or []) if isinstance(self.project_ir, dict) else []
            self.ir_table_widget.setColumnCount(4)
            self.ir_table_widget.setHorizontalHeaderLabels(["Name", "Role", "Pain Points", "Needs"])
            self.ir_table_widget.setRowCount(len(personas))
            for i, p in enumerate(personas):
                self.ir_table_widget.setItem(i, 0, QTableWidgetItem(str(_field(p, "name", "") or "")))
                self.ir_table_widget.setItem(i, 1, QTableWidgetItem(str(_field(p, "role", "") or "")))
                raw_pains = _field(p, "pain_points", [])
                pains = (
                    "; ".join(str(x) for x in raw_pains if x)
                    if isinstance(raw_pains, list)
                    else str(raw_pains or "")
                )
                raw_needs = _field(p, "needs", [])
                needs = (
                    "; ".join(str(x) for x in raw_needs if x)
                    if isinstance(raw_needs, list)
                    else str(raw_needs or "")
                )
                self.ir_table_widget.setItem(i, 2, QTableWidgetItem(pains))
                self.ir_table_widget.setItem(i, 3, QTableWidgetItem(needs))
        self.ir_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    # -------------------------------------------------------------------------
    # THEME SWITCHER
    # -------------------------------------------------------------------------
    def set_theme(self, theme_name: str):
        """Apply Onyx Black or Vellum Light palette dynamically."""
        theme_name = theme_name.lower()
        self.current_theme = theme_name

        if theme_name == "vellum":
            self.setStyleSheet(VELLUM_STYLESHEET)
            self.theme_btn.setText("🌙 Onyx Black")
            self.visualizer.set_theme("vellum")
            for h in self.highlighters.values():
                h.set_theme("vellum")
            self.status_label.setText("Active Theme: Monolith Vellum Luxury Light Mode")
        else:
            self.setStyleSheet(ONYX_STYLESHEET)
            self.theme_btn.setText("☀️ Vellum Light")
            self.visualizer.set_theme("onyx")
            for h in self.highlighters.values():
                h.set_theme("onyx")
            self.status_label.setText("Active Theme: Monolith Onyx True Black Mode")

    def _toggle_theme(self):
        new_theme = "vellum" if self.current_theme == "onyx" else "onyx"
        self.set_theme(new_theme)

    # -------------------------------------------------------------------------
    # GATEWAY HEALTH & BACKEND SWITCHER
    # -------------------------------------------------------------------------
    def _check_gateway_health(self):
        """Check if local FastAPI backend (http://127.0.0.1:8080) is reachable."""
        try:
            req = urllib.request.Request("http://127.0.0.1:8080/health", headers={"User-Agent": "VoGenFlow-Desktop"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    self.gateway_online = True
                    self.gateway_pill.setText("● GATEWAY ONLINE (8080)")
                    self.gateway_pill.setStyleSheet(
                        "font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 12px; "
                        "background-color: #064e3b; color: #6ee7b7;"
                    )
                    return
        except Exception:
            pass

        self.gateway_online = False
        self.gateway_pill.setText("○ IN-PROCESS ENGINE")
        self.gateway_pill.setStyleSheet(
            "font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 12px; "
            "background-color: #3b2505; color: #fde047;"
        )

    def _on_backend_mode_changed(self, index: int):
        if index == 0:
            self.backend_mode = "http"
            self.status_label.setText("Connected via Live HTTP Gateway (127.0.0.1:8080)")
        else:
            self.backend_mode = "in_process"
            self.status_label.setText("Connected via Local In-Process Council Engine")

    # -------------------------------------------------------------------------
    # AUDIO RECORDING & TRANSCRIPTION HANDLERS
    # -------------------------------------------------------------------------
    def _toggle_recording(self):
        if not self.recorder.is_recording and not self.recorder.is_paused:
            try:
                self.recorder.start()
                self.record_timer.start(100)
                self.visualizer.reset()
                self.record_btn.setText("🛑 Stop Recording")
                self.record_btn.setObjectName("stopRecordBtn")
                self.record_btn.setStyle(self.record_btn.style())
                self.pause_btn.setEnabled(True)
                self.status_label.setText("Recording microphone audio...")
            except Exception as e:
                self.status_label.setText(f"Audio recording unavailable: {e}")
                if os.getenv("QT_QPA_PLATFORM") != "offscreen":
                    QMessageBox.critical(self, "Recording Error", f"Failed to start recording: {e}")
        else:
            self.recorder.stop()
            self.record_timer.stop()
            self.visualizer.reset()
            self.record_btn.setText("🎙️ Start Recording")
            self.record_btn.setObjectName("")
            self.record_btn.setStyle(self.record_btn.style())
            self.pause_btn.setEnabled(False)
            self.pause_btn.setText("⏸️ Pause")

            try:
                saved_path = self.recorder.save_wav()
                self._on_audio_file_selected(saved_path)
                self.status_label.setText("Recording saved. Ready to transcribe.")
            except Exception as e:
                self.status_label.setText(f"No audio recorded: {e}")
                if os.getenv("QT_QPA_PLATFORM") != "offscreen":
                    QMessageBox.warning(self, "Save Error", f"Could not save recorded audio: {e}")

    def _toggle_pause(self):
        if self.recorder.is_paused:
            self.recorder.resume()
            self.pause_btn.setText("⏸️ Pause")
            self.status_label.setText("Recording resumed...")
        else:
            self.recorder.pause()
            self.pause_btn.setText("▶️ Resume")
            self.status_label.setText("Recording paused.")

    def _update_record_clock(self):
        duration = self.recorder.get_duration()
        mins = int(duration // 60)
        secs = duration % 60
        self.record_time_label.setText(f"{mins:02d}:{secs:04.1f}")

    def _on_audio_amplitude(self, level: float):
        self.visualizer.set_level(level)

    def _browse_audio_file(self):
        file_filter = "Audio Files (*.wav *.mp3 *.m4a *.ogg *.flac *.webm *.mp4)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", file_filter)
        if file_path:
            self._on_audio_file_selected(file_path)

    def _on_audio_file_selected(self, file_path: str):
        self.current_audio_file = file_path
        self.selected_file_label.setText(f"File: {Path(file_path).name}")
        self.status_label.setText(f"Loaded {Path(file_path).name}")

    def load_sample_voice_memo(self):
        """Load bundled sample audio voice memo for immediate zero-touch testing."""
        sample_path = Path("data/sample_audio.wav").resolve()
        if not sample_path.exists():
            sample_path = (Path(DOCS_DIR).parent / "data" / "sample_audio.wav").resolve()
        if sample_path.exists():
            self._on_audio_file_selected(str(sample_path))
            self.transcript_edit.setPlainText(
                "Build an enterprise global payments and ledger settlement microservice with PostgreSQL 16, "
                "partitioned audit logs, Redis distributed locking, FastAPI ingress gateway, and real-time WebSockets."
            )
            self.status_label.setText("Loaded bundled sample voice memo & architectural brainstorm.")
        else:
            self.transcript_edit.setPlainText(
                "Build a high-velocity event-driven payment processing platform with partitioned PostgreSQL, "
                "declarative Row-Level Security, Redis locking, and automated failure recovery."
            )
            self.status_label.setText("Pre-filled sample architectural brainstorm.")

    def transcribe_audio(self):
        """Trigger transcription via local Whisper STT or HTTP Gateway."""
        if not self.current_audio_file or not os.path.exists(self.current_audio_file):
            QMessageBox.warning(self, "No Audio File", "Please record audio or select an audio file first.")
            return

        model = self.stt_model_combo.currentText()
        mode = "http" if (self.backend_mode == "http" or (self.backend_mode == "auto" and self.gateway_online)) else "in_process"

        self.transcribe_btn.setEnabled(False)
        self.global_progress.setVisible(True)
        self.status_label.setText(f"Transcribing audio ({model}) via {mode.upper()}...")

        self.active_worker = TranscriptionWorker(self.current_audio_file, model=model, mode=mode)
        self.active_worker.signals.finished.connect(self._on_transcription_success)
        self.active_worker.signals.error.connect(self._on_transcription_error)
        self.active_worker.start()

    def _on_transcription_success(self, result: Any):
        self.transcribe_btn.setEnabled(True)
        self.global_progress.setVisible(False)
        text = result.get("text", "") if isinstance(result, dict) else str(result)
        self.transcript_edit.setPlainText(text)
        lat = result.get("latency_seconds", 0.0) if isinstance(result, dict) else 0.0
        self.status_label.setText(f"Transcription completed in {lat:.2f}s!")

    def _on_transcription_error(self, err_msg: str):
        self.transcribe_btn.setEnabled(True)
        self.global_progress.setVisible(False)
        self.status_label.setText("Transcription error.")
        QMessageBox.critical(self, "Transcription Error", f"Transcription encountered an error:\n{err_msg}")

    def _update_transcript_telemetry(self):
        text = self.transcript_edit.toPlainText().strip()
        words = len(text.split())
        est_sec = words / 2.5  # average conversational speech speed
        self.transcript_stats_label.setText(f"Words: {words} | Estimated Duration: {est_sec:.1f}s")

    def _index_rag_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Codebase Directory to Index for RAG")
        if dir_path:
            try:
                from src.rag_engine import LocalRAGEngine
                rag = LocalRAGEngine()
                count = rag.index_directory(dir_path)
                self.rag_stats_label.setText(f"Indexed {count} files ({len(rag.chunks)} chunks)")
                QMessageBox.information(self, "RAG Indexing", f"Indexed {count} files ({len(rag.chunks)} chunks) successfully!")
            except Exception as e:
                QMessageBox.warning(self, "RAG Error", f"Failed indexing directory: {e}")

    # -------------------------------------------------------------------------
    # COUNCIL DELIBERATION HANDLERS
    # -------------------------------------------------------------------------
    def convene_council(self):
        """Convene the 6-Seat Council to deliberate on the spoken transcript."""
        transcript = self.transcript_edit.toPlainText().strip()
        if not transcript:
            QMessageBox.warning(self, "Empty Transcript", "Please provide a transcript or record audio first.")
            return

        # Switch to Council Chamber View
        self.main_nav_tabs.setCurrentIndex(1)
        self.chamber_status_label.setText("COUNCIL STATUS: CONVENED // DELIBERATION IN PROGRESS")
        self.chamber_progress_bar.setValue(10)
        self.chamber_log_edit.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Deliberation initiated.")

        # Reset agent cards to thinking state
        for key, card in self.agent_cards.items():
            card.set_status("DELIBERATING", "Synthesizing domain specifications...")

        mode = "http" if (self.backend_mode == "http" or (self.backend_mode == "auto" and self.gateway_online)) else "in_process"
        preset_idx = self.preset_combo.currentIndex()
        preset_map = {0: "standard", 1: "security", 2: "lean"}
        preset_val = preset_map.get(preset_idx, "standard")

        self.convene_btn.setEnabled(False)
        self.global_progress.setVisible(True)

        self.active_worker = CouncilDeliberationWorker(
            transcript=transcript,
            preset=preset_val,
            mode=mode
        )
        self.active_worker.signals.progress.connect(self._on_council_progress)
        self.active_worker.signals.finished.connect(self._on_council_finished)
        self.active_worker.signals.error.connect(self._on_council_error)
        self.active_worker.start()

    def _on_council_progress(self, msg: str, data: Any):
        self.chamber_log_edit.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
        if isinstance(data, dict):
            role = data.get("role")
            if role in self.agent_cards:
                self.agent_cards[role].set_status("DELIBERATING", msg)

    def _on_council_finished(self, result: Dict[str, Any]):
        self.convene_btn.setEnabled(True)
        self.global_progress.setVisible(False)
        self.chamber_progress_bar.setValue(100)
        self.chamber_status_label.setText("COUNCIL STATUS: DELIBERATION COMPLETE // CONSENSUS REACHED")

        artifacts = result.get("artifacts", {})
        dossier = result.get("seat_dossier", {})
        project_ir = result.get("project_ir")

        self.load_mock_artifacts(artifacts, project_ir=project_ir, seat_dossier=dossier)
        self.chamber_log_edit.append(
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Deliberation complete in {result.get('duration_seconds', 0.0):.2f}s."
        )

    def _on_council_error(self, err_msg: str):
        self.convene_btn.setEnabled(True)
        self.global_progress.setVisible(False)
        self.chamber_status_label.setText("COUNCIL STATUS: ERROR DURING DELIBERATION")
        self.chamber_log_edit.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERROR: {err_msg}")
        QMessageBox.critical(self, "Council Deliberation Error", f"Deliberation encountered an error:\n{err_msg}")

    # -------------------------------------------------------------------------
    # ARTIFACT & PROJECT IR LOADING
    # -------------------------------------------------------------------------
    def load_mock_artifacts(
        self,
        artifacts: Dict[str, str],
        project_ir: Optional[Dict[str, Any]] = None,
        seat_dossier: Optional[Dict[str, Any]] = None
    ):
        """Populate Specification Studio, ProjectIR pane, and Agent Dossiers."""
        self.artifacts = artifacts
        self.project_ir = project_ir
        if seat_dossier:
            self.seat_dossier = seat_dossier

        # 1. Update Specification Studio Tabs
        for file_key, raw_editor in self.spec_editors.items():
            content = (
                artifacts.get(file_key)
                or artifacts.get(file_key.lower())
                or artifacts.get(file_key.capitalize())
                or ""
            )
            # Handle design.md vs design_proposal.md
            if not content and "design" in file_key.lower():
                content = artifacts.get("design_proposal.md", "")
            raw_editor.setPlainText(content)

            # Update preview if active
            if file_key in self.spec_previews:
                self.spec_previews[file_key].setMarkdown(content)

        # 2. Update Council Agent Cards
        agent_doc_mapping = {
            "pm_agent": "PRD.md",
            "architect_agent": "Architecture.md",
            "ui_agent": "design.md",
            "systems_agent": "Flow.md",
            "agile_agent": "tasks.md",
            "diff_agent": "master_execution_bundle.md",
        }
        for role_key, card in self.agent_cards.items():
            doc_key = agent_doc_mapping.get(role_key, "")
            content = artifacts.get(doc_key, "")
            tokens = len(content.split()) if content else 0
            thoughts = ""
            if seat_dossier:
                # seat_dossier keys: strategist, architect, curator, etc.
                for d_info in seat_dossier.values():
                    if isinstance(d_info, dict) and d_info.get("artifact_key", "").lower() == doc_key.lower():
                        thoughts = d_info.get("thoughts", "")
                        tokens = d_info.get("tokens", tokens)
            if not thoughts and content:
                thoughts = content[:280] + "..."
            card.set_status("COMPLETED", tokens=tokens, latency=1.2, thoughts=thoughts)

        # 3. Update ProjectIR Inspector
        if project_ir and isinstance(project_ir, dict):
            self.ir_overview_edit.setPlainText(
                f"PROJECT: {project_ir.get('project_name') or 'VoGenFlow Project'}\n"
                f"TAGLINE: {project_ir.get('tagline') or ''}\n\n"
                f"EXECUTIVE SUMMARY:\n{project_ir.get('executive_summary') or ''}"
            )
            arch = (project_ir.get("architecture") or {}) if isinstance(project_ir, dict) else {}
            ddl = (arch.get("database_ddl") or "") if isinstance(arch, dict) else ""
            self.ir_ddl_edit.setPlainText(ddl)
            self.ir_json_edit.setPlainText(json.dumps(project_ir, indent=2))
        elif artifacts.get("Architecture.md"):
            arch_text = artifacts.get("Architecture.md", "")
            self.ir_ddl_edit.setPlainText(arch_text)
            self.ir_overview_edit.setPlainText(artifacts.get("PRD.md", ""))

    # -------------------------------------------------------------------------
    # CLIENT-SIDE WORD (.DOCX) EXPORT HANDLER
    # -------------------------------------------------------------------------
    def export_to_docx(self, target_path: Optional[str] = None) -> Optional[str]:
        """Bundle all 5 core specifications into a professional, clean .docx document via python-docx."""
        # Gather specifications from current editors
        current_docs = {}
        for key, editor in self.spec_editors.items():
            text = editor.toPlainText().strip()
            if text:
                current_docs[key] = text

        # If editors are empty, check cached artifacts
        if not current_docs and self.artifacts:
            current_docs = self.artifacts

        if not current_docs:
            if not target_path:
                QMessageBox.warning(self, "No Specifications", "No specifications available to export. Please deliberate with Council first.")
            return None

        # Determine target file destination
        if not target_path:
            default_out = str((Path(OUTPUT_DIR) / "VoGenFlow_Master_Specification.docx").resolve())
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export All Specifications to Word (.docx)",
                default_out,
                "Word Document (*.docx)"
            )
            if not save_path:
                return None
        else:
            save_path = target_path

        try:
            proj_name = "VoGenFlow Industrial Architecture Specification"
            if self.project_ir and self.project_ir.get("project_name"):
                proj_name = self.project_ir.get("project_name")

            saved_file = ExportService.export_to_docx(
                documents=current_docs,
                output_path=save_path,
                project_name=proj_name,
                preset_name=self.preset_combo.currentText()
            )
            self.status_label.setText(f"Exported .docx to: {Path(saved_file).name}")
            if not target_path:
                QMessageBox.information(
                    self,
                    "Word Export Successful",
                    f"Successfully generated clean Word (.docx) document bundling all 5 specifications:\n\n{saved_file}"
                )
            return saved_file
        except Exception as e:
            logger.error("Word export failed: %s", str(e))
            if not target_path:
                QMessageBox.critical(self, "Word Export Error", f"Failed to generate .docx document:\n{e}")
            raise

    def _export_to_directory(self):
        docs_to_export = {}
        for filename, view in self.spec_editors.items():
            content = view.toPlainText().strip()
            if content:
                docs_to_export[filename] = content

        if not docs_to_export:
            QMessageBox.warning(self, "No Content", "No generated documents to export.")
            return

        target_dir = QFileDialog.getExistingDirectory(self, "Select Target Folder")
        if target_dir:
            saved = ExportService.export_documents(docs_to_export, target_dir)
            QMessageBox.information(self, "Export Complete", f"Exported {len(saved)} blueprint documents to:\n{target_dir}")

    def _save_single_file(self, filename: str, content: str):
        if not content.strip():
            QMessageBox.warning(self, "Empty File", "Document has no content to save.")
            return
        save_path, _ = QFileDialog.getSaveFileName(self, f"Save {filename}", filename, "Markdown (*.md);;All Files (*)")
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Saved", f"Saved to {save_path}")

    def _copy_to_clipboard(self, text: str):
        if text.strip():
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_label.setText("Copied document content to clipboard.")

    # -------------------------------------------------------------------------
    # API KEYS & SETTINGS
    # -------------------------------------------------------------------------
    def _prompt_api_key(self):
        from src.config import GROQ_API_KEY
        key, ok = QInputDialog.getText(
            self,
            "Groq API Key Configuration",
            "Enter your Groq API Key (from console.groq.com):",
            QLineEdit.EchoMode.Password,
            GROQ_API_KEY,
        )
        if ok and key.strip():
            from src.stt_service import STTService
            stt = STTService()
            stt.set_api_key(key.strip())
            self.status_label.setText("Groq API Key configured.")


def run_gui():
    """Launch the modernized PyQt6 application with Onyx Black luxury aesthetics."""
    app = QApplication(sys.argv)
    window = MainWindow(default_theme="onyx")
    window.show()
    sys.exit(app.exec())
