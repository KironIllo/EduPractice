from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm

def Edit(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = PasswordChangeForm(None)
    return render(request, 'htmls/edit.html', {'form': form})
