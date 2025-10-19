from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Придумайте логин'}),
        label='Логин'
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Ваше имя'}),
        label='Имя'
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Ваша фамилия'}),
        label='Фамилия'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': 'Email'}),
        label='Электронная почта'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name',
                  'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Ваш логин'})
        self.fields['password1'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Подтверждение пароля'})
        self.fields['first_name'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Ваше имя'})
        self.fields['last_name'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Ваша фамилия'})


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Имя пользователя'})
        self.fields['password'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Пароль'})


class UserProfileForm(forms.ModelForm):
    # Кастомные choices для уровня активности с подробными описаниями
    ACTIVITY_CHOICES = [
        ('sedentary', 'Малоподвижный (сидячая работа, минимум активности)'),
        ('light', 'Легкая активность (легкие тренировки 1-3 раза в неделю)'),
        ('moderate', 'Умеренная активность (тренировки 3-5 раз в неделю)'),
        ('high', 'Высокая активность (интенсивные тренировки 6-7 раз в неделю)'),
        ('extreme', 'Очень высокая активность (тяжелые физические нагрузки, работа)'),
    ]

    # Переопределяем поле активности с кастомными choices
    activity_level = forms.ChoiceField(
        choices=ACTIVITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Уровень активности'
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'age', 'weight',
                  'height', 'gender', 'goal', 'activity_level')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': '13', 'max': '100'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '30', 'max': '200'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'min': '100', 'max': '250'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'goal': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'gender': 'Пол',
            'goal': 'Цель',
            'age': 'Возраст (лет)',
            'weight': 'Вес (кг)',
            'height': 'Рост (см)',
        }
        help_texts = {
            'age': 'Введите ваш возраст от 13 до 100 лет',
            'weight': 'Введите ваш вес в килограммах',
            'height': 'Введите ваш рост в сантиметрах',
        }
