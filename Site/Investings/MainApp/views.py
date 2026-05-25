from django.shortcuts import render
from MainApp.models import Profile
import requests
import pandas as pd
import datetime as dt
import logging
import urllib3
from io import BytesIO

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

def Main(request):
    date = dt.datetime.now()
    url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date.strftime("%d")}/{date.strftime("%m")}/{date.strftime("%Y")}'

    currency_country_map = {
    'R01010': 'AU',   # Австралийский доллар
    'R01020A': 'AZ',  # Азербайджанский манат
    'R01030': 'DZ',   # Алжирский динар
    'R01035': 'GB',   # Фунт стерлингов
    'R01060': 'AM',   # Армянский драм
    'R01080': 'BH',   # Бахрейнский динар
    'R01090B': 'BY',  # Белорусский рубль
    'R01105': 'BO',   # Боливиано
    'R01115': 'BR',   # Бразильский реал
    'R01135': 'HU',   # Венгерский форинт
    'R01150': 'VN',   # Вьетнамский донг
    'R01200': 'HK',   # Гонконгский доллар
    'R01210': 'GE',   # Грузинский лари
    'R01215': 'DK',   # Датская крона
    'R01230': 'AE',   # Дирхам ОАЭ
    'R01235': 'US',   # Доллар США
    'R01239': 'EU',   # Евро
    'R01240': 'EG',   # Египетский фунт
    'R01270': 'IN',   # Индийская рупия
    'R01280': 'ID',   # Индонезийская рупия
    'R01300': 'IR',   # Иранский риал
    'R01335': 'KZ',   # Казахстанский тенге
    'R01350': 'CA',   # Канадский доллар
    'R01355': 'QA',   # Катарский риал
    'R01370': 'KG',   # Киргизский сом
    'R01375': 'CN',   # Китайский юань
    'R01395': 'CU',   # Кубинское песо
    'R01500': 'MD',   # Молдавский лей
    'R01503': 'MN',   # Монгольский тугрик
    'R01520': 'NG',   # Нигерийская найра
    'R01530': 'NZ',   # Новозеландский доллар
    'R01535': 'NO',   # Норвежская крона
    'R01540': 'OM',   # Оманский риал
    'R01565': 'PL',   # Польский злотый
    'R01580': 'SA',   # Саудовский риял
    'R01585F': 'RO',  # Румынский лей
    'R01589': 'XX',   # СДР (специальные права заимствования)
    'R01625': 'SG',   # Сингапурский доллар
    'R01670': 'TJ',   # Таджикский сомони
    'R01675': 'TH',   # Таиландский бат
    'R01685': 'BD',   # Бангладешская така
    'R01700J': 'TR',  # Турецкая лира
    'R01710A': 'TM',  # Туркменский манат
    'R01717': 'UZ',   # Узбекский сум
    'R01720': 'UA',   # Украинская гривна
    'R01760': 'CZ',   # Чешская крона
    'R01770': 'SE',   # Шведская крона
    'R01775': 'CH',   # Швейцарский франк
    'R01800': 'ET',   # Эфиопский быр
    'R01805F': 'RS',  # Сербский динар
    'R01810': 'ZA',   # Южноафриканский рэнд
    'R01815': 'KR',   # Южнокорейская вона
    'R01820': 'JP',   # Японская иена
    'R02005': 'MM',   # Мьянманский кьят
    }


    try:
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
        prices = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()

        pric = []
        for i in prices["ID"]:
            currency_id = prices['ID'][i]
            country_code = currency_country_map.get(currency_id, '')  # получаем код страны
            pric.append([
                currency_id,                                    # value.0
                prices['Name'][i],                              # value.1
                float(prices['VunitRate'][i].replace(',', '.')), # value.2
                country_code                                    # value.3
            ])

        bal = 0
        if request.user.is_authenticated:
            profile, _ = Profile.objects.get_or_create(user=request.user)
            bal = profile.balance

        return render(request, 'htmls/main.html', {'prices': pric, 'balance': bal})

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return render(request, 'htmls/main.html', {'prices': []})