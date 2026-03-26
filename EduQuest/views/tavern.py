from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QProgressBar, QScrollArea,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import TavernAnalysis


class _GenerateThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, feedback: str):
        super().__init__()
        self.feedback = feedback

    def run(self):
        try:
            from services.gemini_service import generate_tavern_analysis
            result = generate_tavern_analysis(self.feedback)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))


class TavernView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _GenerateThread | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("📋  Таверна — Анализ класса")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        self.feedback_input = QTextEdit()
        self.feedback_input.setPlaceholderText(
            "Вставьте отзывы учеников, заметки об уроке, наблюдения…"
        )
        self.feedback_input.setObjectName("inputField")
        self.feedback_input.setMaximumHeight(120)
        root.addWidget(self.feedback_input)

        self.gen_btn = QPushButton("🍺 Проанализировать")
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
        text = self.feedback_input.toPlainText().strip()
        if not text:
            self.status_label.setText("⚠ Введите отзывы или заметки")
            return
        self.gen_btn.setEnabled(False)
        self.status_label.setText("⏳ Мастер Таверны изучает обстановку…")
        self._clear()
        self._thread = _GenerateThread(text)
        self._thread.finished.connect(self._on_result)
        self._thread.start()

    def _on_result(self, result):
        self.gen_btn.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ {result}")
            return
        self.status_label.setText("✅ Анализ готов!")
        self._render(result)

    def _clear(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render(self, t: TavernAnalysis):
        # status card
        card = QFrame()
        card.setObjectName("accentCard")
        cl = QVBoxLayout(card)
        cl.addWidget(self._label(f"🛡 {t.status_name}", "cardTitle"))
        cl.addWidget(self._label(t.analysis, "cardBody"))
        self.result_layout.addWidget(card)

        # stats card with bars
        stats_card = QFrame()
        stats_card.setObjectName("card")
        sl = QVBoxLayout(stats_card)
        sl.addWidget(self._label("📊 Статы класса", "cardTitle"))

        stat_items = [
            ("✨ Магия (Креативность)", t.stats.magic),
            ("💪 Сила (Логика)", t.stats.strength),
            ("🏃 Ловкость (Скорость)", t.stats.agility),
            ("🛡 Выносливость (Внимание)", t.stats.endurance),
        ]
        for name, value in stat_items:
            row = QHBoxLayout()
            lbl = QLabel(name)
            lbl.setObjectName("cardBody")
            lbl.setFixedWidth(250)
            row.addWidget(lbl)

            bar = QProgressBar()
            bar.setObjectName("statBar")
            bar.setMaximum(100)
            bar.setValue(value)
            bar.setFormat(f"{value}/100")
            bar.setTextVisible(True)
            bar.setFixedHeight(22)
            row.addWidget(bar)
            sl.addLayout(row)

        self.result_layout.addWidget(stats_card)

        # recommendation
        rec_card = QFrame()
        rec_card.setObjectName("accentCard")
        rl = QVBoxLayout(rec_card)
        rl.addWidget(self._label("📜 Рекомендация Мастера Таверны", "cardTitle"))
        rl.addWidget(self._label(t.recommendation, "cardBody"))
        self.result_layout.addWidget(rec_card)

    def _label(self, text: str, obj_name: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj_name)
        l.setWordWrap(True)
        return l
