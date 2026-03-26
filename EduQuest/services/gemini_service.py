import os
import json
from pathlib import Path
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from models.schemas import (
    QuestScenario, AdaptiveHomework, ArenaRound, BossFight,
    TavernAnalysis, ForgeArtifact, BioCard, GameTurnResult,
    PortalMessage, KnowledgeScan,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _build_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GOOGLE_API_KEY", "")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.8,
    )


def _call_structured(prompt_text: str, schema: type[BaseModel], **kwargs) -> BaseModel:
    """Send prompt to Gemini and parse response into a Pydantic model."""
    llm = _build_llm()
    structured_llm = llm.with_structured_output(schema)
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | structured_llm
    return chain.invoke(kwargs)


# ---------- public API ----------

def generate_quest(topic: str, grade: str) -> QuestScenario:
    return _call_structured(
        "Ты — геймдизайнер образовательных квестов. "
        "Создай квест-сценарий урока по теме «{topic}» для {grade} класса. "
        "Квест должен содержать игровой сеттинг, ровно 3 этапа и финального босса. "
        "Всё на русском языке.",
        QuestScenario,
        topic=topic,
        grade=grade,
    )


def generate_homework(student_name: str, topic: str, history: str) -> AdaptiveHomework:
    return _call_structured(
        "Ты — репетитор-аналитик. Ученик: {student_name}. Тема: {topic}. "
        "История оценок и ошибок:\n{history}\n\n"
        "Проанализируй слабые места и сгенерируй 3-5 персонализированных заданий "
        "разной сложности. Всё на русском.",
        AdaptiveHomework,
        student_name=student_name,
        topic=topic,
        history=history,
    )


def generate_arena_round(topic: str) -> ArenaRound:
    return _call_structured(
        "Ты — ведущий интеллектуального баттла между командами школьников. "
        "Тема: {topic}. Сгенерируй один раунд: тип задания, текст задачи, "
        "очки и лимит времени. Всё на русском.",
        ArenaRound,
        topic=topic,
    )


def generate_boss_fight(topic: str, difficulty: str) -> BossFight:
    diff_map = {"Easy": 3, "Medium": 5, "Hard": 7}
    count = diff_map.get(difficulty, 5)
    return _call_structured(
        "Ты — создатель RPG-боссов для школьных контрольных. "
        "Тема: {topic}. Сложность: {difficulty}. "
        "Создай босса с HP={count} (это количество задач). "
        "Придумай имя, реплики при ошибке и правильном ответе, фразу победы "
        "и ровно {count} задач. Всё на русском.",
        BossFight,
        topic=topic,
        difficulty=difficulty,
        count=count,
    )


def generate_tavern_analysis(feedback_text: str) -> TavernAnalysis:
    return _call_structured(
        "Ты — Мастер Таверны из RPG и экспертный психолог. "
        "Твоя задача — проанализировать отзывы учеников или заметки учителя: {feedback_text}. "
        "На основе текста оцени состояние класса по шкале от 0 до 100 для параметров: "
        "Магия (Креативность и вовлеченность), Сила (Логика и понимание хард-скиллов), "
        "Ловкость (Скорость выполнения задач), Выносливость (Удержание внимания к концу урока). "
        "Дай название состояния, краткий анализ и совет в стиле RPG. Всё на русском.",
        TavernAnalysis,
        feedback_text=feedback_text,
    )


def generate_bio_card(bio_object: str) -> BioCard:
    return _call_structured(
        "Ты — ведущий геймдизайнер RPG-игры 'EduQuest: Bio-Edition' и одновременно "
        "профессор цитологии. Твоя задача — описать биологический микро-объект {bio_object} "
        "(органоид, вирус, бактерия) как персонажа или артефакт игры, сохраняя 100% научную "
        "точность, но используя геймерский сленг.\n\n"
        "Требования:\n"
        "- name_ru: Название на русском\n"
        "- name_latin: Название на латыни (если применимо, иначе null)\n"
        "- classification: Класс (Прокариоты, Эукариоты, Вирусы и т.д.)\n"
        "- description: Краткое научное описание (1-2 предложения)\n"
        "- rpg_card.hp: 0-100, зависит от сложности структуры\n"
        "- rpg_card.type: Тип в игре (например 'Энергетический Кристалл' для Митохондрии, "
        "'Босс-Вирус' для ВИЧ, 'Кузница Белка' для Рибосомы)\n"
        "- rpg_card.abilities: 2-3 способности с name, bio_function и rpg_effect "
        "(например '+50 к Энергии Отряда', 'Синтез брони (мембраны)')\n"
        "- rpg_card.weaknesses: уязвимости с agent и effect\n"
        "- image_generation_prompt: Detailed English prompt for generating a hyper-realistic "
        "microscopic illustration of {bio_object} in 'Dark Fantasy Bio-Punk' style. "
        "Include '4k resolution', 'volumetric lighting', 'detailed textures', "
        "'macro photography style', 'glowing elements'.\n\n"
        "Всё на русском кроме image_generation_prompt и name_latin.",
        BioCard,
        bio_object=bio_object,
    )


