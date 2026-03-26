from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import ArenaRound


class _GenerateThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, topic: str):
        super().__init__()
        self.topic = topic

    def run(self):
        try:
            from services.gemini_service import generate_arena_round
            result = generate_arena_round(self.topic)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))


class ArenaView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _GenerateThread | None = None
        self._total_points = 0
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("🏆  Арена классов")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Тема баттла")
        self.topic_input.setObjectName("inputField")
        self.gen_btn = QPushButton("⚡ Сгенерировать раунд")
        self.gen_btn.setObjectName("primaryButton")
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_btn.clicked.connect(self._on_generate)
        row.addWidget(self.topic_input, 3)
        row.addWidget(self.gen_btn)
        root.addLayout(row)

        self.score_label = QLabel("Очки: 0")
        self.score_label.setObjectName("pageTitle")
        root.addWidget(self.score_label)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        root.addWidget(self.status_label)

        self.round_frame = QFrame()
        self.round_frame.setObjectName("card")
        self.round_frame.setVisible(False)
        rl = QVBoxLayout(self.round_frame)
        self.type_label = QLabel()
        self.type_label.setObjectName("cardTitle")
        self.question_label = QLabel()
        self.question_label.setObjectName("cardBody")
        self.question_label.setWordWrap(True)
        self.meta_label = QLabel()
        self.meta_label.setObjectName("statusLabel")
        rl.addWidget(self.type_label)
        rl.addWidget(self.question_label)
        rl.addWidget(self.meta_label)
        root.addWidget(self.round_frame)
        root.addStretch()

    def _on_generate(self):
        topic = self.topic_input.text().strip()
        if not topic:
            self.status_label.setText("⚠ Введите тему")
            return
        self.gen_btn.setEnabled(False)
        self.status_label.setText("⏳ Генерация раунда…")
        self._thread = _GenerateThread(topic)
        self._thread.finished.connect(self._on_result)
        self._thread.start()

    def _on_result(self, result):
        self.gen_btn.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ {result}")
            return
        self.status_label.setText("✅ Раунд готов!")
        r: ArenaRound = result
        self._total_points += r.points
        self.score_label.setText(f"Очки: {self._total_points}")
        self.type_label.setText(f"🎯 {r.round_type}")
        self.question_label.setText(r.question)
        self.meta_label.setText(f"💎 {r.points} очков  ·  ⏱ {r.time_limit_seconds} сек")
        self.round_frame.setVisible(True)
