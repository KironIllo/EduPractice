from django.shortcuts import render, get_list_or_404, redirect
from django.contrib.auth.decorators import login_required
from MainApp.models import Transaction, userB
from MainApp.forms import transactionForm
from MainApp.modules.prices import get_currency_price
import datetime as dt
import requests
import pyinvesting as pi
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@login_required(login_url="login/")
def Profile(request):
    bal = userB.objects.get(pk=request.user).balance
    return render(request, 'htmls/profile.html', {'time' : dt.datetime.now, 'balance': bal})

@login_required(login_url="login/")
def History(request):
    tran = Transaction.objects.all()
    if tran.count() != 0:
        tran = get_list_or_404(tran, user=request.user)
    bal = userB.objects.get(pk=request.user).balance
    return render(request, 'htmls/history.html', {'hist': tran, 'balance': bal})

def Buy(request, ID):
    bal = userB.objects.get(pk=request.user).balance
    if request.method == 'POST':
        form = transactionForm(data=request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user

            # Округляем до 2 знаков после запятой
            transaction.price = round(float(transaction.price), 2)
            transaction.endprice = round(transaction.count * transaction.price, 2)

            # Обновляем баланс пользователя (покупка — трата денег)
            user = request.user
            user.balance -= transaction.endprice
            user.save()

            transaction.save()
            return redirect('history')
    else:
        # Получаем актуальные цены
        price_data = get_currency_price(ID)
        if not price_data:
            return render(request, 'htmls/error.html', {
                'error': 'Не удалось получить данные о валюте',
                'balance': bal
            })

        form = transactionForm()
        form.fields['user'].initial = request.user
        form.fields['moneyid'].initial = price_data['id']
        form.fields['money'].initial = price_data['name']
        form.fields['price'].initial = round(float(price_data['rate']), 2)
        form.fields['endprice'].initial = round(float(price_data['rate']), 2)

    return render(request, 'htmls/buy.html', {'name': price_data['name'], 'form': form, 'balance': bal})

def Sell(request, ID):
    bal = userB.objects.get(pk=request.user).balance
    if request.method == 'POST':
        form = transactionForm(data=request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user

            # Округляем до 2 знаков после запятой
            transaction.price = abs(round(float(transaction.price), 2))
            transaction.endprice = abs(round(transaction.count * transaction.price, 2))

            # Обновляем баланс пользователя (продажа — получение денег)
            user = request.user
            user.balance += transaction.endprice
            user.save()

            transaction.save()
            return redirect('history')
    else:
        price_data = get_currency_price(ID)
        if not price_data:
            return render(request, 'htmls/error.html', {
                'error': 'Не удалось получить данные о валюте',
                'balance': bal
            })

        form = transactionForm()
        form.fields['user'].initial = request.user
        form.fields['moneyid'].initial = price_data['id']
        form.fields['money'].initial = price_data['name']
        form.fields['price'].initial = round(float(price_data['rate']), 2)
        form.fields['endprice'].initial = round(float(price_data['rate']), 2)

    return render(request, 'htmls/sell.html', {'name': price_data['name'], 'form': form, 'balance': bal})

def Balance(request):
    user = userB.objects.get(pk=request.user)
    if request.method == 'POST':
        print(request.POST)
        if request.POST['income']:
            user.balance += int(request.POST['income'])
            user.save()
            return redirect('/')

    return render(request, 'htmls/balance.html', {'balance': user.balance})