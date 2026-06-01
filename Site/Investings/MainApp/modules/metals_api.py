import requests
import pandas as pd
from io import BytesIO
import datetime as dt
import urllib3
from decimal import Decimal
import xml.etree.ElementTree as ET
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

def get_metal_price_history(metal_code, days=30):
    from django.core.cache import cache
    import xml.etree.ElementTree as ET
    from datetime import datetime, timedelta

    cache_key = f'metal_history_{metal_code}_{days}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_req1 = start_date.strftime('%d/%m/%Y')
    date_req2 = end_date.strftime('%d/%m/%Y')
    url = f'http://www.cbr.ru/scripts/xml_metall.asp?date_req1={date_req1}&date_req2={date_req2}'

    try:
        response = requests.get(url, verify=False, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        dates = []
        prices = []
        for record in root.findall('Record'):
            code = record.get('Code')
            if code and int(code) == metal_code:
                buy = record.find('Buy')
                if buy is not None and buy.text:
                    price = Decimal(buy.text.replace(',', '.'))
                    record_date = record.get('Date')
                    if record_date:
                        try:
                            d = datetime.strptime(record_date, '%d.%m.%Y')
                            dates.append(d.strftime('%d.%m'))
                        except:
                            dates.append(record_date[:-5])
                    else:
                        dates.append('')
                    prices.append(float(price))
        if len(dates) > days:
            dates = dates[-days:]
            prices = prices[-days:]
        result = {'dates': dates, 'prices': prices}
        cache.set(cache_key, result, 21600)  # 6 часов
        return result
    except Exception as e:
        print(f"Ошибка получения истории металлов: {e}")
        return {'dates': [], 'prices': []}