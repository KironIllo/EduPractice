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
    return render(request, 'htmls/profile.html', {'time': dt.datetime.now, 'balance': profile.balance})

@login_required(login_url="login/")
def History(request):
    transactions = Transaction.objects.filter(user=request.user)
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
            transaction.price = round(float(transaction.price), 2)
            transaction.endprice = round(transaction.count * transaction.price, 2)
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
            'price': round(float(price_data['rate']), 2),
            'endprice': round(float(price_data['rate']), 2),
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
            transaction.price = abs(round(float(transaction.price), 2))
            transaction.endprice = abs(round(transaction.count * transaction.price, 2))
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
            'price': round(float(price_data['rate']), 2),
            'endprice': round(float(price_data['rate']), 2),
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