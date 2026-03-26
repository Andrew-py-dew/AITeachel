from pydantic import BaseModel, Field


# --- Модуль 1: Генератор квестов ---

class QuestStage(BaseModel):
    stage_number: int = Field(description="Номер этапа (1-3)")
    title: str = Field(description="Название этапа")
    description: str = Field(description="Описание активности на этапе")
    duration_minutes: int = Field(description="Длительность в минутах")


class QuestBoss(BaseModel):
    name: str = Field(description="Имя финального босса")
    description: str = Field(description="Описание босса и его связь с темой урока")
    defeat_condition: str = Field(description="Условие победы над боссом")


class QuestScenario(BaseModel):
    quest_name: str = Field(description="Название квеста")
    setting: str = Field(description="Игровой сеттинг/мир квеста")
    stages: list[QuestStage] = Field(description="3 этапа урока-квеста")
    final_boss: QuestBoss = Field(description="Финальный босс")


# --- Модуль 2: Адаптивное ДЗ ---

class HomeworkTask(BaseModel):
    task_number: int
    text: str = Field(description="Текст задания")
    difficulty: str = Field(description="easy / medium / hard")
    hint: str = Field(description="Подсказка для ученика")


class AdaptiveHomework(BaseModel):
    student_name: str
    analysis: str = Field(description="Краткий анализ слабых мест ученика")
    tasks: list[HomeworkTask] = Field(description="Список персонализированных заданий")


# --- Модуль 3: Арена классов ---

class ArenaRound(BaseModel):
    round_type: str = Field(description="Тип задания (блиц, загадка, дебаты и т.д.)")
    question: str = Field(description="Текст задачи")
    points: int = Field(description="Количество очков за раунд")
    time_limit_seconds: int = Field(description="Лимит времени в секундах")


# --- Модуль 4: Босс-файт ---

class BossTask(BaseModel):
    task_number: int
    text: str = Field(description="Текст задачи")
    answer_hint: str = Field(description="Подсказка к ответу")


class BossFight(BaseModel):
    boss_name: str = Field(description="Имя босса")
    boss_hp: int = Field(description="HP босса = количество задач")
    taunt_on_wrong: str = Field(description="Реплика босса при ошибке игрока")
    taunt_on_correct: str = Field(description="Реплика босса при правильном ответе")
    victory_phrase: str = Field(description="Фраза при победе над боссом")
    tasks: list[BossTask] = Field(description="Список задач-атак")


# --- Модуль 5: Таверна (анализ класса) ---

class ClassStats(BaseModel):
    magic: int = Field(description="Креативность и вовлеченность (0-100)")
    strength: int = Field(description="Логика и понимание хард-скиллов (0-100)")
    agility: int = Field(description="Скорость выполнения задач (0-100)")
    endurance: int = Field(description="Удержание внимания к концу урока (0-100)")


class TavernAnalysis(BaseModel):
    status_name: str = Field(description="Название состояния класса, например 'Уставшие герои'")
    analysis: str = Field(description="Краткий разбор настроения (2-3 предложения)")
    stats: ClassStats = Field(description="Статы класса")
    recommendation: str = Field(description="Совет учителю в стиле RPG")


# --- Модуль 6: Кузница артефактов (визуальные пособия) ---

class ForgeArtifact(BaseModel):
    artifact_name: str = Field(description="Название артефакта")
    drawing_guide: str = Field(description="Пошаговая инструкция для рисования на доске")
    ai_image_prompt: str = Field(description="Detailed English prompt for AI image generation")
    didactic_value: str = Field(description="Почему этот визуал поможет понять тему")


# --- Модуль 7: Бестиарий (Bio-Edition) ---

class BioAbility(BaseModel):
    name: str = Field(description="Название способности")
    bio_function: str = Field(description="Реальная биологическая функция")
    rpg_effect: str = Field(description="Эффект в игре")


class BioWeakness(BaseModel):
    agent: str = Field(description="Что может разрушить/ингибировать")
    effect: str = Field(description="Что происходит при воздействии")


class BioRpgCard(BaseModel):
    hp: int = Field(description="Уровень жизнеспособности (0-100)")
    type: str = Field(description="Тип в игре")
    abilities: list[BioAbility] = Field(description="2-3 ключевые способности")
    weaknesses: list[BioWeakness] = Field(description="Уязвимости")


class BioCard(BaseModel):
    name_ru: str = Field(description="Название на русском")
    name_latin: str | None = Field(description="Название на латыни")
    classification: str = Field(description="Класс (Прокариоты, Эукариоты, Вирусы)")
    description: str = Field(description="Краткое научное описание (1-2 предложения)")
    rpg_card: BioRpgCard = Field(description="RPG-карточка объекта")
    image_generation_prompt: str = Field(description="English prompt for Dark Fantasy Bio-Punk illustration")


# --- Модуль 8: Ход Игры (Гейм-мастер) ---

class RandomEvent(BaseModel):
    name: str = Field(description="Название события (Засуха, Нашествие саранчи и т.д.)")
    effect: str = Field(description="Как это влияет на виды и ресурсы")


class GameTurnResult(BaseModel):
    new_balance_score: int = Field(description="Новый счёт баланса экосистемы (0-100)")
    consequences: str = Field(description="Описание последствий действий учеников")
    random_event: RandomEvent = Field(description="Случайное событие хода")
    next_turn_goal: str = Field(description="Новая цель для учеников на следующий ход")


# --- Модуль 9: Портал Времени ---

class ArtifactGift(BaseModel):
    artifact_name: str = Field(description="Название артефакта-подарка")
    didactic_meaning: str = Field(description="Дидактический смысл артефакта")
    image_prompt: str = Field(description="English prompt for AI image generation of the artifact")


# --- Модуль 10: Сканер Знаний (ИИ-Ассистент) ---

class FactualError(BaseModel):
    quote: str = Field(description="Цитата ученика с ошибкой")
    explanation: str = Field(description="Почему это биологически неверно")
    correct_fact: str = Field(description="Как должно быть на самом деле")


class KnowledgeScan(BaseModel):
    transcription: str = Field(description="Полный распознанный текст из рукописи ученика")
    factual_errors: list[FactualError] = Field(description="Список фактических ошибок")
    missing_key_concepts: list[str] = Field(description="Важные термины или процессы, которые ученик забыл упомянуть")
    suggested_score: str = Field(description="Оценка по 10-балльной шкале (снижать только за фактические ошибки)")
    teacher_summary: str = Field(description="Краткая выжимка для учителя")


class PortalMessage(BaseModel):
    dialogue: str = Field(description="Реплика исторической личности")
    emotion: str = Field(description="Эмоция персонажа (например: гордость, гнев, любопытство)")
    historical_fact_check: str = Field(description="Проверка исторической точности для учителя")
    is_duel_active: bool = Field(description="Активна ли интеллектуальная дуэль")
    artifact_gift: ArtifactGift | None = Field(default=None, description="Подарок-артефакт (если персонаж решил подарить)")
