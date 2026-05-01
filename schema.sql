-- Serbian Teacher Bot: demo-схема базы данных Supabase
-- Выполнить через SQL Editor в Supabase.

-- Таблица: словарь пользователя
CREATE TABLE IF NOT EXISTS vocabulary (
    id          BIGSERIAL PRIMARY KEY,
    word        TEXT NOT NULL,
    translation TEXT NOT NULL,
    stress      TEXT NOT NULL,          -- сербское слово с ударением
    examples    TEXT[] DEFAULT '{}',    -- массив примеров предложений
    added_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица: параметры SM-2 для каждого слова
CREATE TABLE IF NOT EXISTS reviews (
    id             BIGSERIAL PRIMARY KEY,
    word_id        BIGINT NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    ease_factor    FLOAT NOT NULL DEFAULT 2.5,
    interval       INT NOT NULL DEFAULT 1,    -- интервал в днях
    repetitions    INT NOT NULL DEFAULT 0,
    next_review_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(word_id)
);

-- Таблица: история занятий
CREATE TABLE IF NOT EXISTS sessions (
    id         BIGSERIAL PRIMARY KEY,
    topic      TEXT NOT NULL,
    summary    TEXT,
    new_words  TEXT[] DEFAULT '{}',     -- слова, добавленные за занятие
    started_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица: демо-программа A1
CREATE TABLE IF NOT EXISTS curriculum (
    id               BIGSERIAL PRIMARY KEY,
    lesson_number    INT NOT NULL UNIQUE,
    title            TEXT NOT NULL,
    grammar_topics   TEXT[] NOT NULL DEFAULT '{}',
    key_phrases      TEXT[] NOT NULL DEFAULT '{}',
    current_phase    INT NOT NULL DEFAULT 1,
    phases           TEXT[] NOT NULL DEFAULT ARRAY['Введение', 'Диалог', 'Практика', 'Тест'],
    dialogues        TEXT[] NOT NULL DEFAULT '{}',
    grammar_notes    TEXT[] NOT NULL DEFAULT '{}',
    vocabulary_list  TEXT[] NOT NULL DEFAULT '{}',
    completed_at     TIMESTAMPTZ       -- NULL = не пройден
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_reviews_next_review ON reviews(next_review_at);
CREATE INDEX IF NOT EXISTS idx_curriculum_lesson_number ON curriculum(lesson_number);
CREATE INDEX IF NOT EXISTS idx_curriculum_completed ON curriculum(completed_at);

-- Наполнение curriculum: нейтральная demo-программа из 12 тем.
INSERT INTO curriculum (lesson_number, title, grammar_topics, key_phrases) VALUES
(1, 'Dobar dan',
 ARRAY['Именительный падеж', 'Глагол biti', 'Личные местоимения'],
 ARRAY['Dobar dan', 'Kako se zoveš?', 'Zovem se...', 'Ja sam iz...']),

(2, 'Moja zemlja',
 ARRAY['Род существительных', 'Отрицание', 'Предлоги iz/u'],
 ARRAY['Odakle si?', 'Govorim srpski', 'Da li govoriš...?']),

(3, 'Razumeš li?',
 ARRAY['Глаголы I спряжения', 'Вопрос с da li'],
 ARRAY['Razumem / Ne razumem', 'Možeš li da ponoviš?', 'Kako se kaže...?']),

(4, 'Moja porodica',
 ARRAY['Притяжательные местоимения', 'Имена родственников'],
 ARRAY['Ovo je moja porodica', 'Imam brata/sestru', 'Koliko imaš godina?']),

(5, 'Moj svet',
 ARRAY['Локатив с предлогом u/na', 'Глагол živeti'],
 ARRAY['Gde živiš?', 'Živim u Beogradu', 'Sviđa mi se...']),

(6, 'Šta radiš?',
 ARRAY['Настоящее время', 'Профессии', 'Глагол raditi'],
 ARRAY['Šta radiš?', 'Ja sam pravnik', 'Gde radiš?']),

(7, 'Srećan put!',
 ARRAY['Аккузатив (прямой объект)', 'Глаголы движения'],
 ARRAY['Idem u...', 'Srećan put!', 'Kada ideš?']),

(8, 'Stil života',
 ARRAY['Модальные глаголы: moći, hteti, morati'],
 ARRAY['Mogu / Ne mogu', 'Hoću da...', 'Moram da...']),

(9, 'Upomoć!',
 ARRAY['Императив', 'Выражение просьбы/необходимости'],
 ARRAY['Pomozite!', 'Zovite lekara!', 'Boli me...']),

(10, 'Kako je kod vas?',
 ARRAY['Сравнительная степень', 'Описание мест'],
 ARRAY['Kako je kod vas?', 'Ovde je lepo', 'Bolje/gore nego...']),

(11, 'Odelo čini čoveka',
 ARRAY['Инструментал', 'Описание внешности и одежды'],
 ARRAY['Kako izgledaš?', 'Nosim...', 'Odgovara ti...']),

(12, 'Hotel s pet zvezdica',
 ARRAY['Перфект (прошедшее время)', 'Глагол biti + participle'],
 ARRAY['Gde si bio/bila?', 'Bio sam u...', 'Kako ti je bilo?'])

ON CONFLICT (lesson_number) DO NOTHING;
