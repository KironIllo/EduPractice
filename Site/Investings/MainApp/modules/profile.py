from django.shortcuts import render, get_list_or_404, redirect
from django.contrib.auth.decorators import login_required
from MainApp.models import Transaction, Profile
from MainApp.forms import transactionForm
from MainApp.modules.prices import get_currency_price
from decimal import Decimal
import datetime as dt
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@login_required(login_url="login/")
def Profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    # Получаем все покупки пользователя
    purchases = Transaction.objects.filter(user=request.user, transaction_type='buy')
    sales = Transaction.objects.filter(user=request.user, transaction_type='sell')
    
    # Рассчитываем текущий портфель
    portfolio = {}
    
    for purchase in purchases:
        money_id = purchase.moneyid
        if money_id not in portfolio:
            portfolio[money_id] = {
                'name': purchase.money,
                'quantity': 0,
                'total_cost': 0
            }
        portfolio[money_id]['quantity'] += float(purchase.count)
        portfolio[money_id]['total_cost'] += float(purchase.endprice)
    
    for sale in sales:
        money_id = sale.moneyid
        if money_id in portfolio:
            portfolio[money_id]['quantity'] -= float(sale.count)
            if portfolio[money_id]['quantity'] <= 0:
                del portfolio[money_id]
    
    # Получаем текущие цены и считаем стоимость
    portfel_list = []
    total_portfolio_value = 0
    
    for money_id, data in portfolio.items():
        price_data = get_currency_price(money_id)
        if price_data:
            current_price = float(price_data['rate'])
            current_value = data['quantity'] * current_price
            avg_price = data['total_cost'] / data['quantity'] if data['quantity'] > 0 else 0
            profit = current_value - data['total_cost']
            profit_percent = (profit / data['total_cost']) * 100 if data['total_cost'] > 0 else 0
            
            portfel_list.append({
                'name': data['name'],
                'quantity': data['quantity'],
                'avg_price': avg_price,
                'current_value': current_value,
                'profit': profit,
                'profit_percent': profit_percent,
                'portfolio_share': 0  # пока 0, позже пересчитаем
            })
            total_portfolio_value += current_value
    
    # Пересчитываем доли
    if total_portfolio_value > 0:
        for item in portfel_list:
            item['portfolio_share'] = (item['current_value'] / total_portfolio_value) * 100
    
    return render(request, 'htmls/profile.html', {
        'time': dt.datetime.now(),
        'balance': profile.balance,
        'portfel': portfel_list,
        'portfolio_count': len(portfel_list),
        'transactions_count': purchases.count() + sales.count()
    })

@login_required(login_url="login/")
def History(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'htmls/history.html', {'hist': transactions, 'balance': profile.balance})

def Buy(request, ID):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    # Получаем данные о валюте ДО проверки метода
    price_data = get_currency_price(ID)
    if not price_data:
        return render(request, 'htmls/error.html', {
            'error': 'Не удалось получить данные о валюте',
            'balance': profile.balance
        })

    if request.method == 'POST':
        form = transactionForm(data=request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user

            transaction.price = float(transaction.price)
            transaction.endprice = float(transaction.count) * transaction.price
            transaction.transaction_type = 'buy'

            endprice_decimal = Decimal(str(transaction.endprice))

            if profile.balance >= endprice_decimal:
                profile.balance -= endprice_decimal
                profile.save()
                transaction.save()
                return redirect('history')
            else:
                # Добавляем ошибку к форме
                form.add_error(None, '⚠️ Недостаточно средств для покупки!')
                # Возвращаем форму с ошибкой в тот же шаблон
                return render(request, 'htmls/buy.html', {
                    'name': price_data['name'],
                    'form': form,
                    'balance': profile.balance
                })
        # Если форма невалидна по другим причинам, тоже возвращаем её
        return render(request, 'htmls/buy.html', {
            'name': price_data['name'],
            'form': form,
            'balance': profile.balance
        })
    else:
        form = transactionForm(initial={
            'user': request.user,
            'moneyid': price_data['id'],
            'money': price_data['name'],
            'price': Decimal(price_data['rate']),
            'endprice': Decimal(price_data['rate']),
            'transaction_type': 'buy'
        })

    return render(request, 'htmls/buy.html', {
        'name': price_data['name'],
        'form': form,
        'balance': profile.balance
    })


def Sell(request, ID):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    price_data = get_currency_price(ID)
    if not price_data:
        return render(request, 'htmls/error.html', {
            'error': 'Не удалось получить данные о валюте',
            'balance': profile.balance
        })

    if request.method == 'POST':
        form = transactionForm(data=request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.price = abs(float(transaction.price))
            transaction.endprice = abs(float(transaction.count) * transaction.price)
            transaction.transaction_type = 'sell'

            # Проверка: есть ли у пользователя такая валюта для продажи?
            from django.db.models import Sum
            bought = Transaction.objects.filter(
                user=request.user, 
                moneyid=ID, 
                transaction_type='buy'
            ).aggregate(total=Sum('count'))['total'] or 0
            
            sold = Transaction.objects.filter(
                user=request.user, 
                moneyid=ID, 
                transaction_type='sell'
            ).aggregate(total=Sum('count'))['total'] or 0
            
            available = bought - sold
            
            if transaction.count > available:
                form.add_error(None, f'⚠️ У вас нет столько валюты! Доступно: {available}')
                return render(request, 'htmls/sell.html', {
                    'name': price_data['name'],
                    'form': form,
                    'balance': profile.balance
                })

            endprice_decimal = Decimal(str(transaction.endprice))
            profile.balance += endprice_decimal
            profile.save()
            transaction.save()
            return redirect('history')
    else:
        form = transactionForm(initial={
            'user': request.user,
            'moneyid': price_data['id'],
            'money': price_data['name'],
            'price': float(price_data['rate']),
            'endprice': float(price_data['rate']),
            'transaction_type': 'sell'
        })

    return render(request, 'htmls/sell.html', {
        'name': price_data['name'],
        'form': form,
        'balance': profile.balance
    })

def Balance(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if request.POST.get('income'):
            income_decimal = Decimal(request.POST['income'])
            profile.balance += income_decimal
            profile.save()
            return redirect('/')
    return render(request, 'htmls/balance.html', {'balance': profile.balance})