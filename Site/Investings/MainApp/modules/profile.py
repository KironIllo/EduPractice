from django.shortcuts import render, get_list_or_404, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from MainApp.models import Transaction, userB
from MainApp.forms import transactionForm
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
            form.save()
            return redirect('history')
    
    import pandas as pd
    date = dt.datetime.now()
    day = date.strftime("%d")
    month = date.strftime("%m")
    year = date.strftime("%Y")

    url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={day}/{month}/{year}'

    response = requests.get(url, verify=False, timeout=10)
    response.raise_for_status()  # Проверяем статус ответа

    from io import BytesIO
    prices = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()

    #prices = pd.read_xml(url, encoding='Windows-1251').to_dict()

    pric = []
    for i in prices["ID"]:
        if prices['ID'][i] == ID:
            pric += [prices['ID'][i], prices['Name'][i], prices['VunitRate'][i]]
    form = transactionForm()
    form['user'].initial = request.user
    form['moneyid'].initial = pric[0]
    form['money'].initial = pric[1]
    form['price'].initial = pric[2].replace(',', '.')
    form['endprice'].initial = form['price'].initial
    return render(request, 'htmls/buy.html',{'name':pric[1], 'form':form})

def Sell(request, ID):
    if request.method == 'POST':
        form = transactionForm(data=request.POST)
        if form.is_valid():
            tran = form.save(commit=False)
            tran.price = '-'+request.POST.get('price')
            tran.endprice = '-'+request.POST.get('endprice')
            tran.save()
            return redirect('history')
    
    import pandas as pd
    date = dt.datetime.now()
    day = date.strftime("%d")
    month = date.strftime("%m")
    year = date.strftime("%Y")

    url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={day}/{month}/{year}'

    response = requests.get(url, verify=False, timeout=10)
    response.raise_for_status()  # Проверяем статус ответа

    from io import BytesIO
    prices = pd.read_xml(BytesIO(response.content), encoding='Windows-1251').to_dict()

    #prices = pd.read_xml(url, encoding='Windows-1251').to_dict()

    pric = []
    for i in prices["ID"]:
        if prices['ID'][i] == ID:
            pric += [prices['ID'][i], prices['Name'][i], prices['VunitRate'][i]]
    form = transactionForm()
    form['user'].initial = request.user
    form['moneyid'].initial = pric[0]
    form['money'].initial = pric[1]
    form['price'].initial = pric[2].replace(',', '.')
    form['endprice'].initial = form['price'].initial
    return render(request, 'htmls/buy.html',{'name':pric[1], 'form':form})

def Balance(request):
    ua = get_object_or_404(userB.objects.all(), pk=request.user)
    print(ua.balance)
    return render(request,'htmls/balance.html')