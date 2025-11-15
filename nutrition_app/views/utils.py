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


def _adjust_portion(recipe, new_multiplier):
    """Создает копию рецепта с увеличенной/уменьшенной порцией"""
    # 🔥 Берем ТЕКУЩИЙ множитель и умножаем на НОВЫЙ
    current_multiplier = getattr(recipe, 'portion_multiplier', 1.0)
    total_multiplier = current_multiplier * new_multiplier
    total_multiplier = round(float(total_multiplier), 1)

    # Всегда получаем ОРИГИНАЛЬНЫЙ рецепт из базы данных
    try:
        original_recipe = Recipe.objects.get(id=recipe.id)
        base_calories = original_recipe.calories
        base_protein = original_recipe.protein
        base_fat = original_recipe.fat
        base_carbs = original_recipe.carbs
    except Recipe.DoesNotExist:
        base_calories = recipe.calories
        base_protein = recipe.protein
        base_fat = recipe.fat
        base_carbs = recipe.carbs

    # Корректируем ингредиенты на ОБЩИЙ множитель
    adjusted_ingredients = _adjust_recipe_ingredients(
        recipe.ingredients, total_multiplier
    )

    adjusted_recipe = Recipe(
        id=recipe.id,
        name=recipe.name,
        meal_type=recipe.meal_type,
        calories=int(float(base_calories) * total_multiplier),
        protein=round(float(base_protein) * total_multiplier, 1),
        fat=round(float(base_fat) * total_multiplier, 1),
        carbs=round(float(base_carbs) * total_multiplier, 1),
        ingredients=adjusted_ingredients,
        instructions=recipe.instructions,
        image=recipe.image,
        cooking_time=recipe.cooking_time,
        difficulty=recipe.difficulty,
        base_portion=f"{total_multiplier:.1f} порции" if total_multiplier != 1.0 else "1 порция"
    )

    # 🔥 Сохраняем ОБЩИЙ множитель
    adjusted_recipe.portion_multiplier = total_multiplier
    adjusted_recipe.original_calories = base_calories

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

    closest_recipes = recipes_sorted[:]

    if closest_recipes:
        selected_recipe = random.choice(closest_recipes)
        used_recipe_ids.add(selected_recipe.id)
        return selected_recipe, used_recipe_ids

    return None, used_recipe_ids


def _select_recipe_for_meal_weekly(meal_type, target_calories, used_recipe_ids, day_variation_seed):
    """Выбирает рецепт БЕЗ фиксированного seed"""
    # Создаем локальную копию для безопасности
    current_used_ids = used_recipe_ids.copy()

    # Ищем рецепты этого типа, которые еще не использовались
    available_recipes = list(Recipe.objects.filter(
        meal_type=meal_type
    ).exclude(id__in=current_used_ids))

    if not available_recipes:
        # Если все рецепты этого типа уже использованы, берем из всех рецептов этого типа
        available_recipes = list(Recipe.objects.filter(meal_type=meal_type))
        if not available_recipes:
            return None, used_recipe_ids

    # 🔥 УБИРАЕМ ФИКСИРОВАННЫЙ SEED - используем настоящую случайность
    # Сначала ищем рецепты, которые подходят по калориям (±20% для большего выбора)
    good_matches = [
        recipe for recipe in available_recipes
        if abs(recipe.calories - target_calories) <= target_calories * 0.2
    ]

    if good_matches:
        selected_recipe = random.choice(good_matches)
    else:
        # Если нет хороших совпадений, берем случайный из доступных
        selected_recipe = random.choice(available_recipes)

    # 🔥 УБИРАЕМ random.seed() - не сбрасываем глобальный random

    if selected_recipe:
        # Добавляем выбранный рецепт в использованные
        current_used_ids.add(selected_recipe.id)

    return selected_recipe, current_used_ids


