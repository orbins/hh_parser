import asyncio
from pathlib import Path

import aiosqlite


async def main():
    db_filepath = Path.cwd()/"vacancies_db.sqlite"
    if not db_filepath.exists():
        async with aiosqlite.connect(db_filepath) as db:
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


if __name__ == '__main__':
    asyncio.run(main())
