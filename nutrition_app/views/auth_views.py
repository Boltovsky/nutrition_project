from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import UserProfile, CustomUser
from ..forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .utils import get_motivational_message, calculate_user_calories


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Создаем профиль пользователя
            UserProfile.objects.create(user=user)

            # Автоматический вход после регистрации
            login(request, user)
            messages.success(
                request, f'Добро пожаловать, {user.first_name}! Регистрация прошла успешно!')
            return redirect('profile_setup')
    else:
        form = CustomUserCreationForm()

    return render(request, 'nutrition_app/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        # 🔥 ИСПОЛЬЗУЕМ ПРОСТУЮ АУТЕНТИФИКАЦИЮ БЕЗ ФОРМЫ
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                # 🔥 УБИРАЕМ СООБЩЕНИЕ ОБ УСПЕШНОМ ВХОДЕ
                # messages.success(request, f'С возвращением, {user.first_name}!')

                # Если у пользователя заполнены данные, сразу переходим к плану
                if hasattr(user, 'age') and user.age and user.weight and user.height:
                    return redirect('week_plan')
                else:
                    return redirect('profile_setup')
            else:
                # 🔥 ИСПОЛЬЗУЕМ КАСТОМНОГО ПОЛЬЗОВАТЕЛЯ
                if not CustomUser.objects.filter(username=username).exists():
                    messages.error(
                        request, '❌ Пользователь с таким логином не найден')
                else:
                    messages.error(request, '❌ Неверный пароль')

                # 🔥 ВОЗВРАЩАЕМ С СОХРАНЕННЫМ ЛОГИНОМ
                return render(request, 'nutrition_app/login.html', {'username': username})

    # 🔥 УБИРАЕМ ФОРМУ И ВОЗВРАЩАЕМ ПУСТОЙ ШАБЛОН
    return render(request, 'nutrition_app/login.html')


def user_logout(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('index')


@login_required
def profile_setup(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()

            # Рассчитываем калории на основе данных пользователя
            daily_calories = calculate_user_calories(user)

            # Сохраняем в профиль
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.daily_calories = daily_calories
            profile.motivation_message = get_motivational_message(user)
            profile.save()

            messages.success(
                request, 'Профиль успешно обновлен! Расчет калорий выполнен автоматически.')
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'nutrition_app/profile_setup.html', {'form': form})


@login_required
def dashboard(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    motivational_message = profile.motivation_message or get_motivational_message(
        request.user)

    context = {
        'user': request.user,
        'profile': profile,
        'motivational_message': motivational_message,
    }

    return render(request, 'nutrition_app/dashboard.html', context)
