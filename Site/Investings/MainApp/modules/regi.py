from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.core.cache import cache
from .regEmailCode import EmailService
import re

# Инициализация сервиса email
email_service = EmailService(
    smtp_server='smtp.gmail.com',
    smtp_port=587,
    username='dmitrii.mironov.02.07@gmail.com',
    password='wcowvdsphgpsrvgs'
)

def signup(request):
    if request.method == 'POST':
        if 'send_code' in request.POST:
            form = UserCreationForm(request.POST)
            email = request.POST.get('email', '').strip()

            # Валидация email
            if not email:
                error = 'Email не указан'
            elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                error = 'Введите корректный email адрес'
            else:
                error = None

            if error:
                return render(request, 'htmls/signup.html', {'form': form, 'error': error})

            if form.is_valid():
                try:
                    # Отправляем код подтверждения
                    result = email_service.send_verification_code(email)
                    if result['success']:
                        # Сохраняем код в кэше на 10 минут (600 секунд)
                        cache.set(f'verification_code_{email}', result['code'], 600)
                        request.session['pending_email'] = email
                        request.session['pending_form_data'] = {
                            'username': form.cleaned_data['username'],
                            'password1': form.cleaned_data['password1'],
                            'password2': form.cleaned_data['password2']
                        }
                    return render(request, 'htmls/signup.html', {
                    'form': form,
                    'show_verification': True,
                    'email': email })

                except Exception as e:
                    error = f'Критическая ошибка при отправке email: {str(e)}'
                    return render(request, 'htmls/signup.html', {'form': form, 'error': error})
        else:
            error = 'Форма содержит ошибки'
            return render(request, 'htmls/signup.html', {'form': form, 'error': error})



    elif 'verify_code' in request.POST:
        # Проверка кода подтверждения
        email = request.session.get('pending_email')
        form_data = request.session.get('pending_form_data', {})

        if not email or not form_data:
            error = 'Сессия истекла. Пожалуйста, начните регистрацию заново.'
            return render(request, 'htmls/signup.html', {'form': UserCreationForm(), 'error': error})

        code = request.POST.get('verification_code', '').strip()
        stored_code = cache.get(f'verification_code_{email}')

        if stored_code and stored_code == code:
            # Код верен — создаём пользователя
            form = UserCreationForm(form_data)
            if form.is_valid():
                user = form.save(commit=False)
                user.email = email
                user.is_active = True
                user.save()
                login(request, user)
                # Очищаем кэш и сессию
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
    else:
        form = UserCreationForm()
    return render(request, 'htmls/signup.html', {'form': form})
