import asyncio
from pathlib import Path

import aiosqlite


class DataBaseManager:

    def __init__(self):
        self._db_path = Path.cwd() / "vacancies_db.sqlite"

    async def create_db(self):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS vacancies (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT NOT NULL,
                experience TEXT,
                remote_work TEXT,
                grade TEXT,
                city TEXT,
                link TEXT
                );
                """
            )
            await db.commit()
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS filters (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                text TEXT NOT NULL,
                );
                """
            )
            await db.commit()


if __name__ == '__main__':
    manager = DataBaseManager()
    manager.create_db()
