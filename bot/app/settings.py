import aiosqlite

from app.qna import default_pipeline

db_path = 'settings.db'


async def init_db():
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER,
            pipeline TEXT,
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


async def set_pipeline(chat_id: int, pipeline: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO chats (chat_id, pipeline) VALUES (?, ?)",
            (chat_id, pipeline)
        )
        await db.commit()
