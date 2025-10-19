from django.urls import path
from .views import (
    register, user_login, user_logout, profile_setup, dashboard,
    calculate_calories, week_plan, day_plan, recipe_detail
)

urlpatterns = [
    path('', week_plan, name='index'),  # или создай отдельную view для главной
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('profile/setup/', profile_setup, name='profile_setup'),
    path('dashboard/', dashboard, name='dashboard'),
    path('calculate/', calculate_calories, name='calculate_calories'),
    path('week-plan/', week_plan, name='week_plan'),
    path('day/<str:day_key>/', day_plan, name='day_plan'),
    path('recipe/<int:recipe_id>/', recipe_detail, name='recipe_detail'),
]
