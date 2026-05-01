"""Работа с учебной программой."""

from datetime import datetime, timezone
from services.db import get_client


def get_next_lesson() -> dict | None:
    """Возвращает следующий непройденный урок (или текущий, если не завершён)."""
    result = (
        get_client()
        .table("curriculum")
        .select("*")
        .is_("completed_at", "null")
        .order("lesson_number")
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_last_completed_lesson() -> dict | None:
    """Возвращает последний завершённый урок (для повторения в начале нового)."""
    result = (
        get_client()
        .table("curriculum")
        .select("*")
        .not_.is_("completed_at", "null")
        .order("lesson_number", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_lesson_context(lesson: dict) -> str:
    """Форматирует текущую фазу урока в строку для системного промпта."""
    phase_index = lesson.get("current_phase", 1) - 1
    phases = lesson.get("phases", [])
    total_phases = len(phases)
    current_phase_desc = phases[phase_index] if phase_index < len(phases) else "Итоговый тест"

    dialogues = lesson.get("dialogues") or lesson.get("key_phrases") or []
    grammar_notes = lesson.get("grammar_notes") or lesson.get("grammar_topics") or []
    vocabulary_list = lesson.get("vocabulary_list") or []

    lines = [
        f"Урок {lesson['lesson_number']}: {lesson['title']}",
        f"Текущая фаза: {phase_index + 1} из {total_phases} — {current_phase_desc}",
    ]
    if dialogues:
        lines.append("Ключевые диалоги урока:\n" + "\n".join(f"  • {d}" for d in dialogues))
    if grammar_notes:
        lines.append("Правила (PAZITE):\n" + "\n".join(f"  • {n}" for n in grammar_notes))
    if vocabulary_list:
        lines.append("Слова урока: " + ", ".join(vocabulary_list))

    return "\n".join(lines)


def is_last_phase(lesson: dict) -> bool:
    return lesson.get("current_phase", 1) >= len(lesson.get("phases", []))


def advance_phase(lesson_id: int, current_phase: int) -> None:
    """Переходит к следующей фазе урока (пауза)."""
    get_client().table("curriculum").update(
        {"current_phase": current_phase + 1}
    ).eq("id", lesson_id).execute()


def mark_lesson_complete(lesson_id: int) -> None:
    """Завершает урок и сбрасывает фазу."""
    get_client().table("curriculum").update({
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "current_phase": 1,
    }).eq("id", lesson_id).execute()


def get_all_lessons() -> list[dict]:
    result = get_client().table("curriculum").select("*").order("lesson_number").execute()
    return result.data
