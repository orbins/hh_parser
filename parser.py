import os
from pathlib import Path

import aiosqlite
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


class Parser:

    def __init__(self, url, text):
        self.url = url
        self.default_filter_text = text
        self.db_path = Path.cwd() / "vacancies_db.sqlite"

    async def main(self):
        tasks = []
        pages_count = await self._get_finded_pages_count()
        for num in range(pages_count):
            tasks.append(asyncio.create_task(self._parse_all_vacs_cards_on_page(num)))
        total_vacs = await asyncio.gather(*tasks)
        tasks = []
        # Удалять все записи перед сохранением
        for page_vacs in total_vacs:
            tasks.append(asyncio.create_task(self.save_vacs_to_db(page_vacs)))
        await asyncio.gather(*tasks)

    async def save_vacs_to_db(self, vacancies):
        # Использовать асинхронную итерацию
        for vacancy in vacancies:
            name = vacancy.find("span", class_="vacancy-name--c1Lay3KouCl7XasYakLk serp-item__title-link").text
            company = vacancy.find("span", class_="company-info-text--vgvZouLtf8jwBmaD1xgp").text
            experience = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-work-experience"})
            remote_work = vacancy.find("span", {"data-qa": "vacancy-label-remote-work-schedule"})
            grade = vacancy.find(
                "span",
                class_="fake-magritte-primary-text--Hdw8FvkOzzOcoR4xXWni compensation-text--kTJ0_rp54B2vNeZ3CTt2 separate-line-on-xs--mtby5gO4J0ixtqzW38wh"
            )
            city = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-address"}).find("span", class_="fake-magritte-primary-text--Hdw8FvkOzzOcoR4xXWni")
            link = vacancy.find("a", {"target": "_blank"}).get("href")
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                        INSERT INTO vacancies (name, company, experience, remote_work, grade, city, link)  VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                    (name, company, experience.text if experience else None, remote_work.text if remote_work else None, grade.text if grade else None, city.text if city else None, link),
                )
                await db.commit()

    async def _parse_all_vacs_cards_on_page(self, page_number, filter_text=None):
        params = {
            "page": page_number,
            "text": filter_text or self.default_filter_text
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, params=params) as response:
                html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find_all("div", class_="vacancy-card--z_UXteNo7bRGzxWVcL7y font-inter")

    async def _get_finded_pages_count(self, filter_text=None):
        page =  await self._get_first_page_with_vacs(filter_text)
        soup = BeautifulSoup(page, 'html.parser')
        pager = soup.find("div", class_="pager")
        max_page_block = pager.find("div", class_="pager-item-not-in-short-range")
        if max_page_block:
            pages_count = int(max_page_block.find("span").text)
        else:
            page_blocks = pager.find_all("a", class_="bloko-button")
            pages_count = len(page_blocks)
        return pages_count

    async def _get_first_page_with_vacs(self, filter_text=None):
        params = {"text": filter_text or self.default_filter_text}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, params=params) as response:
                return await response.text()


if __name__ == '__main__':
    parser = Parser(
        url=os.getenv("URL"),
        text=os.getenv("TEXT")
    )
    asyncio.run(parser.main())
