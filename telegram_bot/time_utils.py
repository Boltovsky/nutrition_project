from django.utils import timezone
from datetime import datetime


def is_reminder_time(user, reminder_type='morning'):
    """Проверка времени уведомлений - РАЗНЫЕ минуты для тестирования"""
    try:
        settings = user.notification_settings

        if not settings.is_subscribed:
            return False

        if reminder_type == 'morning' and not settings.send_morning_reminder:
            return False
        if reminder_type == 'evening' and not settings.send_evening_reminder:
            return False

        # РАЗНЫЕ МИНУТЫ для тестирования:
        current_time = timezone.now()
        current_minute = current_time.minute

        if reminder_type == 'morning':
            # Утренние: каждая ЧЕТНАЯ минута (0, 2, 4, 6...)
            return current_minute % 2 == 0
        else:  # evening
            # Вечерние: каждая НЕЧЕТНАЯ минута (1, 3, 5, 7...)
            return current_minute % 2 == 1

    except Exception as e:
        print(f"Error in is_reminder_time: {e}")
        return False
