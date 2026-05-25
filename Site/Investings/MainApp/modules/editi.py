from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import logout, authenticate
from MainApp.models import userB

def Edit(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = PasswordChangeForm(None)
    bal = userB.objects.get(pk=request.user).balance
    return render(request, 'htmls/edit.html', {'form': form, 'balance': bal})

def Delete(request):
    if request.method == 'POST':
        user = authenticate(username=request.user.username, password=request.POST.get('password'))
        if user is not None and user.is_authenticated:
            logout(request)
            user.delete()
            return redirect('home')
    bal = userB.objects.get(pk=request.user).balance
    return render(request, 'htmls/delete.html', {'balance': bal})