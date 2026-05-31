import requests
import pandas as pd
from io import BytesIO
import datetime as dt
import urllib3
from decimal import Decimal

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Соответствие кодов металлов и их названий с русскими наименованиями
METAL_NAMES = {
    1: 'Золото',
    2: 'Серебро',
    3: 'Платина',
    4: 'Палладий',
}

def get_metal_price(metal_code):
    """
    Получает учетную цену драгоценного металла на текущую дату
    metal_code: 1 - золото, 2 - серебро, 3 - платина, 4 - палладий
    """
    try:

        date = dt.datetime.now() - dt.timedelta(days=2)
        day = date.strftime("%d")
        month = date.strftime("%m")
        year = date.strftime("%Y")
        date_req = f'{day}/{month}/{year}'
        url = f'http://www.cbr.ru/scripts/xml_metall.asp?date_req1={date_req}&date_req2={date_req}'

        response = requests.get(url, verify=False, timeout=30)
        response.raise_for_status()
        
        # Парсим XML
        data = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()
        
        # Ищем запись с нужным кодом металла
        for i in range(len(data.get('Code', []))):
            if int(data['Code'][i]) == metal_code:
                price = Decimal(str(data['Buy'][i]).replace(',', '.'))
                return {
                    'code': metal_code,
                    'name': METAL_NAMES.get(metal_code, 'Неизвестный металл'),
                    'price': price,
                    'nominal': 1,  # Цена указана за 1 грамм
                    'char_code': str(metal_code),   # добавляем
                    'unit': 'г'
                }
        return None
        
    except Exception as e:
        print(f"Ошибка получения цены металла {metal_code}: {e}")
        return None

def get_all_metals():
    """Получает данные по всем драгоценным металлам"""
    metals = []
    for code in [1, 2, 3, 4]:
        metal_data = get_metal_price(code)
        if metal_data:
            metals.append([
                str(code),           # ID металла
                metal_data['name'],  # Название
                metal_data['price'], # Цена за грамм
                metal_data['nominal'] # Номинал (всегда 1 для металлов)
            ])
    return metals