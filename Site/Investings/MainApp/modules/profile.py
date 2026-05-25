from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import datetime as dt
import requests
import pyinvesting as pi, cbrapi as cbr
@login_required(login_url="login/")
def Profile(request):
    #bfg = cbr.get_currency_code('EUR')
    #bfg = pi.search.Search().tickers("Apple")
    #help(pi.search)
    return render(request, 'htmls/profile.html', {'time' : dt.datetime.now})

@login_required(login_url="login/")
def History(request):
    return render(request, 'htmls/history.html')