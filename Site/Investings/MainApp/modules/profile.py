from django.shortcuts import render, get_list_or_404, redirect, get_object_or_404
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
    return render(request, 'htmls/profile.html', {'time' : dt.datetime.now})

@login_required(login_url="login/")
def History(request):
    tran = Transaction.objects.all()
    if tran.count() != 0:
        tran = get_list_or_404(tran, user=request.user)
    return render(request, 'htmls/history.html', {'hist': tran})

def Buy(request, ID):
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
                'error': 'Не удалось получить данные о валюте'
            })

        form = transactionForm()
        form.fields['user'].initial = request.user
        form.fields['moneyid'].initial = price_data['id']
        form.fields['money'].initial = price_data['name']
        form.fields['price'].initial = round(float(price_data['rate']), 2)
        form.fields['endprice'].initial = round(float(price_data['rate']), 2)

    return render(request, 'htmls/buy.html', {'name': price_data['name'], 'form': form})

def Sell(request, ID):
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
                'error': 'Не удалось получить данные о валюте'
            })

        form = transactionForm()
        form.fields['user'].initial = request.user
        form.fields['moneyid'].initial = price_data['id']
        form.fields['money'].initial = price_data['name']
        form.fields['price'].initial = round(float(price_data['rate']), 2)
        form.fields['endprice'].initial = round(float(price_data['rate']), 2)

    return render(request, 'htmls/sell.html', {'name': price_data['name'], 'form': form})

def Balance(request):
    user = request.user
    return render(request, 'htmls/balance.html', {'balance': user.balance})