"""Handler для /quiz. SM-2 флэшкарды."""

import random

from telegram import Update
from telegram.ext import ContextTypes

from services import db, openai_client
from services.sm2 import calculate_next_review
from keyboards import back_menu, main_menu


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает сессию повторения слов."""
    due = db.get_due_words()

    if not due:
        await update.message.reply_text(
            "Нет слов для повторения. Возвращайся позже или добавь новые слова через /add."
        )
        return

    context.user_data["quiz_queue"] = due
    context.user_data["quiz_index"] = 0
    context.user_data["mode"] = "quiz"

    await update.message.reply_text(
        f"Повторяем {len(due)} {'слово' if len(due) == 1 else 'слова' if len(due) < 5 else 'слов'}. Начнём!",
        reply_markup=back_menu(),
    )
    await show_next_card(update, context)


async def show_next_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    queue = context.user_data.get("quiz_queue", [])
    index = context.user_data.get("quiz_index", 0)

    if index >= len(queue):
        context.user_data["mode"] = "chat"
        await update.message.reply_text("Повторение завершено! Отличная работа.", reply_markup=main_menu())
        return

    card = queue[index]
    word_data = card["vocabulary"]
    direction = random.choice(["sr_to_ru", "ru_to_sr"])
    card["direction"] = direction
    context.user_data["current_card"] = card

    if direction == "sr_to_ru":
        question = f"Переведи на русский: *{word_data['stress']}*"
    else:
        question = f"Переведи на сербский: *{word_data['translation']}*"

    await update.message.reply_text(
        f"Карточка {index + 1}/{len(queue)}\n\n{question}",
        parse_mode="Markdown",
    )


async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ответ на флэшкарту."""
    user_answer = update.message.text
    card = context.user_data.get("current_card")

    if not card:
        return

    word_data = card["vocabulary"]
    direction = card.get("direction", "sr_to_ru")
    evaluation = await openai_client.evaluate_quiz_answer(
        word=word_data["word"],
        translation=word_data["translation"],
        user_answer=user_answer,
        direction=direction,
    )

    is_correct = evaluation.get("is_correct", False)
    feedback = evaluation.get("feedback", "")
    quality = evaluation.get("quality", 3)

    # Обновляем SM-2
    new_ef, new_interval, new_reps, next_review = calculate_next_review(
        ease_factor=card["ease_factor"],
        interval=card["interval"],
        repetitions=card["repetitions"],
        quality=quality,
    )
    db.update_review(
        word_id=card["word_id"],
        ease_factor=new_ef,
        interval=new_interval,
        repetitions=new_reps,
        next_review_at=next_review,
    )

    emoji = "✓" if is_correct else "✗"
    await update.message.reply_text(
        f"{emoji} {feedback}\n"
        f"Правильно: {word_data['translation']} - {word_data['stress']}\n"
        f"Следующее повторение через {new_interval} {'день' if new_interval == 1 else 'дней'}."
    )

    context.user_data["quiz_index"] = context.user_data.get("quiz_index", 0) + 1
    await show_next_card(update, context)
