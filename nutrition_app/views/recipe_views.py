from django.shortcuts import render
from ..models import Recipe


def recipe_detail(request, recipe_id):
    """Детальная страница рецепта"""
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return render(request, 'nutrition_app/404.html', status=404)

    # Получаем похожие рецепты (той же категории)
    similar_recipes = Recipe.objects.filter(
        meal_type=recipe.meal_type
    ).exclude(id=recipe.id)[:3]

    context = {
        'recipe': recipe,
        'similar_recipes': similar_recipes,
    }

    return render(request, 'nutrition_app/recipe_detail.html', context)
