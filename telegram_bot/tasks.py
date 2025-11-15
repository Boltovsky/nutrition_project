from celery import shared_task
from celery.schedules import crontab
from django.utils import timezone
from datetime import datetime, time
import requests
import os
import logging
from asgiref.sync import sync_to_async
import asyncio

logger = logging.getLogger(__name__)

# ===== КОНФИГУРАЦИЯ =====

MEAL_SCHEDULE = {
    'breakfast': time(9, 0),   # 09:00
    'lunch': time(12, 0),      # 12:00
    'snack': time(16, 0),      # 16:00
    'dinner': time(19, 0),     # 19:00
}

MEAL_MESSAGES = {
    'breakfast': {
        'title': "🍳 Завтрак",
        'message': "Доброе утро! Пора подкрепиться для энергичного дня! 🌅"
    },
    'lunch': {
        'title': "🍗 Обед",
        'message': "Время восстановить силы! Полноценный обед - залог продуктивности! 💪"
    },
    'snack': {
        'title': "🍎 Перекус",
        'message': "Легкий перекус поможет дожить до ужина без срывов! 🎯"
    },
    'dinner': {
        'title': "🐟 Ужин",
        'message': "Время для легкого ужина! Правильный ужин - залог хорошего сна! 🌙"
    }
}

# ===== ОСНОВНЫЕ ЗАДАЧИ =====


@shared_task
def check_and_send_meal_reminders():
    """Основная задача - проверяет время и отправляет уведомления"""
    logger.info("🔔 Celery: Начало проверки уведомлений")

    current_time = timezone.now().time()
    current_date = timezone.now().date()

    # Проверяем каждый прием пищи
    for meal_type, meal_time in MEAL_SCHEDULE.items():
        if _is_meal_time(current_time, meal_time):
            logger.info(f"🎯 Время для {meal_type}! Отправка уведомлений...")
            send_meal_notification.delay(meal_type, current_date)
        else:
            logger.debug(
                f"⏰ {meal_type} - не время (сейчас {current_time.strftime('%H:%M')})")


@shared_task
def send_meal_notification(meal_type, target_date):
    """Отправляет уведомления для конкретного приема пищи"""
    logger.info(f"📨 Отправка уведомлений для {meal_type}")

    try:
        # Получаем всех подписанных пользователей
        users = _get_subscribed_users()
        logger.info(f"🔍 Найдено {len(users)} пользователей для уведомлений")

        for user in users:
            try:
                # Проверяем настройки пользователя
                if _should_send_notification(user, meal_type):
                    # Формируем и отправляем сообщение
                    message = _build_meal_message(user, meal_type, target_date)
                    _send_telegram_message(user.chat_id, message)
                    logger.info(
                        f"✅ Уведомление {meal_type} отправлено {user.user.username}")

            except Exception as e:
                logger.error(f"❌ Ошибка отправки {user.user.username}: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка в send_meal_notification: {e}")


@shared_task
def send_test_notifications():
    """Тестовая задача - отправляет уведомления каждые 2 минуты в правильном порядке"""
    logger.info("🧪 Тестовые уведомления: запуск")

    # Правильный порядок приемов пищи
    meals_cycle = ['breakfast', 'lunch', 'snack', 'dinner']

    # Получаем или создаем ключ для хранения текущего индекса
    from django.core.cache import cache

    # Ключ для хранения текущего индекса
    current_index_key = 'test_notifications_current_index'

    # Получаем текущий индекс из кэша (или 0 по умолчанию)
    current_index = cache.get(current_index_key, 0)

    # Определяем текущий прием пищи
    meal_type = meals_cycle[current_index]
    current_date = timezone.now().date()

    logger.info(
        f"🧪 Отправка уведомления: {meal_type} (индекс: {current_index})")

    # Отправляем уведомление
    send_meal_notification.delay(meal_type, current_date)

    # Увеличиваем индекс для следующего запуска
    next_index = (current_index + 1) % len(meals_cycle)
    cache.set(current_index_key, next_index, timeout=None)  # Храним бессрочно

    logger.info(f"🧪 Следующее уведомление: {meals_cycle[next_index]}")

# ===== СИНХРОННЫЕ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====


def _is_meal_time(current_time, meal_time):
    """Проверяет, совпадает ли текущее время с временем приема пищи (±5 минут)"""
    current_total = current_time.hour * 60 + current_time.minute
    meal_total = meal_time.hour * 60 + meal_time.minute

    return abs(current_total - meal_total) <= 5


def _get_subscribed_users():
    """Получает всех подписанных пользователей"""
    from nutrition_app.models import TelegramUser
    return list(TelegramUser.objects.filter(is_subscribed=True))


