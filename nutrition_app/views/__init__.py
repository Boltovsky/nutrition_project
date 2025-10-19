from operator import indexOf
from .auth_views import register, user_login, user_logout, profile_setup, dashboard
from .meal_views import calculate_calories, week_plan, day_plan
from .recipe_views import recipe_detail
from . import utils
from .main_views import index
# Экспортируем все функции
__all__ = [
    'register', 'user_login', 'user_logout', 'profile_setup', 'dashboard',
    'calculate_calories', 'week_plan', 'day_plan', 'recipe_detail', 'utils', index

]
