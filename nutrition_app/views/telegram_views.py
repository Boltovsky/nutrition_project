from django.utils import timezone

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from nutrition_app.forms import TelegramLinkForm
from nutrition_app.models import TelegramUser, TelegramLinkToken


@login_required
def telegram_link(request):
    """Страница привязки Telegram аккаунта"""
    # Проверяем, не привязан ли уже Telegram
    try:
        telegram_user = TelegramUser.objects.get(user=request.user)
        has_telegram = True
        telegram_info = telegram_user
    except TelegramUser.DoesNotExist:
        has_telegram = False
        telegram_info = None

    token = None
    if request.method == 'POST':
        form = TelegramLinkForm(request.POST)
        if form.is_valid():
            # Генерируем токен
            token = form.generate_token(request.user)
            messages.success(
                request, 'Токен для привязки создан! Используйте его в боте в течение 30 минут.')
    else:
        form = TelegramLinkForm()

    # Получаем активный токен если есть
    active_token = TelegramLinkToken.objects.filter(
        user=request.user,
        is_used=False,
        expires_at__gt=timezone.now()
    ).first()

    context = {
        'form': form,
        'token': token,
        'active_token': active_token,
        'has_telegram': has_telegram,
        'telegram_info': telegram_info,
    }

    return render(request, 'nutrition_app/telegram_link.html', context)


@login_required
def telegram_unlink(request):
    """Отвязка Telegram аккаунта"""
    if request.method == 'POST':
        try:
            telegram_user = TelegramUser.objects.get(user=request.user)
            telegram_user.delete()
            messages.success(request, 'Telegram аккаунт успешно отвязан!')
        except TelegramUser.DoesNotExist:
            messages.error(request, 'Telegram аккаунт не привязан!')

    return redirect('telegram_link')
