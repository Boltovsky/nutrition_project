from tabnanny import verbose
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('male', 'Мужской'),
        ('female', 'Женский'),
    ]

    GOAL_CHOICES = [
        ('loss', 'Похудение'),
        ('maintenance', 'Поддержание веса'),
        ('gain', 'Набор массы'),
    ]

    ACTIVITY_CHOICES = [
        ('sedentary', 'Малоподвижный'),
        ('light', 'Легкая активность'),
        ('moderate', 'Умеренная активность'),
        ('high', 'Высокая активность'),
        ('extreme', 'Очень высокая активность'),
    ]

    # Дополнительные поля для пользователя
    age = models.IntegerField(null=True, blank=True, verbose_name="Возраст")
    weight = models.FloatField(null=True, blank=True, verbose_name="Вес (кг)")
    height = models.FloatField(null=True, blank=True, verbose_name="Рост (см)")
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default='male', verbose_name="Пол")
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES,
                            default='maintenance', verbose_name="Цель")
    activity_level = models.CharField(
        max_length=20, choices=ACTIVITY_CHOICES, default='sedentary', verbose_name="Уровень активности")

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    daily_calories = models.IntegerField(
        default=2000, verbose_name="Суточная норма калорий")
    motivation_message = models.TextField(
        blank=True, verbose_name="Мотивационное сообщение")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Профиль {self.user.username}"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class Recipe(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Завтрак'),
        ('lunch', 'Обед'),
        ('snack', 'Перекус'),
        ('dinner', 'Ужин'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy', 'Легко'),
        ('medium', 'Средне'),
        ('hard', 'Сложно')
    ]

    name = models.CharField(max_length=200, verbose_name="Название блюда")
    meal_type = models.CharField(
        max_length=20, choices=MEAL_TYPES, verbose_name="Тип приема пищи")
    calories = models.IntegerField(verbose_name="Калории")
    protein = models.DecimalField(
        max_digits=5, decimal_places=1, verbose_name="Белки (г)")
    fat = models.DecimalField(
        max_digits=5, decimal_places=1, verbose_name="Жиры (г)")
    carbs = models.DecimalField(
        max_digits=5, decimal_places=1, verbose_name="Углеводы (г)")
    ingredients = models.TextField(verbose_name="Ингредиенты")
    instructions = models.TextField(verbose_name="Инструкция приготовления")
    image = models.ImageField(
        upload_to='recipes/', blank=True, null=True, verbose_name="Изображение")
    cooking_time = models.IntegerField(
        default=15, verbose_name="Время приготовления (мин)")
    difficulty = models.CharField(
        max_length=20, choices=DIFFICULTY_CHOICES, default='easy', verbose_name="Сложность")
    base_portion = models.CharField(
        max_length=100, default="1 порция", verbose_name="Базовая порция")

    @property
    def ingredients_list(self):
        """Возвращает список ингредиентов с оригинальным и скорректированным текстом"""
        ingredients = []
        for line in self.ingredients.split('\n'):
            line = line.strip()
            if line:
                ingredients.append({
                    'text': line,
                    'original_text': getattr(self, 'original_ingredients', line)
                })
        return ingredients

    def __str__(self):
        return f"{self.name} ({self.get_meal_type_display()})"

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class TelegramUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram')
    telegram_id = models.BigIntegerField(unique=True)
    chat_id = models.BigIntegerField()
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    is_subscribed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.telegram_id})"

    class Meta:
        db_table = 'telegram_users'
        verbose_name = "Телеграм пользователя"
        verbose_name_plural = "Телеграм пользователей"


class UserMealPlan(models.Model):
    """Постоянное хранение планов питания пользователей"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    date = models.DateField(verbose_name="Дата плана")
    meal_type = models.CharField(
        max_length=20, choices=Recipe.MEAL_TYPES, verbose_name="Прием пищи")
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")
    portion_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0, verbose_name="Множитель порции")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.get_meal_type_display()} - {self.recipe.name}"

    class Meta:
        unique_together = ['user', 'date', 'meal_type']
        verbose_name = "План питания пользователя"
        verbose_name_plural = "Планы питания пользователей"
        ordering = ['date', 'meal_type']
