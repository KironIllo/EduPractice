from django.shortcuts import render
import requests
import pandas as pd
import datetime as dt
import logging

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настраиваем логирование
logger = logging.getLogger(__name__)

def Main(request):
    date = dt.datetime.now()
    url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date.strftime("%d")}/{date.strftime("%m")}/{date.strftime("%Y")}'

    try:
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()  # Проверяем статус ответа

        # Передаём байтовые данные через BytesIO
        from io import BytesIO
        prices = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()

        pric = []
        for i in prices["ID"]:
            pric.append([prices['ID'][i], prices['Name'][i], prices['VunitRate'][i]])

        return render(request, 'htmls/main.html', {'prices': pric})

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса: {e}")
        return render(request, 'htmls/main.html', {'prices': []})
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return render(request, 'htmls/main.html', {'prices': []})
