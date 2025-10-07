from telegram.ext import ContextTypes
from telegram import Update
from managers.channel_manager import ChannelManager

class ChannelHandlers:
    def __init__(self, channel_manager: ChannelManager):
        self.channel_manager = channel_manager
        
    async def track_bot_added_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отслеживает добавление бота в чаты"""
        if update.message and update.message.new_chat_members:
            for member in update.message.new_chat_members:
                if member.id == context.bot.id:
                    chat = update.effective_chat
                    await ChannelManager.add_bot_channel(
                        chat.id, 
                        chat.title or "Без названия", 
                        chat.type,
                        context.bot
                    )
