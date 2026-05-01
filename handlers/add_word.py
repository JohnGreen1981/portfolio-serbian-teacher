"""Handler для /add. Добавление слова в словарь."""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from services import db, openai_client
from keyboards import BTN_ADD, ALL_BUTTONS, back_menu, main_menu, lesson_menu

WAITING_WORD = 1


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог добавления слова."""
    # Если слово передано сразу: /add вода
    args = context.args
    if args:
        word = " ".join(args)
        await process_word(update, context, word)
        return ConversationHandler.END

    await update.message.reply_text("Введи слово на сербском:", reply_markup=back_menu())
    return WAITING_WORD


async def receive_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    word = update.message.text.strip()
    await process_word(update, context, word)
    return ConversationHandler.END


async def process_word(update: Update, context: ContextTypes.DEFAULT_TYPE, word: str) -> None:
    await update.message.reply_text(f"Обогащаю слово «{word}» через AI...")

    try:
        enriched = await openai_client.enrich_word(word)
    except Exception as e:
        await update.message.reply_text(f"Ошибка при обращении к AI: {e}")
        return

    translation = enriched.get("translation", "")
    stress = enriched.get("stress", word)
    examples = enriched.get("examples", [])

    db.add_word(word=word, translation=translation, stress=stress, examples=examples)

    text = (
        f"Добавлено: {stress} - {translation}\n"
    )
    if examples:
        text += "\nПримеры:\n" + "\n".join(f"- {ex}" for ex in examples)

    keyboard = lesson_menu() if context.user_data.get("mode") == "lesson" else main_menu()
    await update.message.reply_text(text, reply_markup=keyboard)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = lesson_menu() if context.user_data.get("mode") == "lesson" else main_menu()
    await update.message.reply_text("Добавление отменено.", reply_markup=keyboard)
    return ConversationHandler.END


def build_add_handler() -> ConversationHandler:
    nav_buttons = list(ALL_BUTTONS - {BTN_ADD})
    return ConversationHandler(
        entry_points=[
            CommandHandler("add", add_command),
            MessageHandler(filters.Text([BTN_ADD]), add_command),
        ],
        states={
            WAITING_WORD: [MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.Text(nav_buttons),
                receive_word,
            )],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Text(nav_buttons), cancel),
        ],
    )
