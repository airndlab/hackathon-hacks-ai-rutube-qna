#  Copyright 2024 AI RnD Lab
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os

import aiosqlite

# Путь к базе данных
BOT_DB_PATH = os.getenv('BOT_DB_PATH', 'settings.db')

# Получение значений переменных окружения с установленными значениями по умолчанию
DEFAULT_VERBOSE = os.getenv('BOT_DEFAULT_VERBOSE', 'false').lower() in ('true', '1', 't')
DEFAULT_PIPELINE = os.getenv('BOT_DEFAULT_PIPELINE', 'faq_cases')

# Словарь с возможными вариантами пайплайнов
pipelines = {
    "baseline": "Вариант кейсхолдера",
    "faq": "Поиск по вопросам FAQ",
    "faq_cases": "Поиск по вопросам FAQ+Кейсы"
}


# Инициализация базы данных
async def init_db() -> None:
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER,
            pipeline TEXT,
            verbose BOOLEAN,
            PRIMARY KEY (chat_id)
        )
        ''')
        await db.commit()


# Получения пайплайна
async def get_pipeline(chat_id: int) -> str:
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        cursor = await db.execute("SELECT pipeline FROM chats WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        return row[0] if row else None


# Получения пайплайна или значения по умолчанию
async def get_pipeline_or_default(chat_id: int) -> str:
    return await get_pipeline(chat_id) or DEFAULT_PIPELINE


# Установки пайплайна
async def set_pipeline(chat_id: int, pipeline: str) -> None:
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO chats (chat_id, pipeline) VALUES (?, ?)",
            (chat_id, pipeline)
        )
        await db.commit()


# Получение значения verbose
async def get_verbose(chat_id: int) -> bool:
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        cursor = await db.execute("SELECT verbose FROM chats WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        return row[0] if row else None


# Получение значения verbose или значения по умолчанию
async def get_verbose_or_default(chat_id: int) -> bool:
    return await get_verbose(chat_id) or DEFAULT_VERBOSE


# Установка значения verbose
async def set_verbose(chat_id: int, verbose: bool) -> None:
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO chats (chat_id, verbose) VALUES (?, ?)",
            (chat_id, verbose)
        )
        await db.commit()
