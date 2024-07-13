import os
from pathlib import Path

import aiosqlite
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


class Parser:

    def __init__(self, url=None, text=None):
        self.url = url or os.getenv("DEFAULT_HH_URL")
        self.default_filter_text = text or os.getenv("DEFAULT_TEXT_FILTER")
        self._db_path = Path.cwd() / "vacancies_db.sqlite"

    async def save_vacancies_by_filter(self):
        await self._clear_vacancies_table()
        pages_count = await self._get_pages_count()
        tasks = []
        for num in range(pages_count):
            tasks.append(asyncio.create_task(self._save_all_vacancies_on_page(num)))
        await asyncio.gather(*tasks)

    async def _clear_vacancies_table(self):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "DELETE FROM vacancies"
            )
            await db.commit()

    async def _get_pages_count(self):
        page = await self._get_page()
        soup = BeautifulSoup(page, 'html.parser')
        pager = soup.find("div", class_="pager")
        max_page_block = pager.find("div", class_="pager-item-not-in-short-range")
        if max_page_block:
            pages_count = int(max_page_block.find("span").text)
        else:
            page_blocks = pager.find_all("a", class_="bloko-button")
            pages_count = len(page_blocks)
        return pages_count

    async def _save_all_vacancies_on_page(self, page_number):
        page = await self._get_page(page_number)
        soup = BeautifulSoup(page, 'html.parser')
        vacancies_cards = soup.find_all("div", class_="vacancy-card--z_UXteNo7bRGzxWVcL7y font-inter")
        tasks = []
        for vacancy in vacancies_cards:
            tasks.append(asyncio.create_task(self._save_vacancy(vacancy)))
        await asyncio.gather(*tasks)

    async def _get_page(self, page_number=0):
        params = {
            "text": self.default_filter_text,
            "page": page_number
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, params=params) as response:
                return await response.text()

    async def _save_vacancy(self, vacancy):
        data = await self._get_vacancy_data(vacancy)
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

    @staticmethod
    async def _get_vacancy_data(vacancy):
        name = vacancy.find("span", class_="vacancy-name--c1Lay3KouCl7XasYakLk serp-item__title-link").text
        company = vacancy.find("span", class_="company-info-text--vgvZouLtf8jwBmaD1xgp").text
        city = (vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-address"})
                .find("span", class_="fake-magritte-primary-text--Hdw8FvkOzzOcoR4xXWni").text)
        link = vacancy.find("a", {"target": "_blank"}).get("href")
        try:
            experience = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-work-experience"}).text
        except AttributeError:
            experience = "Не указан"
        try:
            remote_work = vacancy.find("span", {"data-qa": "vacancy-label-remote-work-schedule"}).text
        except AttributeError:
            remote_work = "Не указано"
        try:
            grade = vacancy.find(
                "span",
                class_="fake-magritte-primary-text--Hdw8FvkOzzOcoR4xXWni compensation-"
                       "text--kTJ0_rp54B2vNeZ3CTt2 separate-line-on-xs--mtby5gO4J0ixtqzW38wh"
            ).text
        except AttributeError:
            grade = "Не указан"
        return {
            "name": name,
            "company": company,
            "experience": experience,
            "remote_work": remote_work,
            "grade": grade,
            "city": city,
            "link": link
        }


if __name__ == '__main__':
    parser = Parser()
    asyncio.run(parser.save_vacancies_by_filter())
