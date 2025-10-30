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

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("menu", handlers.show_today_menu))
    application.add_handler(CommandHandler("tomorrow", handlers.show_tomorrow_menu))
    application.add_handler(CallbackQueryHandler(handlers.handle_button))


# Сразу настраиваем обработчики при импорте
setup_handlers()

# Алиас для обратной совместимости
bot = application
