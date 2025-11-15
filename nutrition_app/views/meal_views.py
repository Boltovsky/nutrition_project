from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from ..models import UserProfile
from .utils import generate_optimized_weekly_meal_plan, _get_recipe_from_session, _adjust_portion, optimize_daily_calories


def calculate_calories(request):
    """Страница расчета калорий - только для неавторизованных пользователей"""
    if request.user.is_authenticated:
        # Для авторизованных пользователей используем данные из профиля
        return redirect('week_plan')

    if request.method == 'POST':
        # Получаем данные из формы
        gender = request.POST.get('gender')
        age = int(request.POST.get('age'))
        weight = float(request.POST.get('weight'))
        height = float(request.POST.get('height'))
        activity = request.POST.get('activity')
        goal = request.POST.get('goal')

        # Расчет BMR (базового метаболизма)
        if gender == 'male':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        # Коэффициенты активности
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'high': 1.725,
            'extreme': 1.9
        }

        # Расчет суточной калорийности
        daily_calories = bmr * activity_multipliers.get(activity, 1.2)

        # Корректировка по цели
        if goal == 'loss':
            daily_calories *= 0.8  # Дефицит 20%
        elif goal == 'gain':
            daily_calories *= 1.1  # Профицит 10%

        daily_calories = round(daily_calories)

        # Сохраняем данные в сессии
        request.session['daily_calories'] = daily_calories
        request.session['user_data'] = {
            'gender': gender,
            'age': age,
            'weight': weight,
            'height': height,
            'activity': activity,
            'goal': goal
        }

        # Генерируем рацион на неделю
        weekly_meal_plan = generate_optimized_weekly_meal_plan(daily_calories)
        request.session['weekly_meal_plan'] = weekly_meal_plan

        return redirect('week_plan')

    return render(request, 'nutrition_app/calculate_calories.html')


