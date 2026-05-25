from django.shortcuts import render, redirect
from django.db.models import Sum
from decimal import Decimal
import json
from MainApp.models import Transaction, Profile
from MainApp.modules.prices import get_currency_price
from MainApp.forms import transactionForm
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def AssetDetail(request, ID):
    # Получаем данные о валюте
    price_data = get_currency_price(ID)
    if not price_data:
        return render(request, 'htmls/error.html', {
            'error': 'Не удалось получить данные об активе'
        })
    
    # Текущая цена
    current_price = float(price_data['rate'])
    
    # Получаем историю операций по этому активу
    transactions = Transaction.objects.filter(
        user=request.user,
        moneyid=ID
    ).order_by('-created_at') if request.user.is_authenticated else []
    
    # Количество в портфеле
    quantity = 0
    avg_price = 0
    total_cost = 0
    
    if request.user.is_authenticated:
        # Покупки
        buys = Transaction.objects.filter(
            user=request.user,
            moneyid=ID,
            transaction_type='buy'
        ).aggregate(
            total_quantity=Sum('count'),
            total_cost=Sum('endprice')
        )
        
        # Продажи
        sells = Transaction.objects.filter(
            user=request.user,
            moneyid=ID,
            transaction_type='sell'
        ).aggregate(total_quantity=Sum('count'))
        
        buy_quantity = float(buys['total_quantity'] or 0)
        buy_cost = float(buys['total_cost'] or 0)
        sell_quantity = float(sells['total_quantity'] or 0)
        
        quantity = buy_quantity - sell_quantity
        
        if quantity > 0:
            avg_price = buy_cost / quantity
            total_cost = buy_cost - (sell_quantity * avg_price) if sell_quantity > 0 else buy_cost
    
    # Текущая стоимость позиции
    current_value = quantity * current_price
    profit = current_value - total_cost
    profit_percent = (profit / total_cost * 100) if total_cost > 0 else 0
    
    # Формируем данные для графика (последние 30 дней)
    chart_data = generate_chart_data(ID)
    
    context = {
        'asset_id': ID,
        'name': price_data['name'],
        'current_price': current_price,
        'quantity': quantity,
        'avg_price': avg_price,
        'current_value': current_value,
        'profit': profit,
        'profit_percent': profit_percent,
        'transactions': transactions,
        'chart_data': json.dumps(chart_data),
        'balance': Profile.objects.get(user=request.user).balance if request.user.is_authenticated else 0
    }
    
    return render(request, 'htmls/asset.html', context)


def generate_chart_data(currency_id, days=30):
    """
    Генерирует данные для графика изменения цены за последние N дней
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
        # Получаем данные за последние N дней
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            try:
                date_str = current_date.strftime("%d/%m/%Y")
                url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date_str}'
                
                response = requests.get(url, verify=False, timeout=5)
                response.raise_for_status()
                
                prices = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()
                
                # Ищем нужную валюту
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


def BuyAsset(request, ID):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    price_data = get_currency_price(ID)
    
    if not price_data:
        return render(request, 'htmls/error.html', {'error': 'Не удалось получить данные'})
    
    if request.method == 'POST':
        form = transactionForm(data=request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.moneyid = price_data['id']
            transaction.money = price_data['name']
            transaction.price = Decimal(str(price_data['rate']))
            transaction.count = Decimal(request.POST.get('count'))
            transaction.endprice = transaction.count * transaction.price
            transaction.transaction_type = 'buy'
            
            if profile.balance >= transaction.endprice:
                profile.balance -= transaction.endprice
                profile.save()
                transaction.save()
                return redirect('asset', ID=ID)
            else:
                form.add_error(None, '⚠️ Недостаточно средств!')
        return render(request, 'htmls/asset_buy.html', {
            'name': price_data['name'],
            'price': price_data['rate'],
            'form': form,
            'balance': profile.balance,
            'asset_id': ID
        })
    else:
        form = transactionForm(initial={
            'user': request.user,
            'moneyid': price_data['id'],
            'money': price_data['name'],
            'price': price_data['rate'],
            'endprice': price_data['rate'],
            'count': 1,
            'transaction_type': 'buy'
        })
    
    return render(request, 'htmls/asset_buy.html', {
        'name': price_data['name'],
        'price': price_data['rate'],
        'form': form,
        'balance': profile.balance,
        'asset_id': ID
    })


def SellAsset(request, ID):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    price_data = get_currency_price(ID)
    
    if not price_data:
        return render(request, 'htmls/error.html', {'error': 'Не удалось получить данные'})
    
    # Доступное количество
    bought = Transaction.objects.filter(
        user=request.user, moneyid=ID, transaction_type='buy'
    ).aggregate(total=Sum('count'))['total'] or Decimal('0')
    sold = Transaction.objects.filter(
        user=request.user, moneyid=ID, transaction_type='sell'
    ).aggregate(total=Sum('count'))['total'] or Decimal('0')
    available = float(bought - sold)
    
    if request.method == 'POST':
        form = transactionForm(data=request.POST)
        if form.is_valid():
            count = Decimal(request.POST.get('count'))
            if count <= available:
                transaction = form.save(commit=False)
                transaction.user = request.user
                transaction.moneyid = price_data['id']
                transaction.money = price_data['name']
                transaction.price = Decimal(str(price_data['rate']))
                transaction.count = count
                transaction.endprice = transaction.count * transaction.price
                transaction.transaction_type = 'sell'
                
                profile.balance += transaction.endprice
                profile.save()
                transaction.save()
                return redirect('asset', ID=ID)
            else:
                form.add_error(None, f'⚠️ У вас только {available} {price_data["name"]} для продажи')
        return render(request, 'htmls/asset_sell.html', {
            'name': price_data['name'],
            'price': price_data['rate'],
            'form': form,
            'balance': profile.balance,
            'available': available,
            'asset_id': ID
        })
    else:
        form = transactionForm(initial={
            'user': request.user,
            'moneyid': price_data['id'],
            'money': price_data['name'],
            'price': price_data['rate'],
            'endprice': price_data['rate'],
            'count': 1,
            'transaction_type': 'sell'
        })
    
    return render(request, 'htmls/asset_sell.html', {
        'name': price_data['name'],
        'price': price_data['rate'],
        'form': form,
        'balance': profile.balance,
        'available': available,
        'asset_id': ID
    })