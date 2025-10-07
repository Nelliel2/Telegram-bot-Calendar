import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from utils.data_manager import DataManager

logger = logging.getLogger(__name__)

class ChannelManager:
    """Менеджер для работы с каналами"""
    
    @staticmethod
    def normalize_chat_id(chat_id: Any) -> str:
        """Нормализует Chat ID к правильному формату"""
        try:
            chat_id_str = str(chat_id).strip()
            
            if chat_id_str.startswith('-100') and len(chat_id_str) > 4:
                return chat_id_str
            elif chat_id_str.startswith('-') and chat_id_str[1:].isdigit():
                return chat_id_str
            elif chat_id_str.isdigit():
                return f"-100{chat_id_str}" if len(chat_id_str) > 9 else chat_id_str
            else:
                return chat_id_str
                
        except Exception as e:
            logger.error(f"Ошибка нормализации Chat ID {chat_id}: {e}")
            return str(chat_id)
    
    @staticmethod
    async def get_channel_info(chat_id: str, bot) -> Tuple[bool, Optional[str], str]:
        """Получает информацию о канале или группе"""
        try:
            normalized_id = ChannelManager.normalize_chat_id(chat_id)
            chat = await bot.get_chat(normalized_id)
            
            if chat.type in ['group', 'supergroup']:
                return True, chat.title or "Без названия", str(chat.id)
            else:
                return True, chat.title or "Без названия", normalized_id
                
        except Exception as e:
            logger.error(f"Ошибка получения информации о чате {chat_id}: {e}")
            return False, None, ChannelManager.normalize_chat_id(chat_id)

    @staticmethod
    async def get_user_channels(user_id: str, bot) -> Dict[str, Dict]:
        """Получает каналы, доступные пользователю (где есть бот)"""
        channels = DataManager.load_channels()
        user_channels = {}
        
        all_bot_channels = channels.get('bot_channels', {})
        
        for channel_id, channel_info in all_bot_channels.items():
            try:
                chat_member = await bot.get_chat_member(channel_id, user_id)
                if chat_member.status in ['administrator', 'member', 'creator']:
                    user_channels[channel_id] = channel_info
            except Exception:
                continue
        
        return user_channels

    @staticmethod
    async def add_bot_channel(chat_id: str, chat_title: str, chat_type: str, bot) -> bool:
        """Добавляет канал в список каналов где есть бот"""
        channels = DataManager.load_channels()
        
        if 'bot_channels' not in channels:
            channels['bot_channels'] = {}
        
        normalized_id = ChannelManager.normalize_chat_id(chat_id)
        
        channels['bot_channels'][normalized_id] = {
            'name': chat_title,
            'type': chat_type,
            'id': normalized_id,
            'added_date': datetime.now().isoformat()
        }
        
        return DataManager.save_channels(channels)

    @staticmethod
    async def check_bot_permissions(chat_id: str, bot) -> Dict[str, bool]:
        """Проверяет права бота в канале/группе"""
        try:
            chat_member = await bot.get_chat_member(chat_id, bot.id)
            
            permissions = {
                'can_send_messages': True,
                'can_pin_messages': False,
                'is_administrator': chat_member.status in ['administrator', 'creator']
            }
            
            if permissions['is_administrator']:
                if hasattr(chat_member, 'can_pin_messages'):
                    permissions['can_pin_messages'] = chat_member.can_pin_messages
                else:
                    permissions['can_pin_messages'] = True
            
            return permissions
            
        except Exception as e:
            logger.error(f"Ошибка проверки прав бота в {chat_id}: {e}")
            return {
                'can_send_messages': False,
                'can_pin_messages': False,
                'is_administrator': False
            }
