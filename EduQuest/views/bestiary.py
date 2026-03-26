from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QProgressBar, QApplication,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import BioCard


class _GenerateThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, bio_object: str):
        super().__init__()
        self.bio_object = bio_object

    def run(self):
        try:
            from services.gemini_service import generate_bio_card
            result = generate_bio_card(self.bio_object)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))


class BestiaryView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _GenerateThread | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("🧬  Бестиарий — Bio-Edition")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.object_input = QLineEdit()
        self.object_input.setPlaceholderText(
            "Введите био-объект: Митохондрия, ВИЧ, Рибосома, E.coli…"
        )
        self.object_input.setObjectName("inputField")

        self.gen_btn = QPushButton("🧬 Создать карточку")
        self.gen_btn.setObjectName("primaryButton")
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_btn.clicked.connect(self._on_generate)

        row.addWidget(self.object_input, 3)
        row.addWidget(self.gen_btn)
        root.addLayout(row)

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
        bio_object = self.object_input.text().strip()
        if not bio_object:
            self.status_label.setText("⚠ Введите название био-объекта")
            return
        self.gen_btn.setEnabled(False)
        self.status_label.setText("⏳ Сканирование микромира…")
        self._clear()
        self._thread = _GenerateThread(bio_object)
        self._thread.finished.connect(self._on_result)
        self._thread.start()

    def _on_result(self, result):
        self.gen_btn.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ {result}")
            return
        self.status_label.setText("✅ Карточка создана!")
        self._render(result)

    def _clear(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render(self, b: BioCard):
        # Header card
        header = QFrame()
        header.setObjectName("accentCard")
        hl = QVBoxLayout(header)
        name_text = f"🧬 {b.name_ru}"
        if b.name_latin:
            name_text += f"  ({b.name_latin})"
        hl.addWidget(self._label(name_text, "cardTitle"))
        hl.addWidget(self._label(f"📂 {b.classification}", "cardBody"))
        hl.addWidget(self._label(b.description, "cardBody"))
        self.result_layout.addWidget(header)

        # RPG card with HP bar
        rpg_frame = QFrame()
        rpg_frame.setObjectName("card")
        rl = QVBoxLayout(rpg_frame)
        rl.addWidget(self._label(f"⚔ Тип: {b.rpg_card.type}", "cardTitle"))

        hp_row = QHBoxLayout()
        hp_lbl = QLabel("❤ HP")
        hp_lbl.setObjectName("cardBody")
        hp_lbl.setFixedWidth(50)
        hp_row.addWidget(hp_lbl)
        hp_bar = QProgressBar()
        hp_bar.setObjectName("hpBar")
        hp_bar.setMaximum(100)
        hp_bar.setValue(b.rpg_card.hp)
        hp_bar.setFormat(f"{b.rpg_card.hp} / 100")
        hp_bar.setTextVisible(True)
        hp_bar.setFixedHeight(28)
        hp_row.addWidget(hp_bar)
        rl.addLayout(hp_row)

        self.result_layout.addWidget(rpg_frame)

        # Abilities
        for ab in b.rpg_card.abilities:
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.addWidget(self._label(f"✨ {ab.name}", "cardTitle"))
            cl.addWidget(self._label(f"🔬 Биофункция: {ab.bio_function}", "cardBody"))
            cl.addWidget(self._label(f"🎮 Эффект: {ab.rpg_effect}", "cardBody"))
            self.result_layout.addWidget(card)

        # Weaknesses
        if b.rpg_card.weaknesses:
            weak_frame = QFrame()
            weak_frame.setObjectName("accentCard")
            wl = QVBoxLayout(weak_frame)
            wl.addWidget(self._label("💀 Уязвимости", "cardTitle"))
            for w in b.rpg_card.weaknesses:
                wl.addWidget(self._label(f"⚡ {w.agent} → {w.effect}", "cardBody"))
            self.result_layout.addWidget(weak_frame)

        # Image prompt (copyable)
        prompt_frame = QFrame()
        prompt_frame.setObjectName("card")
        pl = QVBoxLayout(prompt_frame)
        pl.addWidget(self._label("🎨 AI Image Prompt (Dark Fantasy Bio-Punk)", "cardTitle"))
        prompt_label = QLabel(b.image_generation_prompt)
        prompt_label.setObjectName("cardBody")
        prompt_label.setWordWrap(True)
        prompt_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        pl.addWidget(prompt_label)

        copy_btn = QPushButton("📋 Скопировать промпт")
        copy_btn.setObjectName("primaryButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setFixedWidth(220)
        copy_btn.clicked.connect(lambda: self._copy(b.image_generation_prompt))
        pl.addWidget(copy_btn)
        self.result_layout.addWidget(prompt_frame)

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
