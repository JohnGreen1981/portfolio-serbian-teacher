# Serbian Teacher Bot

## Назначение

Очищенный портфельный репозиторий Telegram-бота для изучения сербского языка.

Проект показывает AI tutor workflow: свободный чат, уроки, квизы, добавление слов, интервальное повторение по SM-2 и хранение прогресса в Supabase.

## Стек

- Python
- python-telegram-bot
- OpenAI API
- Supabase
- python-dotenv

## Структура

```text
bot.py                      точка входа Telegram-бота
handlers/                   сценарии уроков, квизов, словаря и статистики
services/                   Supabase, curriculum, SM-2, OpenAI client
prompts/teacher.py          системный промпт учителя
keyboards.py                Telegram-клавиатуры
schema.sql                  схема Supabase и демо-программа
requirements.txt            зависимости
.env.example                безопасный шаблон окружения
```

## Портфельная рамка

Проект представлен как AI-assisted education automation prototype. В портфолио акцент на проектировании учебного workflow, промпта учителя, логики повторения, хранении прогресса и пользовательском Telegram UX.

Не описывать проект как production edtech backend, написанный вручную с нуля.

## Данные

В публичный репозиторий не входят реальные `.env`, пользовательская база, учебные PDF/DOCX и приватная история занятий.

`schema.sql` содержит демо-структуру и нейтральную учебную программу A1. Если используется материал из конкретного учебника или курса, перед публикацией нужно проверить права и заменить его на оригинальный demo content.

## Правила

- Не коммитить `.env`, токены, OpenAI/Supabase ключи, Telegram ID реального пользователя, PDF/DOCX учебников и пользовательские данные.
- `.env.example` должен содержать только placeholder-значения.
- При изменении Python-кода запускать `python3 -m py_compile bot.py handlers/*.py services/*.py prompts/*.py keyboards.py`.
- Перед GitHub push запускать проверку на секреты.
- `CLAUDE.md` должен оставаться ссылкой на `AGENTS.md`.