def _optimize_day_with_portions_weekly(breakfast_target, lunch_target, snack_target, dinner_target, used_recipe_ids, day_number, max_attempts=15):
    """Оптимизирует подбор рецептов БЕЗ фиксированных seed"""
    total_target = breakfast_target + lunch_target + snack_target + dinner_target

    best_combination = None
    best_calorie_diff = float('inf')

    for attempt in range(max_attempts):
        current_used_ids = used_recipe_ids.copy()

        # 🔥 УБИРАЕМ ФИКСИРОВАННЫЙ SEED - используем настоящую случайность

        # Подбираем рецепты
        breakfast, used_after_breakfast = _select_recipe_for_meal_weekly(
            # ⬅️ передаем attempt вместо seed
            'breakfast', breakfast_target, current_used_ids, attempt)
        lunch, used_after_lunch = _select_recipe_for_meal_weekly(
            'lunch', lunch_target, used_after_breakfast, attempt)
        snack, used_after_snack = _select_recipe_for_meal_weekly(
            'snack', snack_target, used_after_lunch, attempt)
        dinner, used_after_dinner = _select_recipe_for_meal_weekly(
            'dinner', dinner_target, used_after_snack, attempt)

        if not all([breakfast, lunch, snack, dinner]):
            continue

        # Рассчитываем калорийность
        current_calories = sum(float(meal.calories)
                               for meal in [breakfast, lunch, snack, dinner])
        calorie_diff = abs(current_calories - total_target)

        # Отдаем предпочтение комбинациям, которые ближе к цели
        if calorie_diff < best_calorie_diff:
            best_combination = (breakfast, lunch, snack,
                                dinner, current_calories, used_after_dinner)
            best_calorie_diff = calorie_diff

        # Если нашли хорошее сочетание (±15%), выходим раньше
        if calorie_diff <= total_target * 0.15:
            break

    if best_combination:
        breakfast, lunch, snack, dinner, current_calories, final_used_ids = best_combination

        # 🔥 СРАЗУ ОПТИМИЗИРУЕМ КАЛОРИЙНОСТЬ ПРИ СОЗДАНИИ ПЛАНА
        if abs(current_calories - total_target) > total_target * 0.05:
            breakfast, lunch, snack, dinner, current_calories = optimize_daily_calories(
                breakfast, lunch, snack, dinner, total_target
            )

        return breakfast, lunch, snack, dinner, current_calories, final_used_ids

    return _get_fallback_recipes(breakfast_target, lunch_target, snack_target, dinner_target, used_recipe_ids)


def _get_fallback_recipes(breakfast_target, lunch_target, snack_target, dinner_target, used_recipe_ids):
    """Резервный метод подбора рецептов"""
    current_used_ids = used_recipe_ids.copy()

    # Просто берем первые доступные рецепты каждого типа
    breakfast = Recipe.objects.filter(meal_type='breakfast').exclude(
        id__in=current_used_ids).first()
    if not breakfast:
        breakfast = Recipe.objects.filter(meal_type='breakfast').first()
    if breakfast:
        current_used_ids.add(breakfast.id)

    lunch = Recipe.objects.filter(meal_type='lunch').exclude(
        id__in=current_used_ids).first()
    if not lunch:
        lunch = Recipe.objects.filter(meal_type='lunch').first()
    if lunch:
        current_used_ids.add(lunch.id)

    snack = Recipe.objects.filter(meal_type='snack').exclude(
        id__in=current_used_ids).first()
    if not snack:
        snack = Recipe.objects.filter(meal_type='snack').first()
    if snack:
        current_used_ids.add(snack.id)

    dinner = Recipe.objects.filter(meal_type='dinner').exclude(
        id__in=current_used_ids).first()
    if not dinner:
        dinner = Recipe.objects.filter(meal_type='dinner').first()
    if dinner:
        current_used_ids.add(dinner.id)

    if all([breakfast, lunch, snack, dinner]):
        current_calories = sum(float(meal.calories)
                               for meal in [breakfast, lunch, snack, dinner])
        return breakfast, lunch, snack, dinner, current_calories, current_used_ids

    return None, None, None, None, 0, used_recipe_ids


