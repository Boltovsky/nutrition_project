import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from django.conf import settings

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()


def setup_handlers():
    from . import handlers

    # Основные команды
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("menu", handlers.menu))
    application.add_handler(CommandHandler("help", handlers.show_help))
    application.add_handler(CommandHandler(
        "connect", handlers.connect_command))

    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(handlers.handle_all_buttons))

    print("✅ Обработчики бота настроены!")


# Настраиваем обработчики
setup_handlers()

bot = application
