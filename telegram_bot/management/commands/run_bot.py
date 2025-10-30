from django.core.management.base import BaseCommand
from telegram_bot.bot import application
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run Telegram bot in polling mode'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Telegram bot in polling mode...')
        )
        self.stdout.write('📱 Bot is now listening for messages...')
        self.stdout.write('⏹️  Press Ctrl+C to stop the bot')

        try:

            application.run_polling()

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('✅ Bot stopped successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Bot error: {e}')
            )
            import traceback
            traceback.print_exc()
