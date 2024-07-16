import os

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from database_manager import DataBaseManager

load_dotenv()


class Parser:

    def __init__(self):
        self._db_manager = DataBaseManager()
        self._url = os.getenv("HH_URL")
        self._default_filter_text = os.getenv("DEFAULT_TEXT_FILTER")

    async def get_vacancies_list(self):
        return self._db_manager.get_all_vacancies()

    async def get_vacancies_details(self, url):
        page = await self._get_page(url)
        return await self.get_vacancies_details(page)

    async def parse_vacancies_by_filter(self, filter_):
        page = self._get_page(filter_text=filter_)
        total_finded_pages = await self._get_pages_count(page)
        tasks = []
        for num in range(total_finded_pages):
            page = await self._get_page(filter_text=filter_, page_number=num)
            tasks.append(asyncio.create_task(self._parse_all_vacancies_on_page(page)))
        await asyncio.gather(*tasks)

    async def _get_page(self, url=None, filter_text=None, page_number=0):
        params = {
            "text": filter_text or self._default_filter_text,
            "page": page_number
        }
        url = url or self._url
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.text()

    @staticmethod
    async def _get_pages_count(head_page):
        soup = BeautifulSoup(head_page, 'html.parser')
        pager = soup.find("div", class_="pager")
        max_page_block = pager.find("div", class_="pager-item-not-in-short-range")
        if max_page_block:
            pages_count = int(max_page_block.find("span").text)
        else:
            page_blocks = pager.find_all("a", class_="bloko-button")
            pages_count = len(page_blocks)
        return pages_count

    async def _parse_all_vacancies_on_page(self, page):
        soup = BeautifulSoup(page, 'html.parser')
        vacancies_cards = soup.find_all("div", class_="vacancy-card--z_UXteNo7bRGzxWVcL7y font-inter")
        tasks = []
        for vacancy in vacancies_cards:
            tasks.append(asyncio.create_task(self._parse_vacancy(vacancy)))
        await asyncio.gather(*tasks)

    async def _parse_vacancy(self, vacancy):
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
        vacancy_data = {
            "name": name,
            "company": company,
            "experience": experience,
            "remote_work": remote_work,
            "grade": grade,
            "city": city,
            "link": link
        }
        await self._db_manager.add_vacancy(vacancy_data)

    @staticmethod
    async def parse_vacancy_details(page):
        soup = BeautifulSoup(page, 'html.parser')
        description_block = soup.find("div", {"data-qa": "vacancy-description"})
        text = description_block.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        return text