def week_plan(request):
    """Страница с планом на неделю"""
    if request.user.is_authenticated:
        # Для авторизованных пользователей используем данные из профиля
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        daily_calories = profile.daily_calories
        # Определяем начало текущей недели
        today = timezone.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        weekly_plan_key = f'weekly_plan_{current_week_start}_{request.user.id}'

        # 🔥 ВАЖНО: Проверяем есть ли уже план в сессии
        if weekly_plan_key not in request.session:
            # Если нет - генерируем новый
            weekly_meal_plan = generate_optimized_weekly_meal_plan(
                daily_calories)
            request.session[weekly_plan_key] = weekly_meal_plan
            request.session['weekly_plan_generated'] = today.isoformat()
        else:
            # Используем существующий план из сессии
            weekly_meal_plan = request.session[weekly_plan_key]
        user_data = {
            'goal': request.user.goal,
            'age': request.user.age,
            'weight': request.user.weight,
            'height': request.user.height,
            'activity': request.user.activity_level,
            'gender': request.user.gender
        }

        # Определяем начало текущей недели (понедельник)
        today = timezone.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        weekly_plan_key = f'weekly_plan_{current_week_start}_{request.user.id}'

        # Проверяем, есть ли сохраненный план на текущую неделю
        if weekly_plan_key not in request.session:
            # Генерируем НОВЫЙ оптимизированный рацион на неделю
            weekly_meal_plan = generate_optimized_weekly_meal_plan(
                daily_calories)
            request.session[weekly_plan_key] = weekly_meal_plan
            request.session['weekly_plan_generated'] = today.isoformat()
            plan_generated_new = True
        else:
            # Используем сохраненный план
            weekly_meal_plan = request.session[weekly_plan_key]
            plan_generated_new = False

    else:
        # Для неавторизованных используем сессию (старая логика)
        weekly_meal_plan = request.session.get('weekly_meal_plan')
        daily_calories = request.session.get('daily_calories', 2000)
        user_data = request.session.get('user_data', {})
        plan_generated_new = False

        if not weekly_meal_plan or not daily_calories:
            return redirect('calculate_calories')

    # Дополнительная информация для отображения точности
    total_week_calories = 0
    total_week_target = 0
    days_with_data = 0
    days_within_tolerance = 0  # Дни в пределах ±5%

    for day_data in weekly_meal_plan.values():
        day_target = day_data.get('target_calories', daily_calories)
        day_actual = day_data.get('total_calories', 0)

        if day_actual > 0:
            total_week_calories += day_actual
            total_week_target += day_target
            days_with_data += 1

            # Проверяем, в пределах ли 5% допуска
            tolerance = day_target * 0.05
            if abs(day_actual - day_target) <= tolerance:
                days_within_tolerance += 1

    if days_with_data > 0:
        avg_daily_calories = total_week_calories / days_with_data
        accuracy_percentage = (avg_daily_calories / daily_calories) * 100
        tolerance_percentage = (days_within_tolerance / days_with_data) * 100
    else:
        accuracy_percentage = 0
        tolerance_percentage = 0

    # Русские названия дней недели
    days_russian = {
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота',
        'sunday': 'Воскресенье'
    }

    # Восстанавливаем рецепты из ID с учетом скорректированных порций
    week_days = []
    for day_key, day_data in weekly_meal_plan.items():
        breakfast = _get_recipe_from_session(day_data.get('breakfast_id'))
        lunch = _get_recipe_from_session(day_data.get('lunch_id'))
        snack = _get_recipe_from_session(day_data.get('snack_id'))
        dinner = _get_recipe_from_session(day_data.get('dinner_id'))

        # Применяем корректировку порций к рецептам
        if breakfast and day_data.get('breakfast_multiplier', 1) != 1:
            breakfast = _adjust_portion(
                breakfast, day_data.get('breakfast_multiplier', 1))
        if lunch and day_data.get('lunch_multiplier', 1) != 1:
            lunch = _adjust_portion(lunch, day_data.get('lunch_multiplier', 1))
        if snack and day_data.get('snack_multiplier', 1) != 1:
            snack = _adjust_portion(snack, day_data.get('snack_multiplier', 1))
        if dinner and day_data.get('dinner_multiplier', 1) != 1:
            dinner = _adjust_portion(
                dinner, day_data.get('dinner_multiplier', 1))

        day_target = day_data.get('target_calories', daily_calories)
        day_actual = day_data.get('total_calories', 0)
        day_accuracy = (day_actual / day_target) * 100 if day_target > 0 else 0

        # Определяем статус точности
        tolerance = day_target * 0.05
        if abs(day_actual - day_target) <= tolerance:
            accuracy_status = 'success'
            accuracy_text = 'В норме (±5%)'
        elif day_actual < day_target:
            accuracy_status = 'warning'
            accuracy_text = 'Ниже нормы'
        else:
            accuracy_status = 'danger'
            accuracy_text = 'Выше нормы'

        week_days.append({
            'key': day_key,
            'name': days_russian[day_key],
            'breakfast': breakfast,
            'lunch': lunch,
            'snack': snack,
            'dinner': dinner,
            'total_calories': day_actual,
            'target_calories': day_target,
            'accuracy_percentage': day_accuracy,
            'accuracy_status': accuracy_status,
            'accuracy_text': accuracy_text
        })

    context = {
        'week_days': week_days,
        'daily_calories': daily_calories,
        'user_data': user_data,
        'is_authenticated': request.user.is_authenticated,
        'week_accuracy': accuracy_percentage,
        'tolerance_percentage': tolerance_percentage,
        'plan_generated_new': plan_generated_new,
        'current_week_start': current_week_start if request.user.is_authenticated else None
    }

    return render(request, 'nutrition_app/week_plan.html', context)


