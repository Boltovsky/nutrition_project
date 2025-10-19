import random
import re
from decimal import Decimal
from ..models import Recipe


def get_motivational_message(user):
    messages = [
        f"Привет, {user.first_name}! Ты на правильном пути к здоровому образу жизни! 🚀",
        f"{user.first_name}, каждый твой шаг к правильному питанию - это инвестиция в твое здоровье! 💪",
        f"Отличный день для здоровых привычек, {user.first_name}! Ты молодец! 🌟",
        f"{user.first_name}, помни: маленькие шаги каждый день приводят к большим результатам! 📈",
        f"Ты становишься лучше с каждым днем, {user.first_name}! Гордимся тобой! 🏆",
        f"{user.first_name}, твое упорство вдохновляет! Продолжай в том же духе! 🔥",
        f"Здоровое питание - это твой суперсил, {user.first_name}! Используй его мудро! 🦸‍♂️",
    ]
    return random.choice(messages)


def calculate_user_calories(user):
    """Расчет калорий для пользователя на основе его данных"""
    if user.age and user.weight and user.height:
        # Расчет BMR (базового метаболизма)
        if user.gender == 'male':
            bmr = (10 * user.weight) + \
                (6.25 * user.height) - (5 * user.age) + 5
        else:
            bmr = (10 * user.weight) + \
                (6.25 * user.height) - (5 * user.age) - 161

        # Коэффициенты активности
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'high': 1.725,
            'extreme': 1.9
        }

        # Расчет суточной калорийности
        daily_calories = bmr * \
            activity_multipliers.get(user.activity_level, 1.2)

        # Корректировка по цели
        if user.goal == 'loss':
            daily_calories *= 0.8  # Дефицит 20%
        elif user.goal == 'gain':
            daily_calories *= 1.1  # Профицит 10%

        return round(daily_calories)

    return 2000  # Значение по умолчанию


def _parse_ingredient_amount(ingredient_text):
    """Парсит количество ингредиента из текста"""
    # Паттерны для поиска чисел с единицами измерения
    patterns = [
        r'(\d+\.?\d*)\s*(г|кг|мл|л|шт|ч\.л|ст\.л|зубч|пучок|щепотка)',
        r'(\d+\.?\d*)\s*гр',
        r'(\d+\.?\d*)\s*грамм',
        r'(\d+\.?\d*)\s*миллилитр',
    ]

    for pattern in patterns:
        match = re.search(pattern, ingredient_text, re.IGNORECASE)
        if match:
            amount = float(match.group(1))
            unit = match.group(2)
            return amount, unit, match.start(), match.end()

    return None, None, None, None


def _adjust_ingredient_amount(ingredient_text, multiplier):
    """Корректирует количество ингредиента согласно множителю порции"""
    amount, unit, start, end = _parse_ingredient_amount(ingredient_text)

    if amount is not None:
        new_amount = amount * multiplier
        # Округляем в зависимости от величины
        if new_amount < 1:
            new_amount = round(new_amount, 2)
        elif new_amount < 10:
            new_amount = round(new_amount, 1)
        else:
            new_amount = round(new_amount)

        # Форматируем вывод
        if new_amount.is_integer():
            new_amount = int(new_amount)

        # Заменяем старое количество на новое
        adjusted_text = (ingredient_text[:start] +
                         f"{new_amount}{unit}" +
                         ingredient_text[end:])
        return adjusted_text

    return ingredient_text


def _adjust_recipe_ingredients(ingredients_text, multiplier):
    """Корректирует все ингредиенты рецепта согласно множителю порции"""
    if multiplier == 1:
        return ingredients_text

    ingredients_list = ingredients_text.split('\n')
    adjusted_ingredients = []

    for ingredient in ingredients_list:
        ingredient = ingredient.strip()
        if ingredient:
            adjusted_ingredient = _adjust_ingredient_amount(
                ingredient, multiplier)
            adjusted_ingredients.append(adjusted_ingredient)

    return '\n'.join(adjusted_ingredients)


