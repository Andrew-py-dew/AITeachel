from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QTextEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import QuestScenario


class _GenerateThread(QThread):
    finished = pyqtSignal(object)  # QuestScenario or str (error)

    def __init__(self, topic: str, grade: str):
        super().__init__()
        self.topic = topic
        self.grade = grade

    def run(self):
        try:
            from services.gemini_service import generate_quest
            result = generate_quest(self.topic, self.grade)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))


class QuestGeneratorView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _GenerateThread | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("📝  Генератор квестов")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # --- inputs ---
        form = QHBoxLayout()
        form.setSpacing(12)

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Тема урока, например: Дроби")
        self.topic_input.setObjectName("inputField")

        self.grade_input = QLineEdit()
        self.grade_input.setPlaceholderText("Класс, например: 7")
        self.grade_input.setFixedWidth(120)
        self.grade_input.setObjectName("inputField")

        self.gen_btn = QPushButton("⚡ Сгенерировать")
        self.gen_btn.setObjectName("primaryButton")
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_btn.clicked.connect(self._on_generate)

        form.addWidget(self.topic_input, 3)
        form.addWidget(self.grade_input, 1)
        form.addWidget(self.gen_btn)
        root.addLayout(form)

        # --- result area (scrollable) ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("resultScroll")
        self.result_container = QWidget()
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.result_layout.setSpacing(12)
        scroll.setWidget(self.result_container)
        root.addWidget(scroll)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        root.addWidget(self.status_label)

    # --- logic ---

    def _on_generate(self):
        topic = self.topic_input.text().strip()
        grade = self.grade_input.text().strip()
        if not topic or not grade:
            self.status_label.setText("⚠ Заполните тему и класс")
            return
        self.gen_btn.setEnabled(False)
        self.status_label.setText("⏳ Генерация квеста…")
        self._clear_results()

        self._thread = _GenerateThread(topic, grade)
        self._thread.finished.connect(self._on_result)
        self._thread.start()

    def _on_result(self, result):
        self.gen_btn.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ Ошибка: {result}")
            return
        self.status_label.setText("✅ Квест готов!")
        self._render_quest(result)

    def _clear_results(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render_quest(self, q: QuestScenario):
        # header card
        self._add_card(
            f"🏰 {q.quest_name}",
            f"<b>Сеттинг:</b> {q.setting}",
        )
        # stages
        for s in q.stages:
            self._add_card(
                f"📍 Этап {s.stage_number}: {s.title}",
                f"{s.description}<br><i>⏱ {s.duration_minutes} мин</i>",
            )
        # boss
        self._add_card(
            f"🐉 Финальный босс: {q.final_boss.name}",
            f"{q.final_boss.description}<br><b>Условие победы:</b> {q.final_boss.defeat_condition}",
            accent=True,
        )

    def _add_card(self, title: str, body: str, accent: bool = False):
        card = QFrame()
        card.setObjectName("accentCard" if accent else "card")
        layout = QVBoxLayout(card)
        t = QLabel(title)
        t.setObjectName("cardTitle")
        t.setWordWrap(True)
        b = QLabel(body)
        b.setObjectName("cardBody")
        b.setWordWrap(True)
        b.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(t)
        layout.addWidget(b)
        self.result_layout.addWidget(card)
