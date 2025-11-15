from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from django.utils import timezone
from datetime import datetime, date
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)

# ===== ОСНОВНЫЕ КОМАНДЫ =====


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню с кнопками"""
    keyboard = [
        [InlineKeyboardButton("📅 Меню на сегодня",
                              callback_data="today_menu")],
        [InlineKeyboardButton("🔗 Перейти на сайт",
                              callback_data="go_to_site")],
        [InlineKeyboardButton("⚙️ Настройки уведомлений",
                              callback_data="settings")],
        [InlineKeyboardButton("🔗 Привязать аккаунт",
                              callback_data="connect_account")]
    ]

    message = (
        f"Привет, {update.effective_user.first_name}! 🍏\n\n"
        "Я твой помощник по правильному питанию!\n\n"
        "📋 *Что я умею:*\n"
        "• Показывать твое меню на сегодня\n"
        "• Напоминать о приемах пищи\n"
        "• Помогать следить за питанием\n\n"
        "Выбери действие ниже 👇"
    )

    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /menu - показывает главное меню"""
    await show_main_menu(update)

# ===== ГЛАВНОЕ МЕНЮ =====


async def show_main_menu(update: Update):
    """Показывает главное меню с кнопками"""
    keyboard = [
        [InlineKeyboardButton("📅 Меню на сегодня",
                              callback_data="today_menu")],
        [InlineKeyboardButton("📋 Меню на завтра",
                              callback_data="tomorrow_menu")],
        [InlineKeyboardButton("🔗 Перейти на сайт",
                              callback_data="go_to_site")],
        [InlineKeyboardButton("⚙️ Настройки уведомлений",
                              callback_data="settings")],
        [InlineKeyboardButton("🔗 Привязать аккаунт",
                              callback_data="connect_account")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]

    message = "🍏 *Главное меню*\n\nВыберите действие:"

    await _send_or_edit_message(update, message, keyboard, parse_mode='Markdown')

# ===== МЕНЮ ПИТАНИЯ =====


async def show_today_menu(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Показывает меню на сегодня"""
    today = timezone.now().date()
    await _show_menu_for_date(update, today, "Сегодня")


async def show_tomorrow_menu(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Показывает меню на завтра"""
    tomorrow = timezone.now().date() + timezone.timedelta(days=1)
    await _show_menu_for_date(update, tomorrow, "Завтра")


async def _show_menu_for_date(update: Update, target_date: date, date_label: str):
    """Показывает меню на указанную дату"""
    try:
        # Получаем данные меню
        menu_data = await _get_menu_data(target_date)

        if menu_data:
            message = f"🍽️ *Меню на {date_label}* ({target_date.strftime('%d.%m.%Y')})\n\n{menu_data}"
        else:
            message = f"📝 *На {date_label} ({target_date.strftime('%d.%m.%Y')}) меню не составлено*\n\nЗайдите на сайт чтобы составить персональный план питания!"

    except Exception as e:
        logger.error(f"Ошибка получения меню: {e}")
        message = "❌ Не удалось загрузить меню. Попробуйте позже."

    keyboard = [
        [InlineKeyboardButton(
            "🔄 Обновить", callback_data="today_menu" if date_label == "Сегодня" else "tomorrow_menu")],
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")]
    ]

    await _send_or_edit_message(update, message, keyboard, parse_mode='Markdown')


@sync_to_async
def _get_menu_data(target_date: date) -> str:
    """Получает данные меню из базы (заглушка - замени на реальную логику)"""
    # ЗАГЛУШКА - здесь будет реальная логика получения меню
    menu_examples = {
        'breakfast': "🥣 Овсяная каша с ягодами - 350 ккал",
        'lunch': "🍗 Куриная грудка с гречкой - 450 ккал",
        'snack': "🍎 Яблоко и йогурт - 150 ккал",
        'dinner': "🐟 Рыба на пару с овощами - 400 ккал"
    }

    menu_text = ""
    for meal_type, dish in menu_examples.items():
        menu_text += f"• {dish}\n"

    menu_text += f"\n📊 *Итого: ~1350 ккал*"
    return menu_text

# ===== ПЕРЕХОД НА САЙТ =====


async def go_to_site(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Заглушка для перехода на сайт"""
    message = (
        "🌐 *Переход на сайт*\n\n"
        "Для локального тестирования:\n\n"
        "📍 *Вы успешно перешли на сайт!*\n\n"
        "В реальной версии здесь будет ссылка на ваш сайт с планом питания."
    )

    keyboard = [
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")],
        [InlineKeyboardButton("📅 Меню на сегодня", callback_data="today_menu")]
    ]

    await _send_or_edit_message(update, message, keyboard, parse_mode='Markdown')

# ===== ПРИВЯЗКА АККАУНТА =====


async def connect_account(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Привязка аккаунта через токен"""
    message = (
        "🔗 *Привязка аккаунта*\n\n"
        "Чтобы привязать Telegram к вашей учетной записи:\n\n"
        "1. Зайдите в личный кабинет на сайте\n"
        "2. В разделе 'Привязка Telegram' получите токен\n"
        "3. Отправьте команду:\n"
        "`/connect ВАШ_ТОКЕН`\n\n"
        "Пример: `/connect abc123def456`\n\n"
        "После привязки вы сможете получать персональные уведомления!"
    )

    keyboard = [
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")],
        [InlineKeyboardButton("🌐 Перейти на сайт", callback_data="go_to_site")]
    ]

    await _send_or_edit_message(update, message, keyboard, parse_mode='Markdown')

# ===== НАСТРОЙКИ УВЕДОМЛЕНИЙ =====


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Настройки уведомлений"""
    message = (
        "⚙️ *Настройки уведомлений*\n\n"
        "Здесь вы можете настроить напоминания о приемах пищи:\n\n"
        "• 🍳 Завтрак (09:00)\n"
        "• 🍗 Обед (12:00)\n"
        "• 🍎 Перекус (16:00)\n"
        "• 🐟 Ужин (19:00)\n\n"
        "Для настройки используйте кнопки ниже:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🍳 Завтрак", callback_data="toggle_breakfast"),
            InlineKeyboardButton("🍗 Обед", callback_data="toggle_lunch")
        ],
        [
            InlineKeyboardButton("🍎 Перекус", callback_data="toggle_snack"),
            InlineKeyboardButton("🐟 Ужин", callback_data="toggle_dinner")
        ],
        [InlineKeyboardButton("🔔 Вкл/Выкл все", callback_data="toggle_all")],
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")]
    ]

    await _send_or_edit_message(update, message, keyboard, parse_mode='Markdown')

# ===== ПОМОЩЬ =====


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Справка по боту"""
    message = (
        "ℹ️ *Помощь по боту*\n\n"
        "📋 *Основные команды:*\n"
        "/start - Главное меню\n"
        "/menu - Показать меню\n"
        "/connect - Привязать аккаунт\n\n"

        "🍽️ *Функционал:*\n"
        "• Просмотр меню питания\n"
        "• Напоминания о приемах пищи\n"
        "• Персональные рекомендации\n\n"

        "⚙️ *Настройки:*\n"
        "Вы можете настроить уведомления для каждого приема пищи отдельно.\n\n"

        "Для навигации используйте кнопки меню!"
    )

    keyboard = [
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]

    await _send_or_edit_message(update, message, keyboard, parse_mode='Markdown')

# ===== ОБРАБОТЧИК КНОПОК =====


async def handle_all_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех callback кнопок"""
    query = update.callback_query
    await query.answer()

    handlers = {
        "main_menu": lambda u, c: show_main_menu(u),
        "today_menu": lambda u, c: show_today_menu(u),
        "tomorrow_menu": lambda u, c: show_tomorrow_menu(u),
        "go_to_site": lambda u, c: go_to_site(u),
        "settings": lambda u, c: show_settings(u),
        "connect_account": lambda u, c: connect_account(u),
        "help": lambda u, c: show_help(u),
        
        # Настройки уведомлений - эти функции принимают context
        "toggle_breakfast": _toggle_breakfast,
        "toggle_lunch": _toggle_lunch,
        "toggle_snack": _toggle_snack,
        "toggle_dinner": _toggle_dinner,
        "toggle_all": _toggle_all,
    }

    handler = handlers.get(query.data)
    if handler:
        await handler(update, context)
    else:
        # Если кнопка не найдена
        await query.edit_message_text("❌ Эта функция временно недоступна")
        await show_main_menu(update)

# ===== ФУНКЦИИ ПЕРЕКЛЮЧЕНИЯ НАСТРОЕК =====


async def _toggle_breakfast(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Переключение уведомлений завтрака"""
    await _toggle_setting(update, "Завтрак")


async def _toggle_lunch(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Переключение уведомлений обеда"""
    await _toggle_setting(update, "Обед")


async def _toggle_snack(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Переключение уведомлений перекуса"""
    await _toggle_setting(update, "Перекус")


async def _toggle_dinner(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Переключение уведомлений ужина"""
    await _toggle_setting(update, "Ужин")


async def _toggle_all(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """Переключение всех уведомлений"""
    await _toggle_setting(update, "все уведомления")


async def _toggle_setting(update: Update, setting_name: str):
    """Заглушка для переключения настроек"""
    message = f"⚙️ Настройка '{setting_name}' будет реализована в следующей версии!"

    keyboard = [
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]

    await _send_or_edit_message(update, message, keyboard)

# ===== СЕРВИСНЫЕ ФУНКЦИИ =====


async def _send_or_edit_message(update, message, keyboard=None, **kwargs):
    """Универсальная отправка/редактирование сообщения"""
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=reply_markup,
                **kwargs
            )
        except Exception as e:
            # Если не удалось редактировать (например, сообщение слишком старое)
            logger.error(f"Ошибка редактирования сообщения: {e}")
            await update.callback_query.message.reply_text(
                message,
                reply_markup=reply_markup,
                **kwargs
            )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            **kwargs
        )

# ===== КОМАНДА CONNECT =====


async def connect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /connect для привязки аккаунта"""
    if not context.args:
        # Если токен не указан, показываем инструкцию
        await connect_account(update)
        return

    token = context.args[0]
    await _process_telegram_link(update, token)


async def _process_telegram_link(update: Update, token: str):
    """Обработка привязки Telegram аккаунта"""
    from nutrition_app.models import TelegramLinkToken, TelegramUser

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
        success_message = (
            f"{result_message}\n\n"
            f"👋 Привет, {user.first_name}!\n\n"
            f"Теперь вы будете получать:\n"
            f"• 📅 Уведомления о меню питания\n"
            f"• 🔔 Напоминания о приемах пищи\n"
            f"• 📊 Статистику и советы\n\n"
            f"Настройте уведомления в разделе 'Настройки'!"
        )
        await update.message.reply_text(success_message, parse_mode='Markdown')

        # Показываем главное меню после успешной привязки
        await show_main_menu(update)
    else:
        await update.message.reply_text(result_message)
        await show_main_menu(update)
