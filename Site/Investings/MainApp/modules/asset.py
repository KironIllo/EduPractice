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

    # Данные для графика (только для валют)
    chart_data = {'dates': [], 'prices': []}
    if not str(ID).isdigit():
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
    Работает только для валют (ID начинается с R). Для металлов возвращает пустой словарь.
    """
    import requests
    import pandas as pd
    from io import BytesIO
    from datetime import datetime, timedelta

    chart_data = {
        'dates': [],
        'prices': []
    }

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        current_date = start_date
        while current_date <= end_date:
            try:
                date_str = current_date.strftime("%d/%m/%Y")
                url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date_str}'

                response = requests.get(url, verify=False, timeout=5)
                response.raise_for_status()

                # Парсим XML в DataFrame
                prices = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()

                # Ищем нужную валюту по ID
                for i in prices["ID"]:
                    if prices['ID'][i] == currency_id:
                        price = float(prices['VunitRate'][i].replace(',', '.'))
                        chart_data['dates'].append(current_date.strftime('%d.%m'))
                        chart_data['prices'].append(price)
                        break

            except Exception as e:
                print(f"Ошибка получения данных за {current_date}: {e}")

            current_date += timedelta(days=1)

    except Exception as e:
        print(f"Ошибка генерации графика: {e}")

    return chart_data