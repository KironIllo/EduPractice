from django.shortcuts import render
from django.db.models import Sum
from decimal import Decimal
import json
from MainApp.models import Transaction, Profile
from MainApp.modules.asset_utils import get_asset_price
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def AssetDetail(request, ID):
    asset = get_asset_price(ID)
    if not asset:
        return render(request, 'htmls/error.html', {
            'error': 'Не удалось получить данные об активе'
        })
    current_price = asset['price']
    unit = asset['unit']

    # Получаем историю операций по этому активу
    transactions = Transaction.objects.filter(
        user=request.user,
        moneyid=ID
    ).order_by('-created_at') if request.user.is_authenticated else []

    quantity = Decimal('0')
    total_cost = Decimal('0')

    if request.user.is_authenticated:
        buys = Transaction.objects.filter(
            user=request.user,
            moneyid=ID,
            transaction_type='buy'
        ).aggregate(
            total_quantity=Sum('count'),
            total_cost=Sum('endprice')
        )
        sells = Transaction.objects.filter(
            user=request.user,
            moneyid=ID,
            transaction_type='sell'
        ).aggregate(total_quantity=Sum('count'))

        buy_quantity = buys['total_quantity'] or Decimal('0')
        buy_cost = buys['total_cost'] or Decimal('0')
        sell_quantity = sells['total_quantity'] or Decimal('0')

        quantity = buy_quantity - sell_quantity

        if quantity > 0:
            avg_price = buy_cost / quantity
            total_cost = buy_cost - (sell_quantity * avg_price) if sell_quantity > 0 else buy_cost

    current_value = quantity * current_price
    profit = current_value - total_cost
    profit_percent = (profit / total_cost) * 100 if total_cost > 0 else Decimal('0')


    chart_data = {'dates': [], 'prices': []}
    if str(ID).isdigit():
        from MainApp.modules.metals_api import get_metal_price_history
        chart_data = get_metal_price_history(int(ID), days=30)
    else:
        chart_data = generate_chart_data(ID)

    profile = None
    balance = 0
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        balance = profile.balance

    context = {
        'asset_id': ID,
        'name': asset['name'],
        'current_price': current_price,
        'unit': unit,
        'quantity': quantity,
        'avg_price': avg_price if quantity > 0 else 0,
        'current_value': current_value,
        'profit': profit,
        'profit_percent': profit_percent,
        'transactions': transactions,
        'chart_data': json.dumps(chart_data),
        'balance': balance
    }

    return render(request, 'htmls/asset.html', context)


def generate_chart_data(currency_id, days=30):
    """
    Генерирует данные для графика изменения цены валюты за последние N дней.
    Результат кешируется на 6 часов.
    """
    from django.core.cache import cache
    import requests
    import pandas as pd
    from io import BytesIO
    from datetime import datetime, timedelta
    import time

    cache_key = f'currency_chart_{currency_id}_{days}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    chart_data = {'dates': [], 'prices': []}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    current_date = start_date
    while current_date <= end_date:
        for attempt in range(3):  # 3 попытки
            try:
                date_str = current_date.strftime("%d/%m/%Y")
                url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date_str}'
                response = requests.get(url, verify=False, timeout=30)
                response.raise_for_status()
                prices = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()
                for i in prices["ID"]:
                    if prices['ID'][i] == currency_id:
                        price = float(prices['VunitRate'][i].replace(',', '.'))
                        chart_data['dates'].append(current_date.strftime('%d.%m'))
                        chart_data['prices'].append(price)
                        break
                break  # успешно — выходим из цикла попыток
            except Exception as e:
                if attempt == 2:
                    print(f"Ошибка получения данных за {current_date}: {e}")
                else:
                    time.sleep(2)  # пауза перед повторной попыткой
        current_date += timedelta(days=1)

    # Кешируем на 6 часов (21600 секунд)
    cache.set(cache_key, chart_data, 21600)
    return chart_data