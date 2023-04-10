import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dataclasses import dataclass
import asyncio
import nest_asyncio


@dataclass
class CurrencyCourses:
    dollar_to_rub_course: float
    rub_to_dollar_course: float
    eur_to_rub_course: float
    rub_to_eur_course: float
    dollar_to_eur_course: float
    eur_to_dollar_course: float


scheduler = AsyncIOScheduler()

dollar_course = 0
euro_course = 0

url = 'http://www.cbr.ru/scripts/XML_daily.asp'

currency_courses_data: CurrencyCourses

async def get_exchange_rates(url):
    global dollar_course, euro_course, currency_courses_data

    response = requests.get(url)

    xml_page = BeautifulSoup(response.text, features='lxml-xml')

    all_valutes = xml_page.find_all('Valute')

    for valute in all_valutes:
        char_code = valute.find('CharCode').text

        if char_code == 'USD':
            dollar_course = float(valute.find('Value').text.replace(',', '.'))

        if char_code == 'EUR':
            euro_course = float(valute.find('Value').text.replace(',', '.'))

    dollar_to_rub_course = dollar_course - 1
    rub_to_dollar_course = round(1 / dollar_course - 0.0003, 4)

    eur_to_rub_course = euro_course - 1
    rub_to_eur_course = round(1 / euro_course - 0.0003, 4)

    dollar_to_eur_course = round(dollar_course / euro_course + 0.0003, 4)
    eur_to_dollar_course = round(euro_course / dollar_course - 0.0003, 4)

    currency_courses_data = CurrencyCourses(dollar_to_rub_course, rub_to_dollar_course, eur_to_rub_course, rub_to_eur_course, dollar_to_eur_course, eur_to_dollar_course)


loop = asyncio.get_event_loop()

nest_asyncio.apply()
entering_status = loop.run_until_complete(get_exchange_rates(url))

scheduler.add_job(get_exchange_rates, 'interval', hours=2, args=(url,))