from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import UserProfile
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
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(
                    request, f'С возвращением, {user.first_name}!')

                # Если у пользователя заполнены данные, сразу переходим к плану
                if user.age and user.weight and user.height:
                    return redirect('week_plan')
                else:
                    return redirect('profile_setup')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'nutrition_app/login.html', {'form': form})


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
