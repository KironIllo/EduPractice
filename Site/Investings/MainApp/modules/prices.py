import datetime as dt
import requests
import pandas as pd
from io import BytesIO
import logging
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#import cbrapi as cbr

logger = logging.getLogger(__name__)

def get_currency_price(currency_id):
    """
    Получает актуальную цену валюты по ID с сайта ЦБ РФ.

    Args:
        currency_id (str): ID валюты (например, 'R01235' для USD)

    Returns:
        dict or None: словарь с данными о валюте или None в случае ошибки
    """
    try:
        # Формируем текущую дату для запроса
        date = dt.datetime.now()
        day = date.strftime("%d")
        month = date.strftime("%m")
        year = date.strftime("%Y")

        url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={day}/{month}/{year}'


        # Выполняем запрос к API ЦБ РФ
        response = requests.get(url, verify=False, timeout=30)
        response.raise_for_status()  # Проверяем статус ответа

        logger.info(f"Успешный запрос к API ЦБ: {url}")

        # Парсим XML в DataFrame, затем преобразуем в словарь
        prices = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()

        # Ищем нужную валюту по ID
        for i in prices["ID"]:
            if prices['ID'][i] == currency_id:
                return {
                    'id': prices['ID'][i],
                    'name': prices['Name'][i],
                    'rate': prices['VunitRate'][i].replace(',', '.'),
                    'nominal': int(prices['Nominal'][i]),      # добавляем
                    'char_code': prices['CharCode'][i]         # добавляем
                }

        logger.warning(f"Валюта с ID {currency_id} не найдена в ответе API")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к API ЦБ: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении цены валюты: {e}")
        return None
