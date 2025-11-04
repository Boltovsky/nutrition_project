from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from django.utils import timezone
import datetime
from asgiref.sync import sync_to_async
import asyncio

# ===== ОСНОВНЫЕ КОМАНДЫ =====


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("📅 Меню на сегодня",
                              callback_data="today_menu")],
        [InlineKeyboardButton("⚙️ Настройки уведомлений",
                              callback_data="settings")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]

    message = (
        f"Привет, {update.effective_user.first_name}! 🍏\n\n"
        "Я твой помощник по питанию!\n"
        "Я могу:\n• Показать меню на сегодня\n• Напомнить о приемах пищи\n• Управлять уведомлениями"
    )

    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по командам"""
    message = (
        "🤖 *Nutrition Bot Help*\n\n"
        "*Команды:*\n"
        "/start - Главное меню\n"
        "/menu - Меню на сегодня\n"
        "/notifications - Настройки уведомлений\n"
        "/id - Ваш Telegram ID\n"
        "/help - Эта справка\n\n"
        "Используйте кнопки для навигации!"
    )
    await _send_or_edit_message(update, message, parse_mode='Markdown')


async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает ID пользователя"""
    message = (
        f"👤 *Ваши ID:*\n\n"
        f"*Telegram ID:* `{update.effective_user.id}`\n"
        f"*Chat ID:* `{update.effective_chat.id}`\n\n"
        f"⚠️ *Используйте для тестирования*"
    )
    await update.message.reply_text(message, parse_mode='Markdown')

# ===== МЕНЮ ПИТАНИЯ =====


async def show_today_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню на сегодня"""
    await _show_menu_for_date(update, timezone.now().date(), "today_menu")


async def show_tomorrow_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню на завтра"""
    tomorrow = timezone.now().date() + datetime.timedelta(days=1)
    await _show_menu_for_date(update, tomorrow, "tomorrow_menu")


async def _show_menu_for_date(update: Update, date, callback_data):
    """Общая функция показа меню на дату"""
    try:
        from .utils import generate_personal_menu_message_async, get_first_user_async
        user = await get_first_user_async()
        menu_message = await generate_personal_menu_message_async(user, date) if user else "❌ Нет пользователей"
    except Exception as e:
        menu_message = f"🍽️ Ошибка загрузки меню: {e}"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=callback_data)],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]

    await _send_or_edit_message(update, menu_message, keyboard, parse_mode='Markdown')

# ===== НАСТРОЙКИ УВЕДОМЛЕНИЙ =====


async def notifications_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню настроек уведомлений"""
    settings = await _get_user_settings(update.effective_user.id)

    if not settings:
        await _send_or_edit_message(update, "❌ Аккаунт не привязан к сайту")
        return

    message = await _build_settings_message(settings)
    keyboard = _build_settings_keyboard()

    await _send_or_edit_message(update, message, keyboard, parse_mode='Markdown')


async def show_updated_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновленный статус настроек"""
    settings = await _get_user_settings(update.effective_user.id)

    if not settings:
        await update.callback_query.edit_message_text("❌ Аккаунт не привязан")
        return

    current_time = timezone.now().strftime('%H:%M:%S')
    message = await _build_status_message(settings, current_time)
    keyboard = _build_settings_keyboard()

    await _send_or_edit_message(update, message, keyboard, parse_mode='Markdown')


async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключение всех уведомлений"""
    await _toggle_setting(update, 'all', "Уведомления")


async def toggle_morning_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключение утренних уведомлений"""
    await _toggle_setting(update, 'morning', "Утренние уведомления")


async def toggle_evening_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключение вечерних уведомлений"""
    await _toggle_setting(update, 'evening', "Вечерние уведомления")


async def _toggle_setting(update: Update, setting_type, setting_name):
    """Общая функция переключения настроек"""
    @sync_to_async
    def toggle_and_save(telegram_id, s_type):
        from nutrition_app.models import TelegramUser, UserNotificationSettings
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
            settings = UserNotificationSettings.objects.get_or_create(
                user=telegram_user.user)[0]

            if s_type == 'all':
                settings.is_subscribed = not settings.is_subscribed
            elif s_type == 'morning':
                settings.send_morning_reminder = not settings.send_morning_reminder
            elif s_type == 'evening':
                settings.send_evening_reminder = not settings.send_evening_reminder

            settings.save()
            return settings
        except:
            return None

    settings = await toggle_and_save(update.effective_user.id, setting_type)

    if not settings:
        await update.callback_query.edit_message_text("❌ Ошибка")
        return

    if setting_type == 'all':
        is_enabled = settings.is_subscribed
    else:
        is_enabled = getattr(settings, f'send_{setting_type}_reminder')

    status = "ВКЛЮЧЕНЫ" if is_enabled else "ВЫКЛЮЧЕНЫ"

    await update.callback_query.edit_message_text(f"✅ {setting_name} {status}")
    await asyncio.sleep(1)
    await notifications_settings(update)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("📅 Меню на сегодня",
                              callback_data="today_menu")],
        [InlineKeyboardButton("⚙️ Настройки уведомлений",
                              callback_data="settings")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    await _send_or_edit_message(update, "🍏 Главное меню:", keyboard)


async def show_site_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о сайте"""
    message = (
        "🌐 *Доступ к сайту:*\n\n"
        "1. Перейдите: http://localhost:8000\n"
        "2. Зарегистрируйтесь/войдите\n"
        "3. Составьте план питания\n\n"
        "📱 *Сайт работает локально*"
    )
    await _send_or_edit_message(update, message, parse_mode='Markdown')