def generate_optimized_weekly_meal_plan(daily_calories):
    """Генерирует оптимизированный рацион на неделю с УНИКАЛЬНЫМИ рецептами каждый раз"""

    # 🔥 ДОБАВЛЯЕМ ПРИНУДИТЕЛЬНУЮ РАНДОМИЗАЦИЮ
    import random
    import time
    random.seed(time.time())  # Разный seed каждый раз

    days_of_week = ['monday', 'tuesday', 'wednesday',
                    'thursday', 'friday', 'saturday', 'sunday']
    weekly_plan = {}

    # Разные распределения калорий для каждого дня
    distributions = [
        (0.25, 0.35, 0.15, 0.25),  # Понедельник
        (0.30, 0.30, 0.15, 0.25),  # Вторник
        (0.25, 0.40, 0.10, 0.25),  # Среда
        (0.20, 0.35, 0.20, 0.25),  # Четверг
        (0.28, 0.32, 0.18, 0.22),  # Пятница
        (0.22, 0.38, 0.12, 0.28),  # Суббота
        (0.26, 0.34, 0.16, 0.24),  # Воскресенье
    ]

    # 🔥 ПРИНУДИТЕЛЬНО ОЧИЩАЕМ ИСПОЛЬЗОВАННЫЕ РЕЦЕПТЫ
    weekly_used_recipe_ids = set()

    for i, day in enumerate(days_of_week):
        distribution = distributions[i]

        breakfast_target = int(daily_calories * distribution[0])
        lunch_target = int(daily_calories * distribution[1])
        snack_target = int(daily_calories * distribution[2])
        dinner_target = int(daily_calories * distribution[3])

        # Подбираем рецепты для дня
        breakfast, lunch, snack, dinner, total_calories, daily_used_ids = _optimize_day_with_portions_weekly(
            breakfast_target, lunch_target, snack_target, dinner_target,
            weekly_used_recipe_ids, i + 1
        )

        # ОБНОВЛЯЕМ глобальный список использованных рецептов
        weekly_used_recipe_ids.update(daily_used_ids)

        if all([breakfast, lunch, snack, dinner]):
            weekly_plan[day] = {
                'breakfast_id': breakfast.id,
                'lunch_id': lunch.id,
                'snack_id': snack.id,
                'dinner_id': dinner.id,
                'total_calories': total_calories,
                'target_calories': daily_calories,
                'breakfast_multiplier': getattr(breakfast, 'portion_multiplier', 1.0),
                'lunch_multiplier': getattr(lunch, 'portion_multiplier', 1.0),
                'snack_multiplier': getattr(snack, 'portion_multiplier', 1.0),
                'dinner_multiplier': getattr(dinner, 'portion_multiplier', 1.0),
                'day_name': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][i]
            }
        else:
            # Запасной вариант
            weekly_plan[day] = _create_fallback_day_plan(daily_calories, i)

    return weekly_plan


def _create_fallback_day_plan(daily_calories, day_index):
    """Создает запасной план на день (сохраняет только ID)"""
    # Берем любые доступные рецепты
    breakfast = Recipe.objects.filter(meal_type='breakfast').first()
    lunch = Recipe.objects.filter(meal_type='lunch').first()
    snack = Recipe.objects.filter(meal_type='snack').first()
    dinner = Recipe.objects.filter(meal_type='dinner').first()

    return {
        'breakfast_id': breakfast.id if breakfast else None,
        'lunch_id': lunch.id if lunch else None,
        'snack_id': snack.id if snack else None,
        'dinner_id': dinner.id if dinner else None,
        'total_calories': daily_calories,
        'target_calories': daily_calories,
        'breakfast_multiplier': 1.0,
        'lunch_multiplier': 1.0,
        'snack_multiplier': 1.0,
        'dinner_multiplier': 1.0,
        'day_name': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][day_index],
        'is_fallback': True
    }


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


def _adjust_portion_to_target(recipes, total_target, priority_order):
    """
    Корректирует порции рецептов для достижения целевой калорийности
    """
    # Текущая калорийность (приводим к float)
    current_calories = sum(float(recipe.calories) for recipe in recipes)
    total_target = float(total_target)

    # Если уже в пределах 5% - не корректируем
    tolerance = total_target * 0.05
    if abs(current_calories - total_target) <= tolerance:
        return recipes, current_calories

    # Если текущих калорий меньше цели - увеличиваем порции
    if current_calories < total_target:
        return _increase_portions_precise(recipes, total_target, priority_order)

    # Если текущих калорий больше цели - уменьшаем порции
    return _decrease_portions(recipes, total_target, priority_order)


