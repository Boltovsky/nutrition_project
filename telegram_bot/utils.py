from django.utils import timezone
from datetime import datetime, date
from nutrition_app.models import UserMealPlan, CustomUser
from nutrition_app.views.utils import _adjust_portion
from asgiref.sync import sync_to_async


@sync_to_async
def get_user_meal_plan_for_date_async(user, target_date):
    """Асинхронная версия получения плана питания"""
    return get_user_meal_plan_for_date(user, target_date)


@sync_to_async
def get_first_user_async():
    """Асинхронная версия получения первого пользователя"""
    return CustomUser.objects.first()


def get_user_meal_plan_for_date(user, target_date):
    """Получаем индивидуальный план питания пользователя на дату"""
    try:
        meal_plans = UserMealPlan.objects.filter(
            user=user,
            date=target_date
        ).select_related('recipe')

        result = []
        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0

        for plan in meal_plans:
            # Применяем корректировку порции к рецепту
            if plan.portion_multiplier != 1.0:
                adjusted_recipe = _adjust_portion(
                    plan.recipe, float(plan.portion_multiplier))
                calories = adjusted_recipe.calories
                protein = float(adjusted_recipe.protein)
                fat = float(adjusted_recipe.fat)
                carbs = float(adjusted_recipe.carbs)
                description = f"{adjusted_recipe.name} ({plan.portion_multiplier} порц.)"
            else:
                calories = plan.recipe.calories
                protein = float(plan.recipe.protein)
                fat = float(plan.recipe.fat)
                carbs = float(plan.recipe.carbs)
                description = plan.recipe.name

            result.append({
                'meal_type': plan.meal_type,
                'description': description,
                'calories': calories,
                'protein': protein,
                'fat': fat,
                'carbs': carbs,
                'recipe': plan.recipe
            })

            total_calories += calories
            total_protein += protein
            total_fat += fat
            total_carbs += carbs

        return result, total_calories, total_protein, total_fat, total_carbs

    except Exception as e:
        print(f"Error getting user meal plan: {e}")
        return [], 0, 0, 0, 0


async def generate_personal_menu_message_async(user, target_date):
    """Асинхронная версия генерации меню"""
    meal_entries, total_calories, total_protein, total_fat, total_carbs = await get_user_meal_plan_for_date_async(user, target_date)

    if not meal_entries:
        return f"🍽️ На {target_date.strftime('%d.%m.%Y')} у вас нет плана питания.\n\nЗайдите на сайт чтобы составить персональный план!"

    message = f"🍽️ Ваше персональное меню на {target_date.strftime('%d.%m.%Y')}:\n\n"

    meal_types = {
        'breakfast': '🥣 Завтрак',
        'lunch': '🍗 Обед',
        'dinner': '🐟 Ужин',
        'snack': '🍎 Перекус'
    }

    # Группируем по приемам пищи для красивого отображения
    meals_dict = {}
    for entry in meal_entries:
        if entry['meal_type'] not in meals_dict:
            meals_dict[entry['meal_type']] = []
        meals_dict[entry['meal_type']].append(entry)

    # Выводим по порядку приемов пищи
    for meal_type in ['breakfast', 'lunch', 'snack', 'dinner']:
        if meal_type in meals_dict:
            meal_name = meal_types.get(meal_type, '📝 Прием пищи')
            message += f"**{meal_name}:**\n"

            for entry in meals_dict[meal_type]:
                message += f"• {entry['description']} - {entry['calories']} ккал\n"

            message += "\n"

    # Итоги за день
    message += f"📊 **Итого за день:**\n"
    message += f"• Калории: {total_calories} ккал\n"
    message += f"• Белки: {total_protein:.1f}г\n"
    message += f"• Жиры: {total_fat:.1f}г\n"
    message += f"• Углеводы: {total_carbs:.1f}г\n\n"
    message += "💡 Чтобы изменить план питания, зайдите на сайт"

    return message


