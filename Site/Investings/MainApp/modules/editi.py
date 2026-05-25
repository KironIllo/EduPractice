from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import logout, authenticate

def Edit(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = PasswordChangeForm(None)
    return render(request, 'htmls/edit.html', {'form': form})

def Delete(request):
    if request.method == 'POST':
        user = authenticate(username=request.user.username, password=request.POST.get('password'))
        if user is not None and user.is_authenticated:
            logout(request)
            user.delete()
            return redirect('home')
    return render(request, 'htmls/delete.html')