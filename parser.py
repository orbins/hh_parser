import os

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


class Parser:

    def __init__(self, url, text):
        self.url = url
        self.text = text

    async def get_vacancies_list(self):
        ...

    async def scrape_vacancies(self, page):
        params = {
            "page": page,
            "text": self.text
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, params=params) as response:
                print("Status: ", response.status)
                html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        vacancies = soup.find_all("div", class_="vacancy-card--z_UXteNo7bRGzxWVcL7y font-inter")
        print(f"Page {page}")
        for vacancy in vacancies:
            name = vacancy.find("span", class_="vacancy-name--c1Lay3KouCl7XasYakLk serp-item__title-link")
            company = vacancy.find("span", class_="company-info-text--vgvZouLtf8jwBmaD1xgp")
            experience = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-work-experience"})
            remote_work = vacancy.find("span", {"data-qa": "vacancy-label-remote-work-schedule"})
            grade = vacancy.find("span", class_="fake-magritte-primary-text--Hdw8FvkOzzOcoR4xXWni compensation-text--kTJ0_rp54B2vNeZ3CTt2 separate-line-on-xs--mtby5gO4J0ixtqzW38wh")
            city = vacancy.find("span", {"data-qa": "vacancy-serp__vacancy-address"}).find("span", class_="fake-magritte-primary-text--Hdw8FvkOzzOcoR4xXWni")
            link = vacancy.find("a", {"target": "_blank"}).get("href")
            print(f"name: {name.text}, company: {company.text}, experience: {experience.text if experience else 'Не указан'}, remote_work: {True if remote_work else 'Отсутствует'}, city: {city.text}, grade: {grade.text if grade else 'Не указан'}, link: {link}")

    async def main(self):
        async with aiohttp.ClientSession() as session:
            params = {"text": self.text}
            async with session.get(self.url, params=params) as response:
                html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        pager = soup.find("div", class_="pager")
        max_page_block = pager.find("div", class_="pager-item-not-in-short-range")
        if max_page_block:
            pages_count = int(max_page_block.find("span").text)
        else:
            page_blocks = pager.find_all("a", class_="bloko-button")
            pages_count = len(page_blocks)
        tasks = []
        for num in range(pages_count):
            tasks.append(asyncio.create_task(self.scrape_vacancies(num)))
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    parser = Parser(
        url=os.getenv("URL"),
        text=os.getenv("TEXT")
    )
    asyncio.run(parser.main())