def generate_personal_menu_message(user, target_date):
    """Генерирует сообщение с персональным меню пользователя"""
    meal_entries, total_calories, total_protein, total_fat, total_carbs = get_user_meal_plan_for_date(
        user, target_date)

    if not meal_entries:
        return f"🍽️ На {target_date.strftime('%d.%m.%Y')} у вас нет плана питания.\n\nЗайдите на сайт чтобы составить персональный план!"

    message = f"🍽️ Ваше персональное меню на {target_date.strftime('%d.%m.%Y')}:\n\n"

    meal_types = {
        'breakfast': '🥣 Завтрак',
        'lunch': '🍗 Обед',
        'dinner': '🐟 Ужин',
        'snack': '🍎 Перекус'
    }

    # Группируем по приемам пищи для красивого отображения
    meals_dict = {}
    for entry in meal_entries:
        if entry['meal_type'] not in meals_dict:
            meals_dict[entry['meal_type']] = []
        meals_dict[entry['meal_type']].append(entry)

    # Выводим по порядку приемов пищи
    for meal_type in ['breakfast', 'lunch', 'snack', 'dinner']:
        if meal_type in meals_dict:
            meal_name = meal_types.get(meal_type, '📝 Прием пищи')
            message += f"**{meal_name}:**\n"

            for entry in meals_dict[meal_type]:
                message += f"• {entry['description']} - {entry['calories']} ккал\n"

            message += "\n"

    # Итоги за день
    message += f"📊 **Итого за день:**\n"
    message += f"• Калории: {total_calories} ккал\n"
    message += f"• Белки: {total_protein:.1f}г\n"
    message += f"• Жиры: {total_fat:.1f}г\n"
    message += f"• Углеводы: {total_carbs:.1f}г\n\n"
    message += "💡 Чтобы изменить план питания, зайдите на сайт"

    return message


def save_weekly_plan_to_db(user, weekly_plan):
    """Сохраняет недельный план из сессии в базу данных"""
    try:
        # Определяем даты для недели (с понедельника по воскресенье)
        today = timezone.now().date()
        start_of_week = today - \
            timezone.timedelta(days=today.weekday())  # Понедельник

        date_mapping = {
            'monday': start_of_week,
            'tuesday': start_of_week + timezone.timedelta(days=1),
            'wednesday': start_of_week + timezone.timedelta(days=2),
            'thursday': start_of_week + timezone.timedelta(days=3),
            'friday': start_of_week + timezone.timedelta(days=4),
            'saturday': start_of_week + timezone.timedelta(days=5),
            'sunday': start_of_week + timezone.timedelta(days=6),
        }

        # Удаляем старые планы на эту неделю
        dates = list(date_mapping.values())
        UserMealPlan.objects.filter(user=user, date__in=dates).delete()

        # Сохраняем новые планы
        for day_key, day_data in weekly_plan.items():
            target_date = date_mapping.get(day_key)
            if not target_date:
                continue

            # Сохраняем завтрак
            if day_data.get('breakfast_id'):
                UserMealPlan.objects.create(
                    user=user,
                    date=target_date,
                    meal_type='breakfast',
                    recipe_id=day_data['breakfast_id'],
                    portion_multiplier=day_data.get(
                        'breakfast_multiplier', 1.0)
                )

            # Сохраняем обед
            if day_data.get('lunch_id'):
                UserMealPlan.objects.create(
                    user=user,
                    date=target_date,
                    meal_type='lunch',
                    recipe_id=day_data['lunch_id'],
                    portion_multiplier=day_data.get('lunch_multiplier', 1.0)
                )

            # Сохраняем перекус
            if day_data.get('snack_id'):
                UserMealPlan.objects.create(
                    user=user,
                    date=target_date,
                    meal_type='snack',
                    recipe_id=day_data['snack_id'],
                    portion_multiplier=day_data.get('snack_multiplier', 1.0)
                )

            # Сохраняем ужин
            if day_data.get('dinner_id'):
                UserMealPlan.objects.create(
                    user=user,
                    date=target_date,
                    meal_type='dinner',
                    recipe_id=day_data['dinner_id'],
                    portion_multiplier=day_data.get('dinner_multiplier', 1.0)
                )

        return True
    except Exception as e:
        print(f"Error saving weekly plan to DB: {e}")
        return False