def _should_send_notification(user, meal_type):
    """Проверяет, нужно ли отправлять уведомление пользователю"""
    try:
        settings = user.user.notification_settings
        return getattr(settings, f'send_{meal_type}_reminder', False)
    except Exception as e:
        logger.error(f"❌ Ошибка проверки настроек {user.user.username}: {e}")
        return False


def _build_meal_message(user, meal_type, target_date):
    """Формирует сообщение для уведомления"""
    meal_info = MEAL_MESSAGES[meal_type]

    # Пытаемся получить меню пользователя
    menu_text = _get_user_menu_text(user.user, target_date, meal_type)

    message = f"{meal_info['title']} ⏰ {MEAL_SCHEDULE[meal_type].strftime('%H:%M')}\n\n"
    message += f"{meal_info['message']}\n\n"

    if menu_text:
        message += f"🍽️ *Ваше меню:*\n{menu_text}\n\n"
    else:
        message += "📝 *На сегодня меню не составлено*\nЗайдите на сайт для настройки плана питания!\n\n"

    message += "Приятного аппетита! 🍴"
    return message


def _get_user_menu_text(user, target_date, meal_type):
    """Получает текст меню пользователя на дату"""
    try:
        from nutrition_app.models import UserMealPlan

        # Ищем планы питания на эту дату и прием пищи
        meal_plans = UserMealPlan.objects.filter(
            user=user,
            date=target_date,
            meal_type=meal_type
        ).select_related('recipe')

        if not meal_plans:
            return None

        menu_items = []
        total_calories = 0

        for plan in meal_plans:
            # Рассчитываем калории с учетом порции
            calories = int(plan.recipe.calories *
                           float(plan.portion_multiplier))
            total_calories += calories

            description = plan.recipe.name
            if plan.portion_multiplier != 1.0:
                description += f" ({plan.portion_multiplier} порц.)"

            menu_items.append(f"• {description} - {calories} ккал")

        menu_text = "\n".join(menu_items)
        menu_text += f"\n📊 Всего: {total_calories} ккал"

        return menu_text

    except Exception as e:
        logger.error(f"❌ Ошибка получения меню {user.username}: {e}")
        return None


def _send_telegram_message(chat_id, message):
    """Отправляет сообщение в Telegram через Bot API"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не найден")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            return True
        else:
            logger.error(
                f"❌ Ошибка Telegram API: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения: {e}")
        return False

# ===== РАСПИСАНИЕ ДЛЯ CELERY BEAT =====


# Добавь это в settings.py
CELERY_BEAT_SCHEDULE = {
    # 🔥 ДЛЯ ТЕСТА - каждые 2 минуты
    'test-notifications-every-2-min': {
        'task': 'telegram_bot.tasks.send_test_notifications',
        'schedule': 120.0,  # 120 секунд
    },

    # 🎯 ДЛЯ ПРОДАКШЕНА - проверка каждые 5 минут
    'check-meal-reminders-every-5-min': {
        'task': 'telegram_bot.tasks.check_and_send_meal_reminders',
        'schedule': 300.0,  # 300 секунд = 5 минут
    },

    # 🕒 РЕАЛЬНОЕ РАСПИСАНИЕ (можно добавить позже):
    'breakfast-reminder': {
        'task': 'telegram_bot.tasks.check_and_send_meal_reminders',
        'schedule': crontab(hour=8, minute=55),  # За 5 минут до завтрака
    },
    'lunch-reminder': {
        'task': 'telegram_bot.tasks.check_and_send_meal_reminders',
        'schedule': crontab(hour=11, minute=55),  # За 5 минут до обеда
    },
    'snack-reminder': {
        'task': 'telegram_bot.tasks.check_and_send_meal_reminders',
        'schedule': crontab(hour=15, minute=55),  # За 5 минут до перекуса
    },
    'dinner-reminder': {
        'task': 'telegram_bot.tasks.check_and_send_meal_reminders',
        'schedule': crontab(hour=18, minute=55),  # За 5 минут до ужина
    },
}

# ===== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ =====


@shared_task
def debug_task():
    """Задача для отладки Celery"""
    logger.info("✅ Celery работает! Debug task выполнена")
    return "DEBUG_SUCCESS"


@shared_task
def send_broadcast_message(message_text):
    """Отправляет broadcast сообщение всем пользователям"""
    users = _get_subscribed_users()
    logger.info(f"📢 Broadcast для {len(users)} пользователей")

    success_count = 0
    for user in users:
        if _send_telegram_message(user.chat_id, message_text):
            success_count += 1

    logger.info(f"📢 Broadcast завершен: {success_count}/{len(users)} успешно")
    return success_count
