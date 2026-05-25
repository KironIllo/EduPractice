from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
import datetime as dt
#import cbrapi as cbr

def Main(request):
    import pandas as pd
    date = dt.datetime.now()
    url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date.strftime("%d")}/{date.strftime("%m")}/{date.strftime("%Y")}'
    prices = pd.read_xml(url, encoding='Windows-1251').to_dict()
    pric = []
    for i in prices["ID"]:
        pric += [[prices['Name'][i], prices['VunitRate'][i]]]
    print(pric[0])
    return render(request, 'htmls/main.html', {'prices': pric})