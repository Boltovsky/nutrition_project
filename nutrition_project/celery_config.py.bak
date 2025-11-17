import os
from celery import Celery
from celery.schedules import crontab

# Устанавливаем настройки Django по умолчанию
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutrition_project.settings')

app = Celery('nutrition_project')

# Используем строку конфигурации для настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в приложениях Django
app.autodiscover_tasks()

# Расписание для уведомлений о приемах пищи
app.conf.beat_schedule = {
    # Проверка уведомлений каждую минуту
    'check-meal-reminders': {
        'task': 'telegram_bot.tasks.check_meal_reminders',
        'schedule': 60.0,  # каждую минуту
    },
}

# Настройки времени
app.conf.timezone = 'Asia/Almaty'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
