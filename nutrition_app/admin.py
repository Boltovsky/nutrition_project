from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile, Recipe


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name',
                    'last_name', 'age', 'goal', 'activity_level')
    list_filter = ('goal', 'activity_level', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('age', 'weight', 'height', 'gender', 'goal', 'activity_level')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_calories', 'created_at')
    list_filter = ('created_at',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'meal_type', 'calories', 'protein',
                    'fat', 'carbs', 'cooking_time', 'difficulty']
    list_filter = ['meal_type', 'difficulty']
    search_fields = ['name', 'ingredients']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 200px;" />'
        return "Нет изображения"
    image_preview.allow_tags = True
    image_preview.short_description = "Предпросмотр"