def _adjust_portion(recipe, multiplier):
    """Создает копию рецепта с увеличенной/уменьшенной порцией и скорректированными ингредиентами"""
    if isinstance(multiplier, float):
        multiplier = Decimal(str(multiplier))

    # Корректируем ингредиенты
    adjusted_ingredients = _adjust_recipe_ingredients(
        recipe.ingredients, float(multiplier))

    adjusted_recipe = Recipe(
        id=recipe.id,
        name=recipe.name,
        meal_type=recipe.meal_type,
        calories=round(recipe.calories * multiplier),
        protein=round(recipe.protein * multiplier, 1),
        fat=round(recipe.fat * multiplier, 1),
        carbs=round(recipe.carbs * multiplier, 1),
        ingredients=adjusted_ingredients,
        instructions=recipe.instructions,
        image=recipe.image,
        cooking_time=recipe.cooking_time,
        difficulty=recipe.difficulty,
        base_portion=f"{float(multiplier):.1f} порции" if multiplier != Decimal(
            '1') else "1 порция"
    )

    adjusted_recipe.portion_multiplier = float(multiplier)
    adjusted_recipe.original_calories = recipe.calories
    adjusted_recipe.original_ingredients = recipe.ingredients
    return adjusted_recipe


def _select_recipe_for_meal(meal_type, target_calories, used_recipe_ids=None):
    """Выбирает рецепт для указанного приема пищи, стараясь максимально приблизиться к целевой калорийности"""
    if used_recipe_ids is None:
        used_recipe_ids = set()

    recipes = list(Recipe.objects.filter(
        meal_type=meal_type).exclude(id__in=used_recipe_ids))

    if not recipes:
        return None, used_recipe_ids

    # Сначала ищем рецепты, которые точно подходят по калориям (±10%)
    perfect_match = [
        recipe for recipe in recipes
        if abs(recipe.calories - target_calories) <= target_calories * 0.1
    ]

    if perfect_match:
        selected_recipe = random.choice(perfect_match)
        used_recipe_ids.add(selected_recipe.id)
        return selected_recipe, used_recipe_ids

    # Если нет идеальных совпадений, ищем ближайшие по калориям
    recipes_sorted = sorted(
        recipes, key=lambda x: abs(x.calories - target_calories))

    # Берем 3 самых близких по калориям рецепта
    closest_recipes = recipes_sorted[:3]

    if closest_recipes:
        selected_recipe = random.choice(closest_recipes)
        used_recipe_ids.add(selected_recipe.id)
        return selected_recipe, used_recipe_ids

    return None, used_recipe_ids


def _optimize_day_with_portions(breakfast_target, lunch_target, snack_target, dinner_target, max_attempts=30):
    """Оптимизирует подбор рецептов с корректировкой порций"""
    total_target = breakfast_target + lunch_target + snack_target + dinner_target

    for attempt in range(max_attempts):
        # Подбираем базовые рецепты
        breakfast, used_ids = _select_recipe_for_meal(
            'breakfast', breakfast_target)
        lunch, used_ids = _select_recipe_for_meal(
            'lunch', lunch_target, used_ids)
        snack, used_ids = _select_recipe_for_meal(
            'snack', snack_target, used_ids)
        dinner, used_ids = _select_recipe_for_meal(
            'dinner', dinner_target, used_ids)

        if not all([breakfast, lunch, snack, dinner]):
            continue

        # Рассчитываем текущую калорийность
        current_calories = (
            float(breakfast.calories) +
            float(lunch.calories) +
            float(snack.calories) +
            float(dinner.calories)
        )

        # Если калорийность близка к цели (±5%), возвращаем как есть
        if abs(current_calories - total_target) <= total_target * 0.05:
            return breakfast, lunch, snack, dinner, current_calories

        # Если калорий недостаточно, увеличиваем порции
        if current_calories < total_target:
            deficit = total_target - current_calories

            # Распределяем дефицит по приемам пищи пропорционально их целевой калорийности
            meal_targets = [breakfast_target,
                            lunch_target, snack_target, dinner_target]
            meals = [breakfast, lunch, snack, dinner]
            meal_names = ['breakfast', 'lunch', 'snack', 'dinner']

            total_meal_target = sum(meal_targets)

            for i, (meal, meal_target) in enumerate(zip(meals, meal_targets)):
                if meal_target > 0:
                    # Рассчитываем, сколько калорий нужно добавить этому приему пищи
                    meal_share = meal_target / total_meal_target
                    additional_calories_needed = deficit * meal_share

                    # Рассчитываем множитель порции
                    if float(meal.calories) > 0:
                        portion_multiplier = 1 + \
                            (additional_calories_needed / float(meal.calories))

                        # Ограничиваем максимальное увеличение порции (не более 2x)
                        portion_multiplier = min(portion_multiplier, 2.0)

                        # Корректируем рецепт
                        meals[i] = _adjust_portion(meal, portion_multiplier)

            # Пересчитываем общую калорийность
            adjusted_calories = sum(float(meal.calories) for meal in meals)

            # Если после корректировки мы близки к цели, возвращаем результат
            if abs(adjusted_calories - total_target) <= total_target * 0.1:
                return meals[0], meals[1], meals[2], meals[3], adjusted_calories

    # Если не удалось оптимизировать, возвращаем лучший вариант
    return breakfast, lunch, snack, dinner, current_calories


