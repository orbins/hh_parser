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

    async def add_filter(self, name, text):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                    INSERT INTO filters (
                        name, text
                    )
                    VALUES (
                        :name, :text
                    )
                    """,
                (name, text,)
            )
            await db.commit()

    async def delete_filter(self, pk):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                    DELETE FROM filters
                    WHERE id = ?
                    """,
                (pk,)
            )
            await db.commit()

    async def get_all_filters(self):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                 SELECT id, name, text FROM filters
                """,
            )
            await db.commit()

    async def add_vacancy(self, data):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                    INSERT INTO vacancies (
                        name, company, experience, remote_work, grade, city, link
                    )
                    VALUES (
                        :name, :company, :experience, :remote_work, :grade, :city, :link
                    )
                    """,
                data
            )
            await db.commit()

    async def get_all_vacancies(self):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                SELECT name, company, experience, remote_work, grade, city, link
                FROM vacancies
                """
            )
            await db.commit()

    async def clear_vacancies_table(self):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "DELETE FROM vacancies"
            )
            await db.commit()

