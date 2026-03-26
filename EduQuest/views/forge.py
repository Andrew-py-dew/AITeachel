from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFrame, QScrollArea, QApplication,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import ForgeArtifact


class _GenerateThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, request: str, topic: str):
        super().__init__()
        self.request = request
        self.topic = topic

    def run(self):
        try:
            from services.gemini_service import generate_forge_artifact
            result = generate_forge_artifact(self.request, self.topic)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))


class ForgeView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _GenerateThread | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("🔬  Кузница знаний")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Тема урока")
        self.topic_input.setObjectName("inputField")
        row.addWidget(self.topic_input)
        root.addLayout(row)

        self.request_input = QTextEdit()
        self.request_input.setPlaceholderText(
            "Опишите какое наглядное пособие нужно, например: "
            "«Схема круговорота воды в природе» или «Строение клетки»…"
        )
        self.request_input.setObjectName("inputField")
        self.request_input.setMaximumHeight(100)
        root.addWidget(self.request_input)

        self.gen_btn = QPushButton("🔨 Выковать артефакт")
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
        topic = self.topic_input.text().strip()
        request = self.request_input.toPlainText().strip()
        if not topic or not request:
            self.status_label.setText("⚠ Заполните тему и описание")
            return
        self.gen_btn.setEnabled(False)
        self.status_label.setText("⏳ Кузнец работает над артефактом…")
        self._clear()
        self._thread = _GenerateThread(request, topic)
        self._thread.finished.connect(self._on_result)
        self._thread.start()

    def _on_result(self, result):
        self.gen_btn.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ {result}")
            return
        self.status_label.setText("✅ Артефакт выкован!")
        self._render(result)

    def _clear(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render(self, a: ForgeArtifact):
        # name
        card = QFrame()
        card.setObjectName("accentCard")
        cl = QVBoxLayout(card)
        cl.addWidget(self._label(f"🗡 {a.artifact_name}", "cardTitle"))
        self.result_layout.addWidget(card)

        # drawing guide
        card2 = QFrame()
        card2.setObjectName("card")
        cl2 = QVBoxLayout(card2)
        cl2.addWidget(self._label("🖍 Инструкция для доски", "cardTitle"))
        cl2.addWidget(self._label(a.drawing_guide, "cardBody"))
        self.result_layout.addWidget(card2)

        # AI prompt (copyable)
        card3 = QFrame()
        card3.setObjectName("card")
        cl3 = QVBoxLayout(card3)
        cl3.addWidget(self._label("🤖 AI-промпт для генерации изображения", "cardTitle"))
        prompt_label = QLabel(a.ai_image_prompt)
        prompt_label.setObjectName("cardBody")
        prompt_label.setWordWrap(True)
        prompt_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        cl3.addWidget(prompt_label)

        copy_btn = QPushButton("📋 Скопировать промпт")
        copy_btn.setObjectName("primaryButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setFixedWidth(220)
        copy_btn.clicked.connect(lambda: self._copy(a.ai_image_prompt))
        cl3.addWidget(copy_btn)
        self.result_layout.addWidget(card3)

        # didactic value
        card4 = QFrame()
        card4.setObjectName("accentCard")
        cl4 = QVBoxLayout(card4)
        cl4.addWidget(self._label("📚 Дидактическая ценность", "cardTitle"))
        cl4.addWidget(self._label(a.didactic_value, "cardBody"))
        self.result_layout.addWidget(card4)

    def _copy(self, text: str):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
            self.status_label.setText("✅ Промпт скопирован в буфер обмена!")

    def _label(self, text: str, obj_name: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj_name)
        l.setWordWrap(True)
        return l
