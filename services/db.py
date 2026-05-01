"""Клиент Supabase. CRUD для всех четырёх таблиц."""

import os
from datetime import datetime, timezone

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _client = create_client(url, key)
    return _client


# ---------- vocabulary ----------

def seed_lesson_vocabulary(enriched_words: list[dict]) -> int:
    """Добавляет обогащённые слова урока в vocabulary+reviews, если их ещё нет.
    enriched_words: [{"word": str, "translation": str, "stress": str}, ...]
    """
    added = 0
    for item in enriched_words:
        word = item.get("word", "")
        if not word:
            continue
        existing = get_client().table("vocabulary").select("id").eq("word", word).execute()
        if existing.data:
            continue
        row = {
            "word": word,
            "translation": item.get("translation", ""),
            "stress": item.get("stress", word),
            "examples": [],
        }
        result = get_client().table("vocabulary").insert(row).execute()
        init_review(result.data[0]["id"])
        added += 1
    return added


def add_word(word: str, translation: str, stress: str, examples: list[str] | None = None) -> dict:
    client = get_client()
    existing = client.table("vocabulary").select("id").eq("word", word).execute()
    row = {"word": word, "translation": translation, "stress": stress, "examples": examples or []}
    if existing.data:
        word_id = existing.data[0]["id"]
        client.table("vocabulary").update(row).eq("id", word_id).execute()
        has_review = client.table("reviews").select("id").eq("word_id", word_id).execute()
        if not has_review.data:
            init_review(word_id)
        return {**row, "id": word_id}
    result = client.table("vocabulary").insert(row).execute()
    created = result.data[0]
    init_review(created["id"])
    return created


def get_word(word_id: int) -> dict | None:
    result = get_client().table("vocabulary").select("*").eq("id", word_id).execute()
    return result.data[0] if result.data else None


def get_all_words() -> list[dict]:
    result = get_client().table("vocabulary").select("*").order("added_at").execute()
    return result.data


# ---------- reviews ----------

def init_review(word_id: int) -> dict:
    """Инициализирует SM-2 запись для нового слова."""
    client = get_client()
    row = {
        "word_id": word_id,
        "ease_factor": 2.5,
        "interval": 1,
        "repetitions": 0,
        "next_review_at": datetime.now(timezone.utc).isoformat(),
    }
    result = client.table("reviews").insert(row).execute()
    return result.data[0]


def get_due_words() -> list[dict]:
    """Слова, у которых next_review_at <= NOW()."""
    now = datetime.now(timezone.utc).isoformat()
    result = (
        get_client()
        .table("reviews")
        .select("*, vocabulary(*)")
        .lte("next_review_at", now)
        .order("next_review_at")
        .execute()
    )
    return result.data


def update_review(word_id: int, ease_factor: float, interval: int, repetitions: int, next_review_at: datetime) -> dict:
    row = {
        "ease_factor": ease_factor,
        "interval": interval,
        "repetitions": repetitions,
        "next_review_at": next_review_at.isoformat(),
    }
    result = get_client().table("reviews").update(row).eq("word_id", word_id).execute()
    return result.data[0]


# ---------- sessions ----------

def save_session(topic: str, summary: str, new_words: list[str]) -> dict:
    row = {"topic": topic, "summary": summary, "new_words": new_words}
    result = get_client().table("sessions").insert(row).execute()
    return result.data[0]


def get_recent_sessions(limit: int = 3) -> list[dict]:
    result = (
        get_client()
        .table("sessions")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


# ---------- stats ----------

def get_stats() -> dict:
    client = get_client()
    total_words = len(client.table("vocabulary").select("id").execute().data)
    due_today = len(get_due_words())
    sessions_done = len(client.table("sessions").select("id").execute().data)
    completed_lessons = len(
        client.table("curriculum").select("id").not_.is_("completed_at", "null").execute().data
    )
    return {
        "total_words": total_words,
        "due_today": due_today,
        "sessions_done": sessions_done,
        "completed_lessons": completed_lessons,
    }
