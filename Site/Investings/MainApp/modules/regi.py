from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.core.cache import cache
from .regEmailCode import EmailService
from MainApp.forms import userForm
import re

email_service = EmailService(
    smtp_server='smtp.gmail.com',
    smtp_port=587,
    username='dmitrii.mironov.02.07@gmail.com',
    password='wcowvdsphgpsrvgs'
)

def send_verification_code(email, request):
    """Отправляет код и сохраняет в кэш. Возвращает True/False и сообщение."""
    try:
        result = email_service.send_verification_code(email)
        if result['success']:
            cache.set(f'verification_code_{email}', result['code'], 600)
            return True, None
        else:
            return False, f'Ошибка отправки: {result.get("error", "Неизвестная ошибка")}'
    except Exception as e:
        return False, f'Критическая ошибка: {str(e)}'

def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        form = UserCreationForm(request.POST)
        # Обработка повторной отправки кода
        if 'resend_code' in request.POST:
            # Берём email из сессии, если есть
            email = request.session.get('pending_email') or email
            if not email:
                error = 'Email не найден. Начните регистрацию заново.'
                return render(request, 'htmls/signup.html', {'form': form, 'error': error})

            success, msg = send_verification_code(email, request)
            if success:
                return render(request, 'htmls/signup.html', {
                    'form': form,
                    'show_verification': True,
                    'email': email,
                    'message': 'Новый код отправлен на ваш email.'
                })
            else:
                return render(request, 'htmls/signup.html', {
                    'form': form,
                    'show_verification': True,
                    'email': email,
                    'error': msg
                })

        # Обработка первой отправки кода
        if 'send_code' in request.POST:
            if not email:
                error = 'Email не указан'
                return render(request, 'htmls/signup.html', {'form': form, 'error': error})
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                error = 'Введите корректный email адрес'
                return render(request, 'htmls/signup.html', {'form': form, 'error': error})

            if form.is_valid():
                success, msg = send_verification_code(email, request)
                if success:
                    request.session['pending_email'] = email
                    request.session['pending_form_data'] = {
                        'username': form.cleaned_data['username'],
                        'password1': form.cleaned_data['password1'],
                        'password2': form.cleaned_data['password2'],
                    }
                    return render(request, 'htmls/signup.html', {
                        'form': form,
                        'show_verification': True,
                        'email': email,
                    })
                else:
                    return render(request, 'htmls/signup.html', {'form': form, 'error': msg})
            else:
                return render(request, 'htmls/signup.html', {'form': form, 'error': 'Пожалуйста, исправьте ошибки в форме'})

        # Обработка проверки кода
        elif 'verify_code' in request.POST:
            email = request.session.get('pending_email')
            form_data = request.session.get('pending_form_data', {})

            if not email or not form_data:
                error = 'Сессия истекла. Начните регистрацию заново.'
                return render(request, 'htmls/signup.html', {'form': UserCreationForm(), 'error': error})

            code = request.POST.get('verification_code', '').strip()
            stored_code = cache.get(f'verification_code_{email}')
            if stored_code and stored_code == code:
                form = userForm(form_data)
                if form.is_valid():
                    user = form.save(commit=False)
                    user.username = form_data['username']
                    user.email = email
                    user.is_active = True
                    user.balance = 0
                    user.save()
                    login(request, user)
                    cache.delete(f'verification_code_{email}')
                    del request.session['pending_email']
                    del request.session['pending_form_data']
                    return redirect('/')
                else:
                    error = 'Ошибка при создании пользователя'
            else:
                error = 'Неверный код подтверждения или он истёк'

            return render(request, 'htmls/signup.html', {
                'form': UserCreationForm(form_data),
                'show_verification': True,
                'email': email,
                'error': error
            })

        # Неизвестный POST
        else:
            error = 'Неизвестный запрос.'
            return render(request, 'htmls/signup.html', {'form': form, 'error': error})

    else:  # GET
        form = UserCreationForm()
        return render(request, 'htmls/signup.html', {'form': form})