def _smart_portion_adjustment(breakfast, lunch, snack, dinner, total_target):
    """Умная корректировка порций для точного достижения цели"""
    meals = [breakfast, lunch, snack, dinner]
    current_calories = sum(float(meal.calories) for meal in meals)

    # Если калорийность уже близка, не корректируем
    if abs(current_calories - total_target) <= total_target * 0.02:
        return breakfast, lunch, snack, dinner, current_calories

    # Рассчитываем необходимую корректировку
    adjustment_factor = total_target / current_calories if current_calories > 0 else 1

    # Ограничиваем диапазон корректировки (0.8 - 1.5)
    adjustment_factor = max(0.8, min(adjustment_factor, 1.5))

    # Применяем корректировку ко всем приемам пищи
    adjusted_meals = []
    for meal in meals:
        adjusted_meal = _adjust_portion(meal, adjustment_factor)
        adjusted_meals.append(adjusted_meal)

    adjusted_calories = sum(float(meal.calories) for meal in adjusted_meals)

    return adjusted_meals[0], adjusted_meals[1], adjusted_meals[2], adjusted_meals[3], adjusted_calories


def generate_optimized_weekly_meal_plan(daily_calories):
    """Генерирует оптимизированный рацион на неделю с корректировкой порций"""
    days_of_week = ['monday', 'tuesday', 'wednesday',
                    'thursday', 'friday', 'saturday', 'sunday']
    weekly_plan = {}

    # Гибкое распределение калорий между приемами пищи
    distributions = [
        (0.25, 0.35, 0.15, 0.25),  # стандартное
        (0.30, 0.30, 0.15, 0.25),  # больше на завтрак
        (0.25, 0.40, 0.10, 0.25),  # больше на обед
        (0.20, 0.35, 0.20, 0.25),  # больше перекусов
    ]

    for i, day in enumerate(days_of_week):
        # Чередуем распределения для разнообразия
        distribution = distributions[i % len(distributions)]

        breakfast_target = int(daily_calories * distribution[0])
        lunch_target = int(daily_calories * distribution[1])
        snack_target = int(daily_calories * distribution[2])
        dinner_target = int(daily_calories * distribution[3])

        total_target = breakfast_target + lunch_target + snack_target + dinner_target

        # Сначала подбираем базовые рецепты
        breakfast, lunch, snack, dinner, total_calories = _optimize_day_with_portions(
            breakfast_target, lunch_target, snack_target, dinner_target
        )

        # Затем применяем точную корректировку порций
        breakfast, lunch, snack, dinner, total_calories = _smart_portion_adjustment(
            breakfast, lunch, snack, dinner, total_target
        )

        weekly_plan[day] = {
            'breakfast_id': breakfast.id if breakfast else None,
            'lunch_id': lunch.id if lunch else None,
            'snack_id': snack.id if snack else None,
            'dinner_id': dinner.id if dinner else None,
            'total_calories': total_calories,
            'target_calories': daily_calories,
            'breakfast_multiplier': getattr(breakfast, 'portion_multiplier', 1.0),
            'lunch_multiplier': getattr(lunch, 'portion_multiplier', 1.0),
            'snack_multiplier': getattr(snack, 'portion_multiplier', 1.0),
            'dinner_multiplier': getattr(dinner, 'portion_multiplier', 1.0),
        }

    return weekly_plan


def _get_recipe_from_session(recipe_id):
    """Получает рецепт по ID из базы данных"""
    if recipe_id is None:
        return _create_dummy_recipe("Рецепт временно недоступен")

    try:
        return Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return _create_dummy_recipe("Рецепт не найден")


def _create_dummy_recipe(name):
    """Создает заглушку для рецепта"""
    return Recipe(
        name=name,
        calories=0,
        protein=0,
        fat=0,
        carbs=0,
        cooking_time=0,
        difficulty='easy',
        ingredients="Рецепт временно недоступен",
        instructions="Ожидайте обновления базы рецептов",
        base_portion="1 порция"
    )
