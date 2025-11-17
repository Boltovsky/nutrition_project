"""
Django settings for nutrition_project project.
"""

import os
from pathlib import Path
# from dotenv import load_dotenv
# from celery.schedules import crontab
# load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-eiv)41-s@jg@g$t+rke()i@8sdi^02p37gwxw=)m9vq%dj(vli'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['Boltovsky.pythonanywhere.com',
                 'localhost',
                 '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'nutrition_app',
    'telegram_bot',

]

# Используем кастомную модель пользователя
AUTH_USER_MODEL = 'nutrition_app.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nutrition_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nutrition_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Krasnoyarsk'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'nutrition_app/static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'index'
LOGIN_URL = 'login'
TELEGRAM_BOT_TOKEN = '7652146844:AAENaRhrHofbpP8wXRQUczWtikioCz3eS28'
SITE_URL = 'https://Boltovsky.pythonanywhere.com'

# # Celery Configuration
# CELERY_BROKER_URL = 'memory://'
# CELERY_RESULT_BACKEND = 'cache+memory://'
# CELERY_TASK_ALWAYS_EAGER = True  # Задачи выполняются синхронно
# CELERY_TASK_EAGER_PROPAGATES = True
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = 'Asia/Krasnoyarsk'
# CELERY_ENABLE_UTC = False

# # Celery Beat Schedule
# CELERY_BEAT_SCHEDULE = {
#     # 🔥 ДЛЯ ТЕСТА - каждые 2 минуты (используем нашу задачу)
#     'test-notifications-every-2-min': {
#         'task': 'telegram_bot.tasks.send_test_notifications',
#         'schedule': 120.0,  # 120 секунд
#     },

#     # 🎯 ОСНОВНАЯ ПРОВЕРКА - каждые 5 минут
#     'check-meal-reminders-every-5-min': {
#         'task': 'telegram_bot.tasks.check_and_send_meal_reminders',
#         'schedule': 300.0,  # 300 секунд = 5 минут
#     },
# }
