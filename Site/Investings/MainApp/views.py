from django.shortcuts import render
import datetime as dt
import cbrapi as cbr

def Main(request):
    return render(request, 'htmls/main.html')
def Profile(request):
    #bfg = cbr.get_key_rate("2017-09-13", "2017-09-14").head()
    return render(request, 'htmls/profile.html', { 'time' : dt.datetime.now})
def History(request):
    return render(request, 'htmls/history.html')

def GetPrices():
    return 0
def Notifications():
    return 0