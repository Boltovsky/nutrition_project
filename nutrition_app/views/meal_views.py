from django.shortcuts import render, redirect, get_object_or_404
from ..models import UserProfile
from .utils import generate_optimized_weekly_meal_plan, _get_recipe_from_session, _adjust_portion


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
        user_data = {
            'goal': request.user.goal,
            'age': request.user.age,
            'weight': request.user.weight,
            'height': request.user.height,
            'activity': request.user.activity_level,
            'gender': request.user.gender
        }

        # Генерируем ОПТИМИЗИРОВАННЫЙ рацион на неделю
        weekly_meal_plan = generate_optimized_weekly_meal_plan(daily_calories)
        request.session['weekly_meal_plan'] = weekly_meal_plan

    else:
        # Для неавторизованных используем сессию
        weekly_meal_plan = request.session.get('weekly_meal_plan')
        daily_calories = request.session.get('daily_calories', 2000)
        user_data = request.session.get('user_data', {})

        if not weekly_meal_plan or not daily_calories:
            return redirect('calculate_calories')

    # Дополнительная информация для отображения точности
    total_week_calories = 0
    total_week_target = 0
    days_with_data = 0

    for day_data in weekly_meal_plan.values():
        if day_data.get('total_calories', 0) > 0:
            total_week_calories += day_data.get('total_calories', 0)
            total_week_target += day_data.get('target_calories',
                                              daily_calories)
            days_with_data += 1

    if days_with_data > 0:
        avg_daily_calories = total_week_calories / days_with_data
        accuracy_percentage = (avg_daily_calories / daily_calories) * 100
    else:
        accuracy_percentage = 0

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

        week_days.append({
            'key': day_key,
            'name': days_russian[day_key],
            'breakfast': breakfast,
            'lunch': lunch,
            'snack': snack,
            'dinner': dinner,
            'total_calories': day_actual,
            'target_calories': day_target,
            'accuracy_percentage': day_accuracy
        })

    context = {
        'week_days': week_days,
        'daily_calories': daily_calories,
        'user_data': user_data,
        'is_authenticated': request.user.is_authenticated,
        'week_accuracy': accuracy_percentage
    }

    return render(request, 'nutrition_app/week_plan.html', context)


def day_plan(request, day_key):
    """Детальный план на конкретный день"""
    weekly_meal_plan = request.session.get('weekly_meal_plan')

    if not weekly_meal_plan or day_key not in weekly_meal_plan:
        return redirect('week_plan')

    if request.user.is_authenticated:
        profile = get_object_or_404(UserProfile, user=request.user)
        daily_calories = profile.daily_calories
        user_data = {
            'goal': request.user.goal,
        }
    else:
        daily_calories = request.session.get('daily_calories', 2000)
        user_data = request.session.get('user_data', {})

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
    if breakfast and day_data.get('breakfast_multiplier', 1) != 1:
        breakfast = _adjust_portion(
            breakfast, day_data.get('breakfast_multiplier', 1))
    if lunch and day_data.get('lunch_multiplier', 1) != 1:
        lunch = _adjust_portion(lunch, day_data.get('lunch_multiplier', 1))
    if snack and day_data.get('snack_multiplier', 1) != 1:
        snack = _adjust_portion(snack, day_data.get('snack_multiplier', 1))
    if dinner and day_data.get('dinner_multiplier', 1) != 1:
        dinner = _adjust_portion(dinner, day_data.get('dinner_multiplier', 1))

    total_calories = day_data.get('total_calories', 0)

    # Вычисляем отклонение и процент выполнения
    deviation = total_calories - daily_calories
    if daily_calories > 0:
        percentage = (total_calories / daily_calories) * 100
    else:
        percentage = 0

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
        'is_authenticated': request.user.is_authenticated
    }

    return render(request, 'nutrition_app/day_plan.html', context)
