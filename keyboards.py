"""Клавиатуры для бота."""

from telegram import ReplyKeyboardMarkup

BTN_LESSON = "📚 Урок"
BTN_QUIZ = "🃏 Квиз"
BTN_ADD = "➕ Добавить слово"
BTN_STATS = "📊 Статистика"
BTN_FINISH = "✅ Завершить урок"
BTN_PAUSE = "⏸ Пауза до следующего раза"
BTN_HOME = "🏠 Главное меню"

ALL_BUTTONS = {BTN_LESSON, BTN_QUIZ, BTN_ADD, BTN_STATS, BTN_FINISH, BTN_PAUSE, BTN_HOME}


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BTN_LESSON, BTN_QUIZ], [BTN_ADD, BTN_STATS]],
        resize_keyboard=True,
    )


def lesson_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BTN_FINISH], [BTN_PAUSE], [BTN_ADD]],
        resize_keyboard=True,
    )


def back_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BTN_HOME]],
        resize_keyboard=True,
    )
