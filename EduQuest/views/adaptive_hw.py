from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import AdaptiveHomework


class _GenerateThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, name: str, topic: str, history: str):
        super().__init__()
        self.name = name
        self.topic = topic
        self.history = history

    def run(self):
        try:
            from services.gemini_service import generate_homework
            result = generate_homework(self.name, self.topic, self.history)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))


class AdaptiveHWView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _GenerateThread | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("📊  Адаптивное ДЗ")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # inputs
        row = QHBoxLayout()
        row.setSpacing(12)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя ученика")
        self.name_input.setObjectName("inputField")
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Тема")
        self.topic_input.setObjectName("inputField")
        row.addWidget(self.name_input)
        row.addWidget(self.topic_input)
        root.addLayout(row)

        self.history_input = QTextEdit()
        self.history_input.setPlaceholderText("История оценок и ошибок ученика…")
        self.history_input.setObjectName("inputField")
        self.history_input.setMaximumHeight(100)
        root.addWidget(self.history_input)

        self.gen_btn = QPushButton("⚡ Сгенерировать ДЗ")
        self.gen_btn.setObjectName("primaryButton")
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_btn.clicked.connect(self._on_generate)
        root.addWidget(self.gen_btn)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        root.addWidget(self.status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("resultScroll")
        self.result_container = QWidget()
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.result_layout.setSpacing(12)
        scroll.setWidget(self.result_container)
        root.addWidget(scroll)

    def _on_generate(self):
        name = self.name_input.text().strip()
        topic = self.topic_input.text().strip()
        history = self.history_input.toPlainText().strip()
        if not name or not topic:
            self.status_label.setText("⚠ Заполните имя и тему")
            return
        self.gen_btn.setEnabled(False)
        self.status_label.setText("⏳ Генерация…")
        self._clear()
        self._thread = _GenerateThread(name, topic, history or "Нет данных")
        self._thread.finished.connect(self._on_result)
        self._thread.start()

    def _on_result(self, result):
        self.gen_btn.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ {result}")
            return
        self.status_label.setText("✅ Готово!")
        self._render(result)

    def _clear(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render(self, hw: AdaptiveHomework):
        # analysis card
        card = QFrame()
        card.setObjectName("accentCard")
        cl = QVBoxLayout(card)
        cl.addWidget(self._label(f"📊 Анализ для {hw.student_name}", "cardTitle"))
        cl.addWidget(self._label(hw.analysis, "cardBody"))
        self.result_layout.addWidget(card)

        for t in hw.tasks:
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            diff_colors = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
            icon = diff_colors.get(t.difficulty, "⚪")
            cl.addWidget(self._label(f"{icon} Задание {t.task_number} [{t.difficulty}]", "cardTitle"))
            cl.addWidget(self._label(t.text, "cardBody"))
            cl.addWidget(self._label(f"💡 {t.hint}", "statusLabel"))
            self.result_layout.addWidget(card)

    def _label(self, text: str, obj_name: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj_name)
        l.setWordWrap(True)
        return l
