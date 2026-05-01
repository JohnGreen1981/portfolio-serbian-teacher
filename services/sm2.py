"""
Реализация алгоритма SuperMemo-2 (SM-2).

Параметры карточки:
  ease_factor  - коэффициент лёгкости (начальный 2.5, минимум 1.3)
  interval     - текущий интервал в днях
  repetitions  - количество успешных повторений подряд

Оценка ответа (q):
  0 - полный провал (не вспомнил)
  1 - неправильно, но вспомнил после подсказки
  2 - неправильно, но ответ казался близким
  3 - правильно, но с трудом
  4 - правильно с небольшой паузой
  5 - правильно, мгновенно
"""

from datetime import datetime, timedelta, timezone


def calculate_next_review(
    ease_factor: float,
    interval: int,
    repetitions: int,
    quality: int,
) -> tuple[float, int, int, datetime]:
    """
    Рассчитывает следующий интервал по SM-2.

    Returns:
        (new_ease_factor, new_interval, new_repetitions, next_review_at)
    """
    if quality < 0 or quality > 5:
        raise ValueError("quality must be 0-5")

    if quality < 3:
        # Ответ неправильный - сброс
        new_repetitions = 0
        new_interval = 1
    else:
        # Ответ правильный
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)
        new_repetitions = repetitions + 1

    # Обновляем ease_factor
    new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ease_factor = max(1.3, new_ease_factor)

    next_review_at = datetime.now(timezone.utc) + timedelta(days=new_interval)

    return new_ease_factor, new_interval, new_repetitions, next_review_at


def quality_from_text(answer: str) -> int:
    """
    Преобразует текстовую оценку пользователя в цифровую для SM-2.
    Используется в /quiz: бот сам оценивает ответ через GPT,
    но эта функция нужна для быстрой кнопочной оценки.
    """
    mapping = {
        "не знаю": 0,
        "забыл": 0,
        "плохо": 1,
        "сложно": 2,
        "трудно": 2,
        "нормально": 3,
        "хорошо": 4,
        "отлично": 5,
        "легко": 5,
    }
    return mapping.get(answer.lower().strip(), 3)


def quality_from_correctness(is_correct: bool, was_hard: bool = False) -> int:
    """Упрощённая оценка: правильно/неправильно."""
    if not is_correct:
        return 1
    return 3 if was_hard else 4
