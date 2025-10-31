import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from django.conf import settings


TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")


application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Функция для регистрации обработчиков


def setup_handlers():
    from . import handlers

    # Основные команды
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("menu", handlers.show_today_menu))
    application.add_handler(CommandHandler("id", handlers.get_my_id))
    application.add_handler(CommandHandler(
        "notifications", handlers.notifications_settings))

    # ОДИН обработчик для ВСЕХ кнопок
    application.add_handler(CallbackQueryHandler(handlers.handle_all_buttons))


# Сразу настраиваем обработчики при импорте
setup_handlers()

# Алиас для обратной совместимости
bot = application
