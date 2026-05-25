# profile.py
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from MainApp.models import Transaction, Profile
from MainApp.forms import transactionForm
from MainApp.modules.prices import get_currency_price
import datetime as dt
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@login_required(login_url="login/")
def Profile_view(request):
    """Страница профиля с портфелем"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    # Получаем покупки и продажи пользователя
    buys = Transaction.objects.filter(user=request.user, transaction_type='buy')
    sells = Transaction.objects.filter(user=request.user, transaction_type='sell')
    
    portfolio = {}
    for b in buys:
        currency_id = b.moneyid
        if currency_id not in portfolio:
            portfolio[currency_id] = {
                'name': b.money,
                'quantity': Decimal('0'),
                'total_cost': Decimal('0')
            }
        portfolio[currency_id]['quantity'] += b.count
        portfolio[currency_id]['total_cost'] += b.endprice

    for s in sells:
        currency_id = s.moneyid
        if currency_id in portfolio:
            portfolio[currency_id]['quantity'] -= s.count
            if portfolio[currency_id]['quantity'] <= 0:
                del portfolio[currency_id]
    
    portfel_list = []
    total_portfolio_value = Decimal('0')

    for currency_id, data in portfolio.items():
        price_data = get_currency_price(currency_id)
        if price_data:
            current_price = Decimal(str(price_data['rate']))
            current_value = data['quantity'] * current_price
            avg_price = data['total_cost'] / data['quantity'] if data['quantity'] > 0 else Decimal('0')
            profit = current_value - data['total_cost']
            profit_percent = (profit / data['total_cost']) * 100 if data['total_cost'] > 0 else Decimal('0')
            portfel_list.append({
                'name': data['name'],
                'quantity': data['quantity'],
                'avg_price': avg_price,
                'current_value': current_value,
                'profit': profit,
                'profit_percent': profit_percent,
                'portfolio_share': 0
            })
            total_portfolio_value += current_value

    if total_portfolio_value > 0:
        for item in portfel_list:
            item['portfolio_share'] = (item['current_value'] / total_portfolio_value) * 100

    return render(request, 'htmls/profile.html', {
        'time': dt.datetime.now(),
        'balance': profile.balance,
        'portfel': portfel_list,
        'portfolio_count': len(portfel_list),
        'transactions_count': buys.count() + sells.count()
    })


@login_required(login_url="login/")
def History(request):
    """История операций пользователя"""
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'htmls/history.html', {
        'hist': transactions,
        'balance': profile.balance
    })

@login_required(login_url="login/")
def Buy(request, ID):
    """Покупка валюты с учётом номинала"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    price_data = get_currency_price(ID)
    if not price_data:
        return render(request, 'htmls/error.html', {
            'error': 'Не удалось получить данные о валюте',
            'balance': profile.balance
        })

    nominal = price_data['nominal']
    # Шаг для ввода количества: если номинал > 1, то шаг = номинал, иначе 0.01
    step = nominal if nominal > 1 else Decimal('0.01')
    price = Decimal(str(price_data['rate']))

    if request.method == 'POST':
        form = transactionForm(data=request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.moneyid = ID
            transaction.money = price_data['name']
            transaction.price = price

            count = Decimal(request.POST.get('count', '0'))
            # Проверка кратности номиналу
            if count % step != 0:
                form.add_error('count', f'Количество должно быть кратно {step}')
                return render(request, 'htmls/buy.html', {
                    'name': price_data['name'],
                    'form': form,
                    'balance': profile.balance,
                    'step': step
                })

            transaction.count = count
            transaction.endprice = count * price
            transaction.transaction_type = 'buy'

            if profile.balance >= transaction.endprice:
                profile.balance -= transaction.endprice
                profile.save()
                transaction.save()
                return redirect('history')
            else:
                form.add_error(None, f'⚠️ Недостаточно средств. Требуется: {transaction.endprice} ₽, доступно: {profile.balance} ₽')
        # Если форма невалидна или ошибка, возвращаем страницу с формой
        return render(request, 'htmls/buy.html', {
            'name': price_data['name'],
            'form': form,
            'balance': profile.balance,
            'step': step
        })
    else:
        # GET-запрос – инициализация формы
        initial_data = {
            'user': request.user,
            'moneyid': ID,
            'money': price_data['name'],
            'price': price,
            'endprice': price,
            'count': step,   # по умолчанию минимальное допустимое количество
            'transaction_type': 'buy'
        }
        form = transactionForm(initial=initial_data)
        return render(request, 'htmls/buy.html', {
            'name': price_data['name'],
            'form': form,
            'balance': profile.balance,
            'step': step
        })

@login_required(login_url="login/")
def Sell(request, ID):
    """Продажа валюты с учётом номинала и доступного остатка"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    price_data = get_currency_price(ID)
    if not price_data:
        return render(request, 'htmls/error.html', {
            'error': 'Не удалось получить данные о валюте',
            'balance': profile.balance
        })

    nominal = price_data['nominal']
    step = nominal if nominal > 1 else Decimal('0.01')
    price = Decimal(str(price_data['rate']))

    # Вычисляем доступное количество для продажи
    bought = Transaction.objects.filter(
        user=request.user, moneyid=ID, transaction_type='buy'
    ).aggregate(total=Sum('count'))['total'] or Decimal('0')
    sold = Transaction.objects.filter(
        user=request.user, moneyid=ID, transaction_type='sell'
    ).aggregate(total=Sum('count'))['total'] or Decimal('0')
    available = bought - sold

    if request.method == 'POST':
        form = transactionForm(data=request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.moneyid = ID
            transaction.money = price_data['name']
            transaction.price = price

            count = Decimal(request.POST.get('count', '0'))
            # Проверка кратности номиналу
            if count % step != 0:
                form.add_error('count', f'Количество должно быть кратно {step}')
                return render(request, 'htmls/sell.html', {
                    'name': price_data['name'],
                    'form': form,
                    'balance': profile.balance,
                    'step': step,
                    'available': available
                })

            if count > available:
                form.add_error('count', f'У вас есть только {available} {price_data["name"]} для продажи')
                return render(request, 'htmls/sell.html', {
                    'name': price_data['name'],
                    'form': form,
                    'balance': profile.balance,
                    'step': step,
                    'available': available
                })

            transaction.count = count
            transaction.endprice = count * price
            transaction.transaction_type = 'sell'

            profile.balance += transaction.endprice
            profile.save()
            transaction.save()
            return redirect('history')
        return render(request, 'htmls/sell.html', {
            'name': price_data['name'],
            'form': form,
            'balance': profile.balance,
            'step': step,
            'available': available
        })
    else:
        initial_data = {
            'user': request.user,
            'moneyid': ID,
            'money': price_data['name'],
            'price': price,
            'endprice': price,
            'count': step,
            'transaction_type': 'sell'
        }
        form = transactionForm(initial=initial_data)
        return render(request, 'htmls/sell.html', {
            'name': price_data['name'],
            'form': form,
            'balance': profile.balance,
            'step': step,
            'available': available
        })


def Balance(request):
    """Пополнение баланса"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        income = request.POST.get('income')
        if income:
            try:
                amount = Decimal(income)
                profile.balance += amount
                profile.save()
            except:
                pass
        return redirect('home')
    return render(request, 'htmls/balance.html', {'balance': profile.balance})