from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from django.utils import timezone
import datetime
from .utils import generate_personal_menu_message
from asgiref.sync import sync_to_async


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    keyboard = [
        [InlineKeyboardButton("📅 Меню на сегодня",
                              callback_data="today_menu")],
        [InlineKeyboardButton("📖 Открыть дневник",
                              callback_data="open_diary")],
        [InlineKeyboardButton("ℹ️  Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Привет, {user.first_name}! 🍏\n\n"
        "Я твой помощник по питанию!\n"
        "Я могу:\n"
        "• Показать меню на сегодня\n"
        "• Открыть дневник питания\n"
        "• Напомнить о приемах пищи\n\n"
        "Выбери что тебя интересует:",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📋 Доступные команды:\n"
        "/start - Главное меню\n"
        "/menu - Меню на сегодня\n"
        "/diary - Открыть дневник\n"
        "/help - Эта справка"
    )


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data == "today_menu":
        await show_today_menu(update, context)
    elif query.data == "tomorrow_menu":
        await show_tomorrow_menu(update, context)
    elif query.data == "open_diary":
        await open_diary_link(update, context)
    elif query.data == "help":
        await show_help(update, context)
    elif query.data == "main_menu":
        await main_menu(update, context)
    elif query.data == "open_site_info":
        await show_site_info(update, context)


async def show_today_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать персональное меню на сегодня"""
    today = timezone.now().date()

    try:
        from .utils import generate_personal_menu_message_async, get_first_user_async

        # Асинхронно получаем первого пользователя
        user = await get_first_user_async()

        if user:
            menu_message = await generate_personal_menu_message_async(user, today)
        else:
            menu_message = "❌ В системе нет пользователей. Сначала зарегистрируйтесь на сайте."

    except Exception as e:
        menu_message = f"🍽️ Ошибка загрузки вашего меню: {e}"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="today_menu")],
        [InlineKeyboardButton("ℹ️ О сайте", callback_data="open_site_info")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(menu_message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(menu_message, reply_markup=reply_markup, parse_mode='Markdown')


async def find_telegram_user(telegram_id):
    """Находит пользователя по Telegram ID"""
    from nutrition_app.models import TelegramUser
    try:
        return TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return None


@sync_to_async
def find_telegram_user_async(telegram_id):
    """Асинхронная версия поиска пользователя по Telegram ID"""
    from nutrition_app.models import TelegramUser
    try:
        return TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return None


async def show_tomorrow_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню на завтра"""
    tomorrow = timezone.now().date() + datetime.timedelta(days=1)

    # Аналогично сегодняшнему меню
    from django.contrib.auth.models import User
    try:
        user = User.objects.first()
        menu_message = generate_personal_menu_message(user, tomorrow)
    except:
        menu_message = f"🍽️ Меню на {tomorrow.strftime('%d.%m.%Y')}:\n\nДанные скоро появятся!"

    keyboard = [
        [InlineKeyboardButton("📅 Меню на сегодня",
                              callback_data="today_menu")],
        [InlineKeyboardButton("📖 Открыть дневник",
                              callback_data="open_diary")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(menu_message, reply_markup=reply_markup)


async def open_diary_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ссылка на дневник"""
    today = timezone.now().date()

    # Для локальной разработки - localhost
    diary_url = f"http://localhost:8000/diary/?date={today}"

    keyboard = [
        # [InlineKeyboardButton("📅 Открыть дневник", url=diary_url)],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        f"Нажми кнопку ниже чтобы открыть дневник питания на {today.strftime('%d.%m.%Y')}:",
        reply_markup=reply_markup
    )


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать справку"""
    message = (
        "🤖 Nutrition Bot Help\n\n"
        "Я помогу тебе следить за питанием:\n\n"
        "📅 **Меню на сегодня** - посмотри что сегодня в плане питания\n"
        "📖 **Дневник питания** - открой веб-версию дневника\n"
        "🔔 **Напоминания** - скоро я буду присылать тебе напоминания о приемах пищи\n\n"
        "Для начала работы используй /start"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(message, reply_markup=reply_markup)


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    keyboard = [
        [InlineKeyboardButton("📅 Меню на сегодня",
                              callback_data="today_menu")],
        [InlineKeyboardButton("📖 Открыть дневник",
                              callback_data="open_diary")],
        [InlineKeyboardButton("ℹ️  Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        "🍏 Главное меню Nutrition Bot:",
        reply_markup=reply_markup
    )


async def show_site_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает информацию о сайте"""
    message = (
        "🌐 **Доступ к сайту:**\n\n"
        "Для работы с персональным планом питания:\n"
        "1. Перейдите по адресу: http://localhost:8000\n"
        "2. Зарегистрируйтесь или войдите\n"
        "3. Составьте свой план питания\n"
        "4. Вернитесь в бота для просмотра\n\n"
        "📱 *Сайт работает только на локальном компьютере*"
    )

    keyboard = [
        [InlineKeyboardButton("📅 Меню на сегодня",
                              callback_data="today_menu")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
