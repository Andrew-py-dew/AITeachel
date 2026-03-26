from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QScrollArea, QApplication,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import PortalMessage


class _PortalThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, figure: str, history: str, message: str):
        super().__init__()
        self.figure = figure
        self.history = history
        self.message = message

    def run(self):
        try:
            from services.gemini_service import generate_portal_reply
            result = generate_portal_reply(self.figure, self.history, self.message)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))


class PortalView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _PortalThread | None = None
        self._figure: str = ""
        self._conversation_history: str = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("🕰  Портал Времени — Чат с исторической личностью")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # --- Figure selection ---
        figure_row = QHBoxLayout()
        self.figure_input = QLineEdit()
        self.figure_input.setPlaceholderText("Имя исторической личности (напр. Исаак Ньютон)")
        self.figure_input.setObjectName("inputField")
        figure_row.addWidget(self.figure_input)

        self.portal_btn = QPushButton("🌀 Открыть портал")
        self.portal_btn.setObjectName("primaryButton")
        self.portal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.portal_btn.clicked.connect(self._open_portal)
        figure_row.addWidget(self.portal_btn)
        root.addLayout(figure_row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        root.addWidget(self.status_label)

        # --- Chat area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("resultScroll")
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)
        scroll.setWidget(self.chat_container)
        root.addWidget(scroll, 1)

        # --- Message input ---
        msg_row = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Напишите сообщение…")
        self.msg_input.setObjectName("inputField")
        self.msg_input.setEnabled(False)
        self.msg_input.returnPressed.connect(self._send_message)
        msg_row.addWidget(self.msg_input)

        self.send_btn = QPushButton("📨 Отправить")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self._send_message)
        msg_row.addWidget(self.send_btn)
        root.addLayout(msg_row)

    def _open_portal(self):
        name = self.figure_input.text().strip()
        if not name:
            self.status_label.setText("⚠ Введите имя исторической личности")
            return
        self._figure = name
        self._conversation_history = ""
        self._clear_chat()
        self.status_label.setText(f"🌀 Портал открыт! Вы говорите с: {name}")
        self.msg_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.msg_input.setFocus()

    def _send_message(self):
        text = self.msg_input.text().strip()
        if not text or not self._figure:
            return
        self.msg_input.clear()
        self._add_student_bubble(text)
        self._conversation_history += f"Ученик: {text}\n"
        self.send_btn.setEnabled(False)
        self.msg_input.setEnabled(False)
        self.status_label.setText("⏳ Персонаж думает…")
        self._thread = _PortalThread(self._figure, self._conversation_history, text)
        self._thread.finished.connect(self._on_reply)
        self._thread.start()

    def _on_reply(self, result):
        self.send_btn.setEnabled(True)
        self.msg_input.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ {result}")
            return
        self.status_label.setText(f"🌀 Портал активен — {self._figure}")
        self._add_figure_bubble(result)
        self._conversation_history += f"{self._figure}: {result.dialogue}\n"
        self.msg_input.setFocus()

    def _add_student_bubble(self, text: str):
        bubble = QFrame()
        bubble.setObjectName("card")
        bl = QVBoxLayout(bubble)
        bl.setContentsMargins(14, 10, 14, 10)
        lbl = QLabel(f"🧑‍🎓 Ученик: {text}")
        lbl.setObjectName("cardBody")
        lbl.setWordWrap(True)
        bl.addWidget(lbl)
        self.chat_layout.addWidget(bubble)

    def _add_figure_bubble(self, msg: PortalMessage):
        bubble = QFrame()
        if msg.is_duel_active:
            bubble.setObjectName("duelCard")
        else:
            bubble.setObjectName("accentCard")
        bl = QVBoxLayout(bubble)
        bl.setContentsMargins(14, 10, 14, 10)

        # Emotion badge + dialogue
        header = QLabel(f"🎭 {msg.emotion}")
        header.setObjectName("cardTitle")
        bl.addWidget(header)

        dialogue = QLabel(f"🗣 {self._figure}: {msg.dialogue}")
        dialogue.setObjectName("cardBody")
        dialogue.setWordWrap(True)
        bl.addWidget(dialogue)

        # Fact-check (small, for teacher)
        fact = QLabel(f"📋 Fact-check: {msg.historical_fact_check}")
        fact.setObjectName("statusLabel")
        fact.setWordWrap(True)
        bl.addWidget(fact)

        # Duel indicator
        if msg.is_duel_active:
            duel_lbl = QLabel("⚔️ ДУЭЛЬ АКТИВНА!")
            duel_lbl.setStyleSheet("color: #EF4444; font-weight: 800; font-size: 14px;")
            bl.addWidget(duel_lbl)

        # Artifact gift
        if msg.artifact_gift:
            gift_card = QFrame()
            gift_card.setObjectName("accentCard")
            gl = QVBoxLayout(gift_card)
            gl.addWidget(self._label(f"🎁 Артефакт: {msg.artifact_gift.artifact_name}", "cardTitle"))
            gl.addWidget(self._label(f"📖 {msg.artifact_gift.didactic_meaning}", "cardBody"))

            copy_btn = QPushButton(f"📋 Копировать image prompt")
            copy_btn.setObjectName("primaryButton")
            copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            prompt_text = msg.artifact_gift.image_prompt
            copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(prompt_text))
            gl.addWidget(copy_btn)
            bl.addWidget(gift_card)

        self.chat_layout.addWidget(bubble)

    def _clear_chat(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _label(self, text: str, obj_name: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj_name)
        l.setWordWrap(True)
        return l
