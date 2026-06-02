from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import logout, authenticate
from MainApp.models import Profile

def Edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = PasswordChangeForm(user=request.user)  # важно передать user
    return render(request, 'htmls/edit.html', {'form': form, 'balance': profile.balance})

def Delete(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    errorUser = None
    if request.method == 'POST':
        user = authenticate(username=request.user.username, password=request.POST.get('password'))
        if user is not None:
            logout(request)
            user.delete()
            return redirect('home')
        else:
            errorUser = 'WrongPassword'
    return render(request, 'htmls/delete.html', {'balance': profile.balance, 'errorPS': errorUser})