from celery import shared_task
from nutrition_app.models import TelegramUser, UserMealPlan, UserNotificationSettings
from telegram_bot.bot import application
from telegram_bot.time_utils import is_reminder_time
from asgiref.sync import sync_to_async
import asyncio


@shared_task
def check_all_reminders():
    """Проверяем и отправляем все уведомления"""
    print("🎯 Celery: НАЧАЛО ПРОВЕРКИ УВЕДОМЛЕНИЙ")

    telegram_users = TelegramUser.objects.select_related(
        'user', 'user__notification_settings'
    ).all()

    print(f"🔍 ВСЕГО Telegram пользователей в базе: {telegram_users.count()}")

    for telegram_user in telegram_users:
        try:
            print(
                f"👤 Проверяем: {telegram_user.user.username} (ID: {telegram_user.telegram_id})")

            settings = telegram_user.user.notification_settings

            if not settings.is_subscribed:
                print("   ⏭️  Пропускаем - уведомления выключены")
                continue

            # Утреннее напоминание
            if is_reminder_time(telegram_user.user, 'morning') and settings.send_morning_reminder:
                print(f"   📨 ОТПРАВЛЯЕМ УТРЕННЕЕ УВЕДОМЛЕНИЕ!")
                # Запускаем асинхронную задачу
                asyncio.run(send_morning_reminder_async(telegram_user))

            # Вечернее напоминание
            if is_reminder_time(telegram_user.user, 'evening') and settings.send_evening_reminder:
                print(f"   📨 ОТПРАВЛЯЕМ ВЕЧЕРНЕЕ УВЕДОМЛЕНИЕ!")
                # Запускаем асинхронную задачу
                asyncio.run(send_evening_reminder_async(telegram_user))

        except Exception as e:
            print(f"❌ Ошибка у {telegram_user.user.username}: {e}")

    print("✅ ПРОВЕРКА ЗАВЕРШЕНА")


async def send_morning_reminder_async(telegram_user):
    """Асинхронная отправка утреннего напоминания"""
    try:
        from django.utils import timezone

        today = timezone.now().date()

        # Асинхронно получаем план питания
        meal_plans = await sync_to_async(list)(
            UserMealPlan.objects.filter(
                user=telegram_user.user,
                date=today
            ).select_related('recipe')
        )

        if meal_plans:
            # Если есть план - показываем его
            message = generate_daily_menu_message(meal_plans, today)
        else:
            # Если плана нет - напоминаем составить
            message = (
                f"🌅 *Доброе утро!*\n\n"
                f"На {today.strftime('%d.%m.%Y')} у вас нет плана питания.\n\n"
                f"Составьте план на день для достижения ваших целей! 💪\n\n"
                f"*Команды бота:*\n"
                f"/menu - Посмотреть меню\n"
                f"/notifications - Настройки уведомлений"
            )

        await send_telegram_message_async(telegram_user.chat_id, message)
        print(
            f"✅ Утреннее уведомление отправлено для {telegram_user.user.username}")

    except Exception as e:
        print(f"❌ Ошибка отправки утреннего уведомления: {e}")


async def send_evening_reminder_async(telegram_user):
    """Асинхронная отправка вечернего напоминания"""
    try:
        message = (
            "🌙 *Добрый вечер!*\n\n"
            "Не забудьте внести все приемы пищи за сегодня в дневник! 📝\n\n"
            "*Команды бота:*\n"
            "/menu - Посмотреть сегодняшнее меню\n"
            "/notifications - Управление уведомлениями\n\n"
            "Спокойной ночи! 😴"
        )

        await send_telegram_message_async(telegram_user.chat_id, message)
        print(
            f"✅ Вечернее уведомление отправлено для {telegram_user.user.username}")

    except Exception as e:
        print(f"❌ Ошибка отправки вечернего уведомления: {e}")


