import aiosqlite

db_path = 'metrics.db'


async def init_db() -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            answer_id TEXT PRIMARY KEY,
            question TEXT,
            answer TEXT,
            answered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            feedback INTEGER DEFAULT 0
        )
        ''')
        await db.commit()


async def save_answer(answer_id: str, question: str, answer: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO answers (answer_id, question, answer) VALUES (?, ?, ?)",
            (answer_id, question, answer)
        )
        await db.commit()


async def set_feedback(answer_id: str, feedback: int) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE answers SET feedback=? WHERE answer_id=?",
            (feedback, answer_id)
        )
        await db.commit()