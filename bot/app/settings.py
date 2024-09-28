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

db_path = 'settings.db'

default_verbose = os.getenv('BOT_DEFAULT_VERBOSE', 'false').lower() in ('true', '1', 't')
default_pipeline = os.getenv('BOT_DEFAULT_PIPELINE', 'faq_cases')

pipelines = {
    "baseline": "Вариант кейсхолдера",
    "faq": "Поиск по вопросам FAQ",
    "faq_cases": "Поиск по вопросам FAQ+Кейсы"
}


async def init_db() -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER,
            pipeline TEXT,
            verbose BOOLEAN,
            PRIMARY KEY (chat_id)
        )
        ''')
        await db.commit()


async def get_pipeline(chat_id: int) -> str:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT pipeline FROM chats WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_pipeline_or_default(chat_id: int) -> str:
    return await get_pipeline(chat_id) or default_pipeline


async def set_pipeline(chat_id: int, pipeline: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO chats (chat_id, pipeline) VALUES (?, ?)",
            (chat_id, pipeline)
        )
        await db.commit()


async def get_verbose(chat_id: int) -> bool:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT verbose FROM chats WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_verbose_or_default(chat_id: int) -> bool:
    return await get_verbose(chat_id) or default_verbose


async def set_verbose(chat_id: int, verbose: bool) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO chats (chat_id, verbose) VALUES (?, ?)",
            (chat_id, verbose)
        )
        await db.commit()
