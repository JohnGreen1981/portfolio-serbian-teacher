"""Обёртка над OpenAI API."""

import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

_client: AsyncOpenAI | None = None

MODEL = "gpt-4o-mini"
MAX_HISTORY = 20  # максимум сообщений в истории сессии


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


async def chat(
    system_prompt: str,
    history: list[dict],
    user_message: str,
) -> str:
    """
    Отправляет сообщение в OpenAI и возвращает ответ.

    history - список {"role": "user"/"assistant", "content": "..."}
    """
    messages = [{"role": "system", "content": system_prompt}]

    # Ограничиваем историю
    trimmed = history[-MAX_HISTORY:]
    messages.extend(trimmed)
    messages.append({"role": "user", "content": user_message})

    response = await get_client().chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content


async def enrich_word(word: str) -> dict:
    """
    Запрашивает у модели перевод, ударение и примеры для нового слова.
    Returns: {"translation": str, "stress": str, "examples": list[str]}
    """
    prompt = f"""Слово на сербском: {word}

Верни JSON (только JSON, без лишнего текста):
{{
  "translation": "перевод на русский",
  "stress": "слово с проставленным ударением (знак ´ над гласной)",
  "examples": ["пример 1 на сербском - перевод", "пример 2 на сербском - перевод"]
}}"""

    import json
    response = await get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


async def enrich_words_batch(words: list[str]) -> list[dict]:
    """
    Одним запросом получает перевод и ударение для списка слов.
    Returns: [{"word": str, "translation": str, "stress": str}, ...]
    """
    import json
    words_str = ", ".join(words)
    prompt = f"""Слова на сербском: {words_str}

Верни JSON-массив (только массив, без лишнего):
[
  {{"word": "слово", "translation": "перевод на русский", "stress": "сло́во"}}
]
Для каждого слова из списка — один объект. Ударение ставь знаком ´ над гласной."""

    response = await get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    # модель может вернуть {"words": [...]} или просто [...]
    if isinstance(data, list):
        return data
    return next((v for v in data.values() if isinstance(v, list)), [])


async def generate_session_summary(history: list[dict], topic: str) -> dict:
    """
    Генерирует summary занятия и список новых слов.
    Returns: {"summary": str, "new_words": list[str]}
    """
    import json
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in history
    )
    prompt = f"""Это диалог урока сербского языка по теме: {topic}

{history_text}

Верни JSON:
{{
  "summary": "краткое резюме урока (3-5 предложений на русском)",
  "new_words": ["список", "новых", "сербских", "слов", "из", "урока"]
}}"""

    response = await get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


async def evaluate_quiz_answer(word: str, translation: str, user_answer: str, direction: str = "sr_to_ru") -> dict:
    """
    Оценивает ответ пользователя во время флэшкарт.
    direction: "sr_to_ru" — спрашивали сербское, ждём русский перевод
               "ru_to_sr" — спрашивали русское, ждём сербское слово
    Returns: {"is_correct": bool, "feedback": str, "quality": int}
    """
    import json
    if direction == "sr_to_ru":
        prompt = f"""Сербское слово: {word} (перевод: {translation})
Пользователь должен был написать перевод на русский.
Ответ пользователя: {user_answer}"""
    else:
        prompt = f"""Русское слово: {translation} (сербский вариант: {word})
Пользователь должен был написать слово на сербском.
Ответ пользователя: {user_answer}"""

    prompt += """

Оцени ответ. Верни JSON:
{
  "is_correct": true/false,
  "feedback": "краткий фидбек (1 предложение)",
  "quality": число от 0 до 5 по шкале SM-2
}"""

    response = await get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
