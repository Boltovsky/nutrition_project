from django.shortcuts import render
from ..models import Recipe
from .utils import _adjust_portion


def recipe_detail(request, recipe_id):
    """Детальная страница рецепта с возможностью изменения порций"""
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return render(request, 'nutrition_app/404.html', status=404)

    # Получаем количество порций из GET-параметра или используем 1 по умолчанию
    portions = int(request.GET.get('portions', 1))

    # Ограничиваем диапазон порций (от 1 до 10)
    portions = max(1, min(portions, 10))

    # Корректируем рецепт под выбранное количество порций
    adjusted_recipe = _adjust_portion(recipe, portions)

    # Получаем похожие рецепты (той же категории)
    similar_recipes = Recipe.objects.filter(
        meal_type=recipe.meal_type
    ).exclude(id=recipe.id)[:3]

    context = {
        'recipe': adjusted_recipe,
        'original_recipe': recipe,  # Сохраняем оригинальный рецепт для сброса
        'similar_recipes': similar_recipes,
        'current_portions': portions,
        'portion_range': range(1, 11),  # Для выпадающего списка
    }

    return render(request, 'nutrition_app/recipe_detail.html', context)
