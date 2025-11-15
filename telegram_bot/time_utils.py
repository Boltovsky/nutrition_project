from django.utils import timezone
from datetime import datetime, time

def is_meal_time(user, meal_type):
    """Проверка времени для уведомлений о приемах пищи"""
    try:
        settings = user.notification_settings

        if not settings.is_subscribed:
            return False

        # Проверяем, включены ли уведомления для конкретного приема пищи
        if not getattr(settings, f'send_{meal_type}_reminder', True):
            return False

        # Время приемов пищи
        meal_times = {
            'breakfast': time(9, 0),    # 09:00
            'lunch': time(14, 0),       # 14:00
            'snack': time(16, 0),       # 16:00
            'dinner': time(18, 0),      # 18:00
        }

        current_time = timezone.now().time()
        target_time = meal_times.get(meal_type)

        if not target_time:
            return False

        # Точное совпадение по часам и минутам
        return (current_time.hour == target_time.hour and 
                current_time.minute == target_time.minute)

    except Exception as e:
        print(f"Error in is_meal_time: {e}")
        return False

# Для обратной совместимости - оставляем старую функцию
def is_reminder_time(user, reminder_type='morning'):
    """Старая функция для обратной совместимости"""
    # Просто вызываем новую функцию с преобразованием типов
    if reminder_type == 'morning':
        return is_meal_time(user, 'breakfast')
    elif reminder_type == 'evening':
        return is_meal_time(user, 'dinner')
    else:
        return False