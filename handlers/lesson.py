"""Handler для /lesson. Управление диалогом урока, фазы, пауза, сохранение summary."""

from telegram import Update
from telegram.ext import ContextTypes

from services import curriculum, openai_client, db
from prompts.teacher import build_system_prompt
from keyboards import lesson_menu, main_menu


async def lesson_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает новый урок или продолжает с текущей фазы."""
    lesson = curriculum.get_next_lesson()

    if lesson is None:
        await update.message.reply_text(
            "Поздравляю! Ты прошёл все 12 уроков демо-программы."
        )
        return

    context.user_data["lesson"] = lesson
    context.user_data["lesson_history"] = []
    context.user_data["mode"] = "lesson"

    phase_index = lesson.get("current_phase", 1) - 1
    phases = lesson.get("phases", [])
    total_phases = len(phases)
    is_resuming = phase_index > 0

    # Автозасев словаря урока с переводами (батч-запрос к AI, только на первой фазе)
    vocab_list = lesson.get("vocabulary_list", [])
    if vocab_list and phase_index == 0:
        await update.message.reply_text("Загружаю словарь урока...")
        enriched = await openai_client.enrich_words_batch(vocab_list)
        db.seed_lesson_vocabulary(enriched)

    # Контекст: текущая фаза + повторение предыдущего урока (только на 1-й фазе нового урока)
    lesson_context = curriculum.get_lesson_context(lesson)
    prev_lesson_context = ""
    if phase_index == 0:
        prev = curriculum.get_last_completed_lesson()
        if prev:
            prev_context = curriculum.get_lesson_context(prev)
            prev_lesson_context = f"ПРЕДЫДУЩИЙ УРОК (для краткого повторения в начале):\n{prev_context}"

    system = build_system_prompt(
        f"{lesson_context}\n\n{prev_lesson_context}".strip()
    )
    context.user_data["lesson_system"] = system

    if is_resuming:
        current_phase_desc = phases[phase_index] if phase_index < len(phases) else "Итоговый тест"
        start_prompt = (
            f"Продолжаем урок {lesson['lesson_number']}: {lesson['title']}.\n"
            f"Мы на фазе {phase_index + 1} из {total_phases}: {current_phase_desc}.\n"
            f"Начни эту фазу урока."
        )
    else:
        start_prompt = (
            f"Начинаем урок {lesson['lesson_number']}: {lesson['title']}.\n"
            f"{'Кратко напомни ключевые моменты предыдущего урока (2-3 предложения), затем начни первую фазу.' if prev_lesson_context else 'Начни первую фазу урока.'}"
        )

    intro = await openai_client.chat(
        system_prompt=system,
        history=[],
        user_message=start_prompt,
    )

    context.user_data["lesson_history"].append({"role": "assistant", "content": intro})

    phase_label = f"Фаза {phase_index + 1}/{total_phases}" if total_phases else ""
    header = f"📖 Урок {lesson['lesson_number']}: {lesson['title']}"
    if phase_label:
        header += f" | {phase_label}"

    await update.message.reply_text(f"{header}\n\n{intro}", reply_markup=lesson_menu())


async def lesson_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщения во время урока."""
    user_text = update.message.text
    history = context.user_data.get("lesson_history", [])
    system = context.user_data.get("lesson_system", build_system_prompt())

    response = await openai_client.chat(
        system_prompt=system,
        history=history,
        user_message=user_text,
    )

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": response})
    context.user_data["lesson_history"] = history

    await update.message.reply_text(response)


async def pause_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ставит урок на паузу: сохраняет прогресс, переходит к следующей фазе."""
    lesson = context.user_data.get("lesson")
    history = context.user_data.get("lesson_history", [])

    if not lesson:
        return

    await update.message.reply_text("Сохраняем прогресс...")

    result = await openai_client.generate_session_summary(history, lesson["title"])
    summary = result.get("summary", "")
    new_words = result.get("new_words", [])

    db.save_session(
        topic=lesson["title"],
        summary=summary,
        new_words=new_words,
    )

    current_phase = lesson.get("current_phase", 1)
    phases = lesson.get("phases", [])
    total_phases = len(phases)

    if current_phase >= total_phases:
        # Все фазы пройдены — завершаем урок
        curriculum.mark_lesson_complete(lesson["id"])
        text = f"Урок {lesson['lesson_number']} завершён!\n\n{summary}"
        if new_words:
            text += f"\n\nНовые слова: {', '.join(new_words)}"
        text += "\n\nМожешь идти на /quiz, чтобы закрепить слова урока."
        context.user_data.pop("lesson", None)
        context.user_data.pop("lesson_history", None)
        context.user_data.pop("lesson_system", None)
        context.user_data["mode"] = "chat"
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        # Переходим к следующей фазе
        curriculum.advance_phase(lesson["id"], current_phase)
        next_phase_desc = phases[current_phase] if current_phase < len(phases) else ""
        text = (
            f"Фаза {current_phase} из {total_phases} пройдена!\n\n"
            f"{summary}\n\n"
            f"Следующий раз начнём с: {next_phase_desc}\n\n"
            f"Нажми /lesson, когда будешь готов продолжить."
        )
        if new_words:
            text += f"\n\nНовые слова: {', '.join(new_words)}"
        context.user_data.pop("lesson", None)
        context.user_data.pop("lesson_history", None)
        context.user_data.pop("lesson_system", None)
        context.user_data["mode"] = "chat"
        await update.message.reply_text(text, reply_markup=main_menu())


async def finish_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Завершает урок досрочно: генерирует summary и сохраняет в БД."""
    lesson = context.user_data.get("lesson")
    history = context.user_data.get("lesson_history", [])

    if not lesson:
        return

    await update.message.reply_text("Подводим итоги урока...")

    result = await openai_client.generate_session_summary(history, lesson["title"])
    summary = result.get("summary", "")
    new_words = result.get("new_words", [])

    db.save_session(
        topic=lesson["title"],
        summary=summary,
        new_words=new_words,
    )
    curriculum.mark_lesson_complete(lesson["id"])

    context.user_data.pop("lesson", None)
    context.user_data.pop("lesson_history", None)
    context.user_data.pop("lesson_system", None)
    context.user_data["mode"] = "chat"

    text = f"Урок завершён!\n\n{summary}"
    if new_words:
        text += f"\n\nНовые слова: {', '.join(new_words)}"
    text += "\n\nМожешь идти на /quiz, чтобы закрепить слова урока."
    await update.message.reply_text(text, reply_markup=main_menu())
