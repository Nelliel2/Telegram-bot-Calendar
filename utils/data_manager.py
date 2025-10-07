import json
import os
import logging
from typing import Any, Dict
from config import EVENTS_FILE, CHANNELS_FILE

logger = logging.getLogger(__name__)

class DataManager:
    """Менеджер для работы с данными"""
    
    @staticmethod
    def load_data(filename: str, default: Any = None) -> Any:
        """Загружает данные из JSON файла"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки {filename}: {e}")
        return default if default is not None else {}
    
    @staticmethod
    def save_data(data: Any, filename: str) -> bool:
        """Сохраняет данные в JSON файл"""
        try:
            temp_filename = filename + '.tmp'
            
            with open(temp_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # Заменяем оригинальный файл временным
            if os.path.exists(filename):
                os.replace(temp_filename, filename)
            else:
                os.rename(temp_filename, filename)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения {filename}: {e}")
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            return False
    
    @classmethod
    def load_events(cls) -> Dict:
        """Загружает события"""
        return cls.load_data(EVENTS_FILE, {})
    
    @classmethod
    def save_events(cls, events: Dict) -> bool:
        """Сохраняет данные о событии"""
        return cls.save_data(events, EVENTS_FILE)
    
    @classmethod
    def load_channels(cls) -> Dict:
        """Загружает информацию о каналах где есть бот"""
        return cls.load_data(CHANNELS_FILE, {})
    
    @classmethod
    def save_channels(cls, channels: Dict) -> bool:
        """Сохраняет данные о канале"""
        return cls.save_data(channels, CHANNELS_FILE)
