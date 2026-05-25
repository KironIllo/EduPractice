from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import datetime as dt

@login_required(login_url="login/")
def Profile(request):
    #bfg = cbr.get_key_rate("2017-09-13", "2017-09-14").head()
    return render(request, 'htmls/profile.html', {'time' : dt.datetime.now})
@login_required(login_url="login/")
def History(request):
    return render(request, 'htmls/history.html')