def _increase_portions_precise(recipes, total_target, priority_order):
    """Точно увеличивает порции для достижения цели"""
    current_calories = sum(float(recipe.calories) for recipe in recipes)
    total_target = float(total_target)
    deficit = total_target - current_calories

    # Если дефицит слишком большой (>30%), лучше пересобрать день
    if deficit > total_target * 0.3:
        return recipes, current_calories

    adjusted_recipes = recipes.copy()

    # Пробуем увеличивать порции постепенно
    for multiplier in [1.5, 2.0, 2.5, 3.0]:
        temp_recipes = recipes.copy()
        temp_calories = current_calories
        success = False

        # Увеличиваем порции по приоритету
        for priority_index in priority_order:
            if temp_calories >= total_target * 0.95:
                success = True
                break

            recipe = temp_recipes[priority_index]
            original_calories = float(recipe.calories)

            # Увеличиваем порцию
            adjusted_recipe = _adjust_portion(recipe, multiplier)
            new_calories = float(adjusted_recipe.calories)

            # Проверяем, не превысим ли мы цель слишком сильно
            if temp_calories + (new_calories - original_calories) <= total_target * 1.05:
                temp_recipes[priority_index] = adjusted_recipe
                temp_calories = sum(float(r.calories) for r in temp_recipes)

        # Если достигли цели, сохраняем результат
        if success and abs(temp_calories - total_target) <= total_target * 0.1:
            adjusted_recipes = temp_recipes
            current_calories = temp_calories
            break

    return adjusted_recipes, current_calories


def _decrease_portions(recipes, total_target, priority_order):
    """Уменьшает порции если калорий слишком много"""
    current_calories = sum(float(recipe.calories) for recipe in recipes)
    total_target = float(total_target)

    # Если превышение небольшое (<10%), не уменьшаем
    if current_calories <= total_target * 1.1:
        return recipes, current_calories

    adjusted_recipes = recipes.copy()
    target_max = total_target * 1.05

    # Уменьшаем порции в обратном порядке приоритета
    reverse_priority = list(reversed(priority_order))

    for priority_index in reverse_priority:
        if current_calories <= target_max:
            break

        recipe = adjusted_recipes[priority_index]
        current_multiplier = float(getattr(recipe, 'portion_multiplier', 1.0))

        # Уменьшаем порцию если множитель > 1
        if current_multiplier > 1:
            new_multiplier = max(1.0, current_multiplier - 0.5)
            adjusted_recipe = _adjust_portion(recipe, new_multiplier)
            adjusted_recipes[priority_index] = adjusted_recipe
            current_calories = sum(float(r.calories) for r in adjusted_recipes)

    return adjusted_recipes, current_calories


def optimize_daily_calories(breakfast, lunch, snack, dinner, total_target):
    """
    Оптимизирует калорийность дня через корректировку порций
    Приоритет: завтрак -> перекус -> обед -> ужин
    """
    # Порядок приоритета: завтрак, перекус, обед, ужин
    recipes = [breakfast, snack, lunch, dinner]
    priority_order = [0, 1, 2, 3]

    # Приводим total_target к float
    total_target = float(total_target)

    # Сначала пробуем точный метод
    adjusted_recipes, final_calories = _adjust_portion_to_target(
        recipes, total_target, priority_order
    )

    # Если не удалось достичь цели, пробуем умный метод
    if abs(final_calories - total_target) > total_target * 0.1:
        adjusted_recipes, final_calories = _increase_portions_smart(
            recipes, total_target, priority_order
        )

    # Возвращаем в исходном порядке: завтрак, обед, перекус, ужин
    return adjusted_recipes[0], adjusted_recipes[2], adjusted_recipes[1], adjusted_recipes[3], final_calories


def _increase_portions_smart(recipes, total_target, priority_order):
    """Умное увеличение порций с проверкой на каждом шаге"""
    current_calories = sum(float(recipe.calories) for recipe in recipes)
    total_target = float(total_target)
    adjusted_recipes = recipes.copy()

    # Целевой диапазон: 95-105% от нормы
    target_min = total_target * 0.95
    target_max = total_target * 1.05

    # Постепенно увеличиваем порции пока не достигнем цели
    while current_calories < target_min:
        calorie_gain = 0

        # Проходим по приоритетам и увеличиваем порции
        for priority_index in priority_order:
            if current_calories >= target_min:
                break

            recipe = adjusted_recipes[priority_index]
            current_multiplier = float(
                getattr(recipe, 'portion_multiplier', 1.0))

            # Увеличиваем порцию на 0.5
            new_multiplier = current_multiplier + 0.5
            adjusted_recipe = _adjust_portion(recipe, new_multiplier)

            # Проверяем, не выйдем ли за верхнюю границу
            new_total = current_calories - \
                float(recipe.calories) + float(adjusted_recipe.calories)
            if new_total <= target_max:
                adjusted_recipes[priority_index] = adjusted_recipe
                calorie_gain = float(
                    adjusted_recipe.calories) - float(recipe.calories)
                current_calories += calorie_gain

        # Если за цикл не удалось увеличить калории, выходим
        if calorie_gain == 0:
            break

    return adjusted_recipes, current_calories
