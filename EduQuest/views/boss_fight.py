from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QProgressBar, QScrollArea, QFrame, QTextEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import BossFight as BossFightModel


class _GenerateThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, topic: str, difficulty: str):
        super().__init__()
        self.topic = topic
        self.difficulty = difficulty

    def run(self):
        try:
            from services.gemini_service import generate_boss_fight
            result = generate_boss_fight(self.topic, self.difficulty)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))


class BossFightView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _GenerateThread | None = None
        self._boss: BossFightModel | None = None
        self._current_task = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("🧪  Босс-Контроша")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # --- inputs ---
        form = QHBoxLayout()
        form.setSpacing(12)

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Тема контрольной")
        self.topic_input.setObjectName("inputField")

        self.diff_combo = QComboBox()
        self.diff_combo.setObjectName("inputField")
        self.diff_combo.addItems(["Easy", "Medium", "Hard"])
        self.diff_combo.setFixedWidth(130)

        self.gen_btn = QPushButton("⚡ Призвать босса")
        self.gen_btn.setObjectName("primaryButton")
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_btn.clicked.connect(self._on_generate)

        form.addWidget(self.topic_input, 3)
        form.addWidget(self.diff_combo)
        form.addWidget(self.gen_btn)
        root.addLayout(form)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        root.addWidget(self.status_label)

        # --- boss display (hidden until generated) ---
        self.boss_frame = QFrame()
        self.boss_frame.setObjectName("accentCard")
        self.boss_frame.setVisible(False)
        boss_layout = QVBoxLayout(self.boss_frame)

        self.boss_name_label = QLabel()
        self.boss_name_label.setObjectName("cardTitle")
        boss_layout.addWidget(self.boss_name_label)

        self.hp_bar = QProgressBar()
        self.hp_bar.setObjectName("hpBar")
        self.hp_bar.setTextVisible(True)
        self.hp_bar.setFormat("HP: %v / %m")
        boss_layout.addWidget(self.hp_bar)

        self.taunt_label = QLabel()
        self.taunt_label.setObjectName("cardBody")
        self.taunt_label.setWordWrap(True)
        boss_layout.addWidget(self.taunt_label)

        root.addWidget(self.boss_frame)

        # --- task area ---
        self.task_frame = QFrame()
        self.task_frame.setObjectName("card")
        self.task_frame.setVisible(False)
        task_layout = QVBoxLayout(self.task_frame)

        self.task_label = QLabel()
        self.task_label.setObjectName("cardBody")
        self.task_label.setWordWrap(True)
        task_layout.addWidget(self.task_label)

        self.hint_label = QLabel()
        self.hint_label.setObjectName("statusLabel")
        self.hint_label.setWordWrap(True)
        task_layout.addWidget(self.hint_label)

        btn_row = QHBoxLayout()
        self.correct_btn = QPushButton("✅ Правильно")
        self.correct_btn.setObjectName("primaryButton")
        self.correct_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.correct_btn.clicked.connect(self._on_correct)

        self.wrong_btn = QPushButton("❌ Неправильно")
        self.wrong_btn.setObjectName("dangerButton")
        self.wrong_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.wrong_btn.clicked.connect(self._on_wrong)

        btn_row.addWidget(self.correct_btn)
        btn_row.addWidget(self.wrong_btn)
        task_layout.addLayout(btn_row)

        root.addWidget(self.task_frame)

        # victory banner
        self.victory_label = QLabel()
        self.victory_label.setObjectName("victoryLabel")
        self.victory_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.victory_label.setVisible(False)
        root.addWidget(self.victory_label)

        root.addStretch()

    # --- generation ---

    def _on_generate(self):
        topic = self.topic_input.text().strip()
        if not topic:
            self.status_label.setText("⚠ Введите тему")
            return
        diff = self.diff_combo.currentText()
        self.gen_btn.setEnabled(False)
        self.status_label.setText("⏳ Призыв босса…")
        self.boss_frame.setVisible(False)
        self.task_frame.setVisible(False)
        self.victory_label.setVisible(False)

        self._thread = _GenerateThread(topic, diff)
        self._thread.finished.connect(self._on_result)
        self._thread.start()

    def _on_result(self, result):
        self.gen_btn.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ Ошибка: {result}")
            return
        self._boss = result
        self._current_task = 0
        self.status_label.setText("")

        self.boss_name_label.setText(f"🐉 {result.boss_name}")
        self.hp_bar.setMaximum(result.boss_hp)
        self.hp_bar.setValue(result.boss_hp)
        self.taunt_label.setText(f"«{result.taunt_on_wrong}»")
        self.boss_frame.setVisible(True)

        self._show_task()

    # --- gameplay ---

    def _show_task(self):
        if not self._boss or self._current_task >= len(self._boss.tasks):
            self._win()
            return
        task = self._boss.tasks[self._current_task]
        self.task_label.setText(f"⚔ Задача {task.task_number}: {task.text}")
        self.hint_label.setText(f"💡 Подсказка: {task.answer_hint}")
        self.task_frame.setVisible(True)

    def _on_correct(self):
        if not self._boss:
            return
        hp = self.hp_bar.value() - 1
        self.hp_bar.setValue(hp)
        self.taunt_label.setText(f"«{self._boss.taunt_on_correct}»")
        self._current_task += 1
        if hp <= 0:
            self._win()
        else:
            self._show_task()

    def _on_wrong(self):
        if not self._boss:
            return
        self.taunt_label.setText(f"«{self._boss.taunt_on_wrong}»")

    def _win(self):
        self.task_frame.setVisible(False)
        self.hp_bar.setValue(0)
        if self._boss:
            self.victory_label.setText(f"🏆 ПОБЕДА! {self._boss.victory_phrase}")
        self.victory_label.setVisible(True)
        self.taunt_label.setText("Босс повержен!")
