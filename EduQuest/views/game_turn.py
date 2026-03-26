from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QScrollArea, QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import GameTurnResult


class _GenerateThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, actions: str, world_state: str):
        super().__init__()
        self.actions = actions
        self.world_state = world_state

    def run(self):
        try:
            from services.gemini_service import generate_game_turn
            result = generate_game_turn(self.actions, self.world_state)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))


class GameTurnView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _GenerateThread | None = None
        self._turn_number = 0
        self._balance = 50
        self._world_log: list[str] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("🌍  School-мастер — Ход Игры  ")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # Turn counter & balance bar
        info_row = QHBoxLayout()
        info_row.setSpacing(16)

        self.turn_label = QLabel("Ход: 0")
        self.turn_label.setObjectName("cardTitle")
        info_row.addWidget(self.turn_label)

        balance_lbl = QLabel("⚖ Баланс:")
        balance_lbl.setObjectName("cardBody")
        info_row.addWidget(balance_lbl)

        self.balance_bar = QProgressBar()
        self.balance_bar.setObjectName("statBar")
        self.balance_bar.setMaximum(100)
        self.balance_bar.setValue(50)
        self.balance_bar.setFormat("50 / 100")
        self.balance_bar.setTextVisible(True)
        self.balance_bar.setFixedHeight(24)
        info_row.addWidget(self.balance_bar, 2)
        root.addLayout(info_row)

        # World state input
        self.world_input = QTextEdit()
        self.world_input.setPlaceholderText(
            "Текущее состояние мира (например: Трава — 80%, Зайцы — 30 шт, "
            "Волки — 5 шт, Вода — достаточно, Сезон — лето)"
        )
        self.world_input.setObjectName("inputField")
        self.world_input.setMaximumHeight(80)
        root.addWidget(self.world_input)

        # Student actions input
        self.actions_input = QTextEdit()
        self.actions_input.setPlaceholderText(
            "Действия учеников (например: Заселили 100 зайцев, Посадили лес, "
            "Убрали всех хищников, Построили дамбу…)"
        )
        self.actions_input.setObjectName("inputField")
        self.actions_input.setMaximumHeight(80)
        root.addWidget(self.actions_input)

        self.gen_btn = QPushButton("🎲 Следующий ход")
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
        actions = self.actions_input.toPlainText().strip()
        world_state = self.world_input.toPlainText().strip()
        if not actions or not world_state:
            self.status_label.setText("⚠ Заполните состояние мира и действия учеников")
            return
        self.gen_btn.setEnabled(False)
        self.status_label.setText("⏳ Гейм-мастер рассчитывает последствия…")
        self._thread = _GenerateThread(actions, world_state)
        self._thread.finished.connect(self._on_result)
        self._thread.start()

    def _on_result(self, result):
        self.gen_btn.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ {result}")
            return
        self._turn_number += 1
        self._balance = result.new_balance_score
        self.turn_label.setText(f"Ход: {self._turn_number}")
        self.balance_bar.setValue(self._balance)
        self.balance_bar.setFormat(f"{self._balance} / 100")
        self.status_label.setText(f"✅ Ход {self._turn_number} завершён!")
        self._render(result)

    def _render(self, r: GameTurnResult):
        # Consequences
        cons_card = QFrame()
        cons_card.setObjectName("accentCard")
        cl = QVBoxLayout(cons_card)
        cl.addWidget(self._label(f"📜 Ход {self._turn_number} — Последствия", "cardTitle"))
        cl.addWidget(self._label(r.consequences, "cardBody"))
        self.result_layout.insertWidget(0, cons_card)

        # Random event
        event_card = QFrame()
        event_card.setObjectName("card")
        el = QVBoxLayout(event_card)
        el.addWidget(self._label(f"🌪 Событие: {r.random_event.name}", "cardTitle"))
        el.addWidget(self._label(r.random_event.effect, "cardBody"))
        self.result_layout.insertWidget(1, event_card)

        # Next goal
        goal_card = QFrame()
        goal_card.setObjectName("accentCard")
        gl = QVBoxLayout(goal_card)
        gl.addWidget(self._label("🎯 Цель следующего хода", "cardTitle"))
        gl.addWidget(self._label(r.next_turn_goal, "cardBody"))
        self.result_layout.insertWidget(2, goal_card)

        # Separator between turns
        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet("background-color: #1E2939; margin: 8px 0;")
        self.result_layout.insertWidget(3, sep)

    def _label(self, text: str, obj_name: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj_name)
        l.setWordWrap(True)
        return l
