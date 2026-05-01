"""Handler для /stats."""

from telegram import Update
from telegram.ext import ContextTypes

from services.db import get_stats
from keyboards import main_menu


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stats = get_stats()

    text = (
        "Твой прогресс:\n\n"
        f"Слов в словаре: {stats['total_words']}\n"
        f"На повторение сегодня: {stats['due_today']}\n"
        f"Проведено занятий: {stats['sessions_done']}\n"
        f"Пройдено уроков: {stats['completed_lessons']}/12"
    )
    await update.message.reply_text(text, reply_markup=main_menu())
