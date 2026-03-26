from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QSizePolicy, QApplication,
)
from PyQt6.QtCore import Qt

from views.portal import PortalView
from views.quest_generator import QuestGeneratorView
from views.adaptive_hw import AdaptiveHWView
from views.arena import ArenaView
from views.boss_fight import BossFightView
from views.tavern import TavernView
from views.forge import ForgeView
from views.bestiary import BestiaryView
from views.game_turn import GameTurnView
from views.knowledge_scanner import KnowledgeScannerView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduQuest — Геймифицированная платформа для учителей")
        self.setMinimumSize(1100, 700)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo = QLabel("🎓 EduQuest")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedHeight(70)
        sidebar_layout.addWidget(logo)

        self.stack = QStackedWidget()
        self.pages = [
            KnowledgeScannerView(),
            QuestGeneratorView(),
            AdaptiveHWView(),
            ArenaView(),
            BossFightView(),
            PortalView(),
            TavernView(),
            ForgeView(),
            BestiaryView(),
            GameTurnView(),
        ]
        for page in self.pages:
            self.stack.addWidget(page)

        menu_items = [
            ("📋  Проверка Домашки", 0),
            ("📝  Генератор квестов", 1),
            ("📊  Адаптивное ДЗ", 2),
            ("🏆  Арена классов", 3),
            ("🧪  Босс-файт", 4),
            ("🕰  Портал Времени", 5),
            ("📋  Таверна", 6),
            ("🔬  Кузница", 7),
            ("🧬  Бестиарий", 8),
            ("🌍  Ход Игры", 9),
        ]
        self.nav_buttons: list[QPushButton] = []
        for label, idx in menu_items:
            btn = QPushButton(label)
            if idx == 0:
                obj_name = "navButtonBlue"
            elif idx == 5:
                obj_name = "navButtonGold"
            else:
                obj_name = "navButton"
            btn.setObjectName(obj_name)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self._switch(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        self._is_dark = True
        self._styles_dir = Path(__file__).resolve().parent.parent / "styles"
        self.theme_btn = QPushButton("☀  Светлая тема")
        self.theme_btn.setObjectName("themeToggle")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        sidebar_layout.addWidget(self.theme_btn)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack)

        self._switch(0)

    def _switch(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        if self._is_dark:
            qss_file = self._styles_dir / "theme.qss"
            self.theme_btn.setText("☀  Светлая тема")
        else:
            qss_file = self._styles_dir / "theme_light.qss"
            self.theme_btn.setText("🌙  Тёмная тема")
        app = QApplication.instance()
        if app and qss_file.exists():
            app.setStyleSheet(qss_file.read_text(encoding="utf-8"))
