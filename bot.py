"""Точка входа. Application setup, регистрация handlers."""

import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from handlers.lesson import lesson_command, lesson_message, finish_lesson, pause_lesson
from handlers.quiz import quiz_command, quiz_answer
from handlers.add_word import build_add_handler, add_command
from handlers.stats import stats_command
from services import openai_client
from prompts.teacher import build_system_prompt
from keyboards import main_menu, BTN_LESSON, BTN_QUIZ, BTN_ADD, BTN_STATS, BTN_FINISH, BTN_PAUSE, BTN_HOME

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ALLOWED_USER_ID = int(os.environ["ALLOWED_USER_ID"])


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "chat"
    context.user_data["chat_history"] = []
    await update.message.reply_text(
        "До́бар да́н! Я твой учитель сербского языка.\n\n"
        "Выбери действие или просто напиши что-нибудь по-сербски!",
        reply_markup=main_menu(),
    )


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Завершает текущий урок досрочно."""
    if context.user_data.get("mode") == "lesson":
        await finish_lesson(update, context)
    else:
        await update.message.reply_text("Нет активного урока.")


async def deny_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает пользователям вне allowlist."""
    if update.message:
        await update.message.reply_text("Нет доступа.")


async def free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает свободные сообщения в зависимости от режима."""
    text = update.message.text
    mode = context.user_data.get("mode", "chat")

    # Обработка кнопок
    if text == BTN_HOME:
        if mode == "lesson":
            await pause_lesson(update, context)
        else:
            context.user_data["mode"] = "chat"
            await update.message.reply_text("Главное меню.", reply_markup=main_menu())
        return

    if text == BTN_FINISH:
        if mode == "lesson":
            await finish_lesson(update, context)
        return

    if text == BTN_PAUSE:
        if mode == "lesson":
            await pause_lesson(update, context)
        return

    if text == BTN_LESSON:
        await lesson_command(update, context)
        return

    if text == BTN_QUIZ:
        await quiz_command(update, context)
        return

    if text == BTN_STATS:
        await stats_command(update, context)
        return

    if mode == "lesson":
        await lesson_message(update, context)
        return

    if mode == "quiz":
        await quiz_answer(update, context)
        return

    # Свободный чат
    history = context.user_data.setdefault("chat_history", [])
    system = build_system_prompt()

    response = await openai_client.chat(
        system_prompt=system,
        history=history,
        user_message=update.message.text,
    )

    history.append({"role": "user", "content": update.message.text})
    history.append({"role": "assistant", "content": response})
    # Ограничиваем историю свободного чата
    if len(history) > 40:
        context.user_data["chat_history"] = history[-40:]

    await update.message.reply_text(response)


def main() -> None:
    token = os.environ["TELEGRAM_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(MessageHandler(
        filters.ALL & ~filters.User(ALLOWED_USER_ID),
        deny_access,
    ))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("lesson", lesson_command))
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(build_add_handler())
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, free_chat))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
