import base64
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QScrollArea, QFileDialog, QApplication,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from models.schemas import KnowledgeScan


class _ScanThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, text: str, image_path: str | None):
        super().__init__()
        self.text = text
        self.image_path = image_path

    def run(self):
        try:
            if self.image_path:
                self._scan_image()
            else:
                from services.gemini_service import generate_knowledge_scan
                result = generate_knowledge_scan(self.text)
                self.finished.emit(result)
        except Exception as e:
            self.finished.emit(str(e))

    def _scan_image(self):
        import os
        from dotenv import load_dotenv
        from pathlib import Path as P
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        load_dotenv(P(__file__).resolve().parent.parent / ".env")
        api_key = os.getenv("GOOGLE_API_KEY", "")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.4,
        )

        img_data = Path(self.image_path).read_bytes()
        b64 = base64.b64encode(img_data).decode()
        ext = Path(self.image_path).suffix.lower()
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                "webp": "image/webp", "gif": "image/gif"}.get(ext.lstrip("."), "image/jpeg")

        message = HumanMessage(content=[
            {"type": "text", "text": (
                "Ты — строгий, но справедливый профессор биологии.\n"
                "На изображении — рукописный конспект или сочинение ученика.\n\n"
                "1. Расшифруй ВЕСЬ текст с фотографии.\n"
                "2. Проведи фактчекинг ТОЛЬКО биологических фактов (игнорируй орфографию).\n"
                "3. Если текст неразборчив — отметь это.\n\n"
                "Верни ответ СТРОГО в формате JSON без markdown-разметки:\n"
                '{"transcription": "...", "factual_errors": [{"quote": "...", '
                '"explanation": "...", "correct_fact": "..."}], '
                '"missing_key_concepts": ["..."], "suggested_score": "...", '
                '"teacher_summary": "..."}\n\n'
                "Всё на русском языке."
            )},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ])

        response = llm.invoke([message])
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        import json
        data = json.loads(text)
        result = KnowledgeScan(**data)
        self.finished.emit(result)


class KnowledgeScannerView(QWidget):
    def __init__(self):
        super().__init__()
        self._thread: _ScanThread | None = None
        self._image_path: str | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("📋  Проверка Домашки — ИИ-Ассистент")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        desc = QLabel(
            "Загрузите фото рукописного конспекта или вставьте текст вручную. "
            "ИИ проверит биологическую достоверность фактов."
        )
        desc.setObjectName("cardBody")
        desc.setWordWrap(True)
        root.addWidget(desc)

        # Image upload row
        img_row = QHBoxLayout()
        img_row.setSpacing(12)
        self.upload_btn = QPushButton("📷 Загрузить фото")
        self.upload_btn.setObjectName("primaryButton")
        self.upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_btn.clicked.connect(self._on_upload)
        img_row.addWidget(self.upload_btn)

        self.file_label = QLabel("Файл не выбран")
        self.file_label.setObjectName("statusLabel")
        img_row.addWidget(self.file_label, 1)

        self.clear_img_btn = QPushButton("✕")
        self.clear_img_btn.setObjectName("navButton")
        self.clear_img_btn.setFixedWidth(36)
        self.clear_img_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_img_btn.clicked.connect(self._clear_image)
        self.clear_img_btn.setVisible(False)
        img_row.addWidget(self.clear_img_btn)
        root.addLayout(img_row)

        # Or text input
        or_label = QLabel("— или введите текст вручную —")
        or_label.setObjectName("statusLabel")
        or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(or_label)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Вставьте сюда текст конспекта ученика для проверки…"
        )
        self.text_input.setObjectName("inputField")
        self.text_input.setFixedHeight(120)
        root.addWidget(self.text_input)

        # Generate button
        self.scan_btn = QPushButton("🔍 Сканировать")
        self.scan_btn.setObjectName("primaryButton")
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.clicked.connect(self._on_scan)
        root.addWidget(self.scan_btn)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        root.addWidget(self.status_label)

        # Results scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("resultScroll")
        self.result_container = QWidget()
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.result_layout.setSpacing(12)
        scroll.setWidget(self.result_container)
        root.addWidget(scroll)

    def _on_upload(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото конспекта", "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        if path:
            self._image_path = path
            self.file_label.setText(Path(path).name)
            self.clear_img_btn.setVisible(True)

    def _clear_image(self):
        self._image_path = None
        self.file_label.setText("Файл не выбран")
        self.clear_img_btn.setVisible(False)

    def _on_scan(self):
        text = self.text_input.toPlainText().strip()
        if not self._image_path and not text:
            self.status_label.setText("⚠ Загрузите фото или введите текст")
            return
        self.scan_btn.setEnabled(False)
        self.status_label.setText("⏳ Сканирую и проверяю факты…")
        self._clear_results()
        self._thread = _ScanThread(text, self._image_path)
        self._thread.finished.connect(self._on_result)
        self._thread.start()

    def _on_result(self, result):
        self.scan_btn.setEnabled(True)
        if isinstance(result, str):
            self.status_label.setText(f"❌ {result}")
            return
        self.status_label.setText("✅ Анализ завершён!")
        self._render(result)

    def _clear_results(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render(self, s: KnowledgeScan):
        # Transcription
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.addWidget(self._label("📄 Распознанный текст", "cardTitle"))
        cl.addWidget(self._label(s.transcription, "cardBody"))
        self.result_layout.addWidget(card)

        # Score
        score_card = QFrame()
        score_card.setObjectName("accentCard")
        sl = QVBoxLayout(score_card)
        sl.addWidget(self._label(f"⭐ Оценка: {s.suggested_score} / 10", "cardTitle"))
        sl.addWidget(self._label(s.teacher_summary, "cardBody"))
        self.result_layout.addWidget(score_card)

        # Errors
        if s.factual_errors:
            err_frame = QFrame()
            err_frame.setObjectName("accentCard")
            el = QVBoxLayout(err_frame)
            el.addWidget(self._label(f"❌ Фактические ошибки ({len(s.factual_errors)})", "cardTitle"))
            for i, err in enumerate(s.factual_errors, 1):
                el.addWidget(self._label(f"— Ошибка {i}: «{err.quote}»", "cardBody"))
                el.addWidget(self._label(f"  Почему неверно: {err.explanation}", "cardBody"))
                el.addWidget(self._label(f"  ✅ Правильно: {err.correct_fact}", "cardBody"))
            self.result_layout.addWidget(err_frame)
        else:
            ok_frame = QFrame()
            ok_frame.setObjectName("card")
            ol = QVBoxLayout(ok_frame)
            ol.addWidget(self._label("✅ Фактических ошибок не обнаружено!", "cardTitle"))
            self.result_layout.addWidget(ok_frame)

        # Missing concepts
        if s.missing_key_concepts:
            miss_frame = QFrame()
            miss_frame.setObjectName("card")
            ml = QVBoxLayout(miss_frame)
            ml.addWidget(self._label("📚 Пропущенные ключевые понятия", "cardTitle"))
            for concept in s.missing_key_concepts:
                ml.addWidget(self._label(f"• {concept}", "cardBody"))
            self.result_layout.addWidget(miss_frame)

    def _label(self, text: str, obj_name: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj_name)
        l.setWordWrap(True)
        return l
