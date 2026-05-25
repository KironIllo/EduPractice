from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import datetime as dt
import cbrapi as cbr
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'htmls/signup.html', {'form': form})

def login_view(request):
    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
    return render(request, 'htmls/login.html', {'form': form})
def logout_view(request):
    logout(request)
    return redirect('/')

def Main(request):
    return render(request, 'htmls/main.html')
def Profile(request):
    #bfg = cbr.get_key_rate("2017-09-13", "2017-09-14").head()
    if request.user.is_authenticated:
        #return redirect('profile')
        return render(request, 'htmls/profile.html', { 'time' : dt.datetime.now})
    return redirect('/login')
def History(request):
    return render(request, 'htmls/history.html')

def GetPrices():
    return 0
def Notifications():
    return 0