def day_plan(request, day_key):
    """Детальный план на конкретный день"""
    if request.user.is_authenticated:
        # Для авторизованных пользователей
        profile = get_object_or_404(UserProfile, user=request.user)
        daily_calories = profile.daily_calories
        user_data = {
            'goal': request.user.goal,
        }

        # Определяем начало текущей недели (понедельник)
        today = timezone.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        weekly_plan_key = f'weekly_plan_{current_week_start}_{request.user.id}'

        # Получаем план из сессии
        weekly_meal_plan = request.session.get(weekly_plan_key)

        if not weekly_meal_plan:
            # Если плана нет в сессии, генерируем новый
            weekly_meal_plan = generate_optimized_weekly_meal_plan(
                daily_calories)
            request.session[weekly_plan_key] = weekly_meal_plan
    else:
        # Для неавторизованных используем сессию (старая логика)
        weekly_meal_plan = request.session.get('weekly_meal_plan')
        daily_calories = request.session.get('daily_calories', 2000)
        user_data = request.session.get('user_data', {})

    # Проверяем, есть ли план и запрошенный день
    if not weekly_meal_plan or day_key not in weekly_meal_plan:
        messages.error(request, f'План на выбранный день не найден')
        return redirect('week_plan')

    # Русские названия дней недели
    days_russian = {
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота',
        'sunday': 'Воскресенье'
    }

    day_data = weekly_meal_plan[day_key]

    # Восстанавливаем рецепты из ID с учетом скорректированных порций
    breakfast = _get_recipe_from_session(day_data.get('breakfast_id'))
    lunch = _get_recipe_from_session(day_data.get('lunch_id'))
    snack = _get_recipe_from_session(day_data.get('snack_id'))
    dinner = _get_recipe_from_session(day_data.get('dinner_id'))

    # Применяем корректировку порций к рецептам
    if all([breakfast, lunch, snack, dinner]):
        breakfast, lunch, snack, dinner, optimized_calories = optimize_daily_calories(
            breakfast, lunch, snack, dinner, float(daily_calories)
        )
        total_calories = optimized_calories

        # 🔥 ВАЖНО: Берем множители ИЗ СКОРРЕКТИРОВАННЫХ РЕЦЕПТОВ
        breakfast_multiplier = getattr(breakfast, 'portion_multiplier', 1.0)
        lunch_multiplier = getattr(lunch, 'portion_multiplier', 1.0)
        snack_multiplier = getattr(snack, 'portion_multiplier', 1.0)
        dinner_multiplier = getattr(dinner, 'portion_multiplier', 1.0)

        # Обновляем данные дня
        day_data.update({
            'breakfast_multiplier': breakfast_multiplier,
            'lunch_multiplier': lunch_multiplier,
            'snack_multiplier': snack_multiplier,
            'dinner_multiplier': dinner_multiplier,
            'total_calories': total_calories
        })
    else:
        total_calories = day_data.get('total_calories', 0)
        # Используем множители из сохраненных данных
        breakfast_multiplier = day_data.get('breakfast_multiplier', 1.0)
        lunch_multiplier = day_data.get('lunch_multiplier', 1.0)
        snack_multiplier = day_data.get('snack_multiplier', 1.0)
        dinner_multiplier = day_data.get('dinner_multiplier', 1.0)

    # Вычисляем отклонение и процент выполнения
    deviation = total_calories - daily_calories
    if daily_calories > 0:
        percentage = (total_calories / daily_calories) * 100
    else:
        percentage = 0
    request.session['current_day'] = day_key
    context = {
        'day_key': day_key,
        'day_name': days_russian[day_key],
        'breakfast': breakfast,
        'lunch': lunch,
        'snack': snack,
        'dinner': dinner,
        'total_calories': total_calories,
        'daily_calories': daily_calories,
        'deviation': deviation,
        'percentage': percentage,
        'user_data': user_data,
        'is_authenticated': request.user.is_authenticated,
        'breakfast_multiplier': breakfast_multiplier,
        'lunch_multiplier': lunch_multiplier,
        'snack_multiplier': snack_multiplier,
        'dinner_multiplier': dinner_multiplier,
    }

    return render(request, 'nutrition_app/day_plan.html', context)


def refresh_weekly_plan(request):
    """Принудительное обновление плана на неделю"""
    # 🔥 ПРИНУДИТЕЛЬНАЯ ПЕРЕЗАГРУЗКА ВСЕХ МОДУЛЕЙ
    import sys
    import importlib

    # Удаляем все наши модули из кэша
    modules_to_reload = []
    for module_name in list(sys.modules.keys()):
        if 'nutrition_app' in module_name or 'utils' in module_name:
            modules_to_reload.append(module_name)

    for module_name in modules_to_reload:
        if module_name in sys.modules:
            del sys.modules[module_name]

    # 🔥 ПЕРЕИМПОРТИРУЕМ ВСЕ С НУЛЯ
    from nutrition_app.views.utils import generate_optimized_weekly_meal_plan, calculate_user_calories

    if request.user.is_authenticated:
        daily_calories = calculate_user_calories(request.user)

        today = timezone.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        weekly_plan_key = f'weekly_plan_{current_week_start}_{request.user.id}'

        # Удаляем старый план
        if weekly_plan_key in request.session:
            del request.session[weekly_plan_key]

        # Генерируем новый план
        weekly_meal_plan = generate_optimized_weekly_meal_plan(daily_calories)
        request.session[weekly_plan_key] = weekly_meal_plan
        request.session.save()

        messages.success(request, 'Меню на неделю успешно обновлено!')

    return redirect('week_plan')
