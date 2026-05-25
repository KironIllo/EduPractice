from django.shortcuts import render
from MainApp.models import Profile   # вместо userB
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

    try:
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
        prices = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()

        pric = []
        for i in prices["ID"]:
            pric.append([prices['ID'][i], prices['Name'][i], float(prices['VunitRate'][i].replace(',','.'))])
        
        bal = 0
        if request.user.is_authenticated:
            profile, _ = Profile.objects.get_or_create(user=request.user)
            bal = profile.balance

        return render(request, 'htmls/main.html', {'prices': pric, 'balance': bal})

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return render(request, 'htmls/main.html', {'prices': []})