async def send_telegram_message_async(chat_id, message):
    """Асинхронная отправка сообщения в Telegram"""
    try:
        await application.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
        print(f"✅ Сообщение отправлено в {chat_id}")
    except Exception as e:
        print(f"❌ Ошибка отправки в {chat_id}: {e}")


def generate_daily_menu_message(meal_plans, date):
    """Генерирует сообщение с меню на день"""
    message = f"🍽️ *Ваше меню на {date.strftime('%d.%m.%Y')}:*\n\n"

    meal_types = {
        'breakfast': '🥣 Завтрак',
        'lunch': '🍗 Обед',
        'dinner': '🐟 Ужин',
        'snack': '🍎 Перекус'
    }

    total_calories = 0

    # Группируем по приемам пищи
    meals_dict = {}
    for plan in meal_plans:
        if plan.meal_type not in meals_dict:
            meals_dict[plan.meal_type] = []

        description = plan.recipe.name
        if plan.portion_multiplier != 1.0:
            description += f" ({plan.portion_multiplier} порц.)"

        calories = plan.recipe.calories * float(plan.portion_multiplier)
        meals_dict[plan.meal_type].append({
            'description': description,
            'calories': calories
        })

        total_calories += calories

    # Формируем сообщение
    for meal_type in ['breakfast', 'lunch', 'snack', 'dinner']:
        if meal_type in meals_dict:
            meal_name = meal_types.get(meal_type, '📝 Прием пищи')
            message += f"*{meal_name}:*\n"

            for item in meals_dict[meal_type]:
                message += f"• {item['description']} - {int(item['calories'])} ккал\n"

            message += "\n"

    message += f"📊 *Итого за день:* {int(total_calories)} ккал\n\n"
    message += "Приятного аппетита! 🍴\n\n"
    message += "*Команды:* /menu - обновить, /notifications - настройки"

    return message


async def send_telegram_message_async(chat_id, message):
    """Асинхронная отправка сообщения в Telegram"""
    try:
        await application.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
        print(f"✅ Сообщение отправлено в {chat_id}")
    except Exception as e:
        print(f"❌ Ошибка отправки в {chat_id}: {e}")


@shared_task
def check_all_reminders():
    """Проверяем и отправляем все уведомления"""
    print("🎯 Celery: НАЧАЛО ПРОВЕРКИ УВЕДОМЛЕНИЙ")

    telegram_users = TelegramUser.objects.select_related(
        'user', 'user__notification_settings'
    ).all()

    print(f"🔍 ВСЕГО Telegram пользователей в базе: {telegram_users.count()}")

    active_users = 0
    for telegram_user in telegram_users:
        try:
            print(
                f"👤 Проверяем: {telegram_user.user.username} (ID: {telegram_user.telegram_id})")

            settings = telegram_user.user.notification_settings

            if not settings.is_subscribed:
                print("   ⏭️  Пропускаем - уведомления выключены")
                continue

            active_users += 1

            # Утреннее напоминание
            morning_time = is_reminder_time(telegram_user.user, 'morning')
            print(f"   🌅 Утреннее время: {morning_time}")

            if morning_time and settings.send_morning_reminder:
                print(f"   📨 ОТПРАВЛЯЕМ УТРЕННЕЕ УВЕДОМЛЕНИЕ!")
                asyncio.run(send_morning_reminder_async(telegram_user))

            # Вечернее напоминание
            evening_time = is_reminder_time(telegram_user.user, 'evening')
            print(f"   🌙 Вечернее время: {evening_time}")

            if evening_time and settings.send_evening_reminder:
                print(f"   📨 ОТПРАВЛЯЕМ ВЕЧЕРНЕЕ УВЕДОМЛЕНИЕ!")
                asyncio.run(send_evening_reminder_async(telegram_user))

        except Exception as e:
            print(f"❌ Ошибка у {telegram_user.user.username}: {e}")

    print(f"✅ ПРОВЕРКА ЗАВЕРШЕНА. Активных пользователей: {active_users}")


