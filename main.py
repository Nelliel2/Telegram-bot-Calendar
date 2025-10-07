import logging
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from utils.calendar import Calendar
from utils.data_manager import DataManager
from managers.channel_manager import ChannelManager
from managers.event_manager import EventManager
from handlers.event_handlers import EventHandlers
from handlers.channel_handlers import ChannelHandlers
from services.scheduler import Scheduler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_startup(application):
    """Запуск после старта бота"""
    global app
    app = application
    
    commands = [
        ("start", "🔍 Показать справку"),
        ("addevent", "🗓️ Добавить событие"),
        ("events", "👁️ Показать события"),
        ("deleteevent", "🗑️ Удалить событие"),
        ("mychannels", "📢 Мои каналы"),
        ("checkperms", "🔐 Проверить права"),
    ]
    await application.bot.set_my_commands(commands)
    
    await application.bot.set_my_description(
        "Бот для управления событиями в Telegram каналах и группах. "
        "Создавайте события, получайте уведомления и автоматически закрепляйте сообщения. "
        "Поддерживает разовые и ежегодные события."
    )
    
    await application.bot.set_my_short_description("📅 Управление событиями каналов")
    
    scheduler = Scheduler(application)
    asyncio.create_task(scheduler.start())

def main():
    global application
    
    application = Application.builder().token(BOT_TOKEN).build()

    calendar = Calendar()
    data_manager = DataManager()
    channel_manager = ChannelManager()
    event_manager = EventManager()

    event_handlers = EventHandlers(calendar, data_manager, channel_manager, event_manager)
    channel_handlers = ChannelHandlers(channel_manager)
    
    handlers = [
        CommandHandler("start", event_handlers.start_command),
        CommandHandler("addevent", event_handlers.add_event_command),
        CommandHandler("events", event_handlers.events_command),
        CommandHandler("deleteevent", event_handlers.delete_event_command),
        CommandHandler("mychannels", event_handlers.my_channels_command),
        CommandHandler("cancel", event_handlers.cancel_command),
        CommandHandler("checkperms", event_handlers.check_permissions_command),
        
        CallbackQueryHandler(event_handlers._handle_channel_selection, pattern="^select_channel_"),
        CallbackQueryHandler(event_handlers.handle_calendar_callback, pattern="^calendar_"),
        CallbackQueryHandler(event_handlers.handle_calendar_callback, pattern="^event_type_"),
        CallbackQueryHandler(event_handlers.handle_calendar_callback, pattern="^event_cancel"),
        CallbackQueryHandler(event_handlers.handle_events_callback, pattern="^view_events_"),
        CallbackQueryHandler(event_handlers.handle_delete_confirmation, pattern="^delete_"),
        
        MessageHandler(filters.TEXT & ~filters.COMMAND, event_handlers.handle_event_description),
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, channel_handlers.track_bot_added_to_chat),
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    application.post_init = post_startup

    application.run_polling()

if __name__ == "__main__":
    main()