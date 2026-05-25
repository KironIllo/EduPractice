from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from MainApp.forms import transactionForm
import datetime as dt
import requests
import pyinvesting as pi
@login_required(login_url="login/")
def Profile(request):
    return render(request, 'htmls/profile.html', {'time' : dt.datetime.now})

@login_required(login_url="login/")
def History(request):
    return render(request, 'htmls/history.html')

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
    url = f'https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={day}/{month}/{year}&date_req2={day}/{month}/{year}&VAL_NM_RQ={ID}'
    url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={day}/{month}/{year}'
    prices = pd.read_xml(url, encoding='Windows-1251').to_dict()
    pric = []
    for i in prices["ID"]:
        if prices['ID'][i] == ID:
            pric += [prices['ID'][i], prices['Name'][i], prices['VunitRate'][i]]
    form = transactionForm()
    return render(request, 'htmls/buy.html',{'name':pric, 'form':form})