def generate_game_turn(students_actions: str, current_world_state: str) -> GameTurnResult:
    return _call_structured(
        "Ты — Гейм-мастер экологической RPG-симуляции. "
        "Прошлый ход учеников: {students_actions}.\n"
        "Текущее состояние мира: {current_world_state}.\n\n"
        "Тебе нужно:\n"
        "1. Рассчитать последствия действий учеников (если зайцев много, а травы мало — "
        "баланс падает; если хищников мало — травоядные размножаются бесконтрольно и т.д.)\n"
        "2. Вкинуть случайное событие (Засуха, Нашествие саранчи, Вирусное заболевание, "
        "Мутация, Миграция и т.д.)\n"
        "3. Поставить новую цель для следующего хода\n\n"
        "new_balance_score: число 0-100, где 50 = идеальный баланс, 0 = экосистема мертва, "
        "100 = перенаселение.\n"
        "Будь научно точным, но используй RPG-стиль повествования. Всё на русском.",
        GameTurnResult,
        students_actions=students_actions,
        current_world_state=current_world_state,
    )


def generate_portal_reply(historical_figure: str, conversation_history: str, student_message: str) -> PortalMessage:
    return _call_structured(
        "Ты — {historical_figure}, реальная историческая личность. Ты находишься в «Портале Времени» — "
        "магическом пространстве, где ученик может поговорить с тобой.\n\n"
        "ПРАВИЛА ROLEPLAY:\n"
        "1. Говори от первого лица, в характере и стиле речи этой личности.\n"
        "2. Используй реальные факты из жизни персонажа. Если ученик упоминает что-то, "
        "чего не было в твоей эпохе (анахронизм), реагируй с удивлением и любопытством, "
        "но НЕ притворяйся, что знаешь об этом.\n"
        "3. ДУЭЛЬ: Если ученик бросает тебе интеллектуальный вызов или спорит — "
        "установи is_duel_active=true и веди аргументированный спор, используя знания своей эпохи.\n"
        "4. АРТЕФАКТ: Если ученик проявил особую мудрость, задал глубокий вопрос или "
        "выиграл дуэль — подари ему артефакт (artifact_gift). Артефакт должен быть связан "
        "с твоей деятельностью (например, Ньютон может подарить «Призму Познания»).\n"
        "5. historical_fact_check: кратко укажи, какие факты из твоей реплики соответствуют "
        "реальной истории, а какие — художественный вымысел (для учителя).\n\n"
        "История диалога:\n{conversation_history}\n\n"
        "Сообщение ученика: {student_message}\n\n"
        "Ответь на русском языке, кроме image_prompt в artifact_gift (на английском).",
        PortalMessage,
        historical_figure=historical_figure,
        conversation_history=conversation_history,
        student_message=student_message,
    )


def generate_knowledge_scan(transcribed_text: str) -> KnowledgeScan:
    return _call_structured(
        "Ты — строгий, но справедливый профессор биологии и старший эксперт по проверке "
        "экзаменационных работ.\n\n"
        "Тебе предоставлен распознанный текст рукописного конспекта или сочинения ученика. "
        "Твоя цель — провести жесткий фактчекинг (проверку на биологическую достоверность).\n\n"
        "ПРАВИЛА АНАЛИЗА:\n"
        "1. Игнорируй орфографические, пунктуационные и стилистические ошибки. Твой фокус — ТОЛЬКО биологические факты.\n"
        "2. Если ученик пишет что-то биологически неверное — это грубая фактическая ошибка.\n"
        "3. Если текст обрывается или неразборчив, отметь это, но не выдумывай текст за ученика.\n\n"
        "ТЕКСТ УЧЕНИКА:\n{transcribed_text}\n\n"
        "Верни:\n"
        "- transcription: полный текст как есть\n"
        "- factual_errors: список ошибок с цитатой, объяснением и правильным фактом\n"
        "- missing_key_concepts: 1-2 важных термина/процесса, которые ученик забыл упомянуть\n"
        "- suggested_score: оценка по 10-балльной шкале (снижай ТОЛЬКО за фактические ошибки)\n"
        "- teacher_summary: краткая выжимка для учителя в стиле 'Ученик хорошо понял X, но плавает в Y'\n\n"
        "Всё на русском языке.",
        KnowledgeScan,
        transcribed_text=transcribed_text,
    )


def generate_forge_artifact(teacher_request: str, topic: str) -> ForgeArtifact:
    return _call_structured(
        "Ты — Главный Кузнец визуальных артефактов. "
        "Учитель хочет создать наглядное пособие. Запрос учителя: {teacher_request}. Тема: {topic}. "
        "Составь: 1) Пошаговую инструкцию как нарисовать это мелом/маркером на доске, "
        "используя простые геометрические фигуры. "
        "2) Профессиональный английский промпт для генерации изображения "
        "(Stable Diffusion/Midjourney/Imagen), включая стиль, освещение и 4k. "
        "3) Объясни дидактическую ценность визуала. Всё на русском кроме AI-промпта.",
        ForgeArtifact,
        teacher_request=teacher_request,
        topic=topic,
    )