async def open_diary_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ссылка на дневник"""
    today = timezone.now().date()
    message = f"📖 Откройте дневник на {today.strftime('%d.%m.%Y')} на сайте"
    await _send_or_edit_message(update, message)

# ===== ОБРАБОТЧИК КНОПОК =====


async def handle_all_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех кнопок"""
    query = update.callback_query
    await query.answer()

    handlers = {
        # Основные кнопки
        "today_menu": show_today_menu,
        "tomorrow_menu": show_tomorrow_menu,
        "open_diary": open_diary_link,
        "open_site_info": show_site_info,
        "help": help_command,
        "main_menu": main_menu,
        "settings": notifications_settings,
        # Кнопки уведомлений
        "toggle_notifications": toggle_notifications,
        "toggle_morning": toggle_morning_reminders,
        "toggle_evening": toggle_evening_reminders,
        "notifications_status": show_updated_status,
    }

    handler = handlers.get(query.data)
    if handler:
        await handler(update, context)

# ===== СЕРВИСНЫЕ ФУНКЦИИ =====


async def _send_or_edit_message(update, message, keyboard=None, **kwargs):
    """Универсальная отправка/редактирование сообщения"""
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, **kwargs)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, **kwargs)


@sync_to_async
def _get_user_settings(telegram_id):
    """Получение настроек пользователя"""
    from nutrition_app.models import TelegramUser, UserNotificationSettings
    try:
        telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
        return UserNotificationSettings.objects.get_or_create(user=telegram_user.user)[0]
    except:
        return None


async def _build_settings_message(settings):
    """Формирование сообщения с настройками"""
    status_icon = "🔔" if settings.is_subscribed else "🔕"
    morning_icon = "✅" if settings.send_morning_reminder else "❌"
    evening_icon = "✅" if settings.send_evening_reminder else "❌"

    return (
        f"{status_icon} *Настройки уведомлений:*\n\n"
        f"*Общие:* {'ВКЛ' if settings.is_subscribed else 'ВЫКЛ'}\n"
        f"*Утренние:* {morning_icon}\n"
        f"*Вечерние:* {evening_icon}\n\n"
        f"Используйте кнопки для управления:"
    )


async def _build_status_message(settings, current_time):
    """Формирование сообщения статуса"""
    return (
        f"🔔 *Настройки уведомлений*\n🕐 *Обновлено:* {current_time}\n\n"
        f"*Текущий статус:*\n"
        f"• Общие: {'ВКЛ' if settings.is_subscribed else 'ВЫКЛ'}\n"
        f"• Утренние: {'ВКЛ' if settings.send_morning_reminder else 'ВЫКЛ'}\n"
        f"• Вечерние: {'ВКЛ' if settings.send_evening_reminder else 'ВЫКЛ'}"
    )


def _build_settings_keyboard():
    """Формирование клавиатуры настроек"""
    return [
        [InlineKeyboardButton(
            "🔔 Вкл/Выкл все", callback_data="toggle_notifications")],
        [InlineKeyboardButton("🌅 Утренние", callback_data="toggle_morning")],
        [InlineKeyboardButton("🌙 Вечерние", callback_data="toggle_evening")],
        [InlineKeyboardButton(
            "🔄 Статус", callback_data="notifications_status")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]


async def connect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Привязка Telegram аккаунта к учетной записи"""
    if not context.args:
        message = (
            "🔗 *Привязка аккаунта*\n\n"
            "Для привязки Telegram к вашей учетной записи:\n\n"
            "1. Зайдите в личный кабинет на сайте\n"
            "2. В разделе 'Привязка Telegram' получите токен\n"
            "3. Отправьте команду:\n"
            "`/connect ВАШ_ТОКЕН`\n\n"
            "Пример: `/connect abc123def456`"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
        return

    token = context.args[0]
    await _process_telegram_link(update, token)


async def _process_telegram_link(update: Update, token: str):
    """Обработка привязки Telegram аккаунта"""
    from nutrition_app.models import TelegramLinkToken, TelegramUser
    from asgiref.sync import sync_to_async

    @sync_to_async
    def link_telegram_account(telegram_id, token_str):
        try:
            # Ищем валидный токен
            link_token = TelegramLinkToken.objects.filter(
                token=token_str,
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()

            if not link_token:
                return None, "❌ Токен не найден или просрочен"

            # Проверяем, не привязан ли уже этот Telegram
            if TelegramUser.objects.filter(telegram_id=telegram_id).exists():
                return None, "❌ Этот Telegram аккаунт уже привязан"

            # Создаем привязку
            TelegramUser.objects.create(
                user=link_token.user,
                telegram_id=telegram_id,
                chat_id=update.effective_chat.id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name,
                is_subscribed=True
            )

            # Помечаем токен как использованный
            link_token.is_used = True
            link_token.save()

            return link_token.user, "✅ Аккаунт успешно привязан!"

        except Exception as e:
            return None, f"❌ Ошибка привязки: {str(e)}"

    user, result_message = await link_telegram_account(update.effective_user.id, token)

    if user:
        # Дополнительное сообщение при успешной привязке
        success_message = (
            f"{result_message}\n\n"
            f"👋 Привет, {user.first_name}!\n\n"
            f"Теперь вы будете получать:\n"
            f"• 📅 Уведомления о меню питания\n"
            f"• 🔔 Напоминания о приемах пищи\n"
            f"• 📊 Статистику и советы\n\n"
            f"Настройте уведомления командой: /notifications"
        )
        await update.message.reply_text(success_message, parse_mode='Markdown')
    else:
        await update.message.reply_text(result_message)
