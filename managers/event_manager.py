import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

class EventManager:
    """Менеджер для работы с событиями"""
    
    @staticmethod
    def create_event_id() -> str:
        """Создает уникальный ID для события"""
        return str(int(datetime.now().timestamp()))
    
    @staticmethod
    def get_storage_key(date_str: str, event_type: str) -> str:
        """Возвращает ключ для хранения события"""
        if event_type == 'yearly':
            date_parts = date_str.split('-')
            return f"yearly_{date_parts[1]}-{date_parts[2]}"
        return date_str
    
    @staticmethod
    def calculate_next_date(storage_key: str, event_type: str) -> Optional[datetime]:
        """Вычисляет следующую дату для события"""
        today = datetime.now().date()
        
        try:
            if event_type == 'yearly':
                month_day = storage_key.replace('yearly_', '')
                current_year = today.year
                next_date = datetime.strptime(f"{current_year}-{month_day}", "%Y-%m-%d").date()
                
                if next_date < today:
                    next_date = datetime.strptime(f"{current_year + 1}-{month_day}", "%Y-%m-%d").date()
                return next_date
            else:
                return datetime.strptime(storage_key, "%Y-%m-%d").date()
        except ValueError as e:
            logger.error(f"Ошибка вычисления даты {storage_key}: {e}")
            return None

    @staticmethod
    def add_event_to_storage(events: Dict, event_data: Dict) -> bool:
        """Добавляет событие в хранилище с новой структурой"""
        try:
            channel_id = event_data['channel_id']
            storage_key = EventManager.get_storage_key(event_data['original_date'], event_data['event_type'])
            
            if channel_id not in events:
                events[channel_id] = {
                    'channel_name': event_data['channel_name'],
                    'events': {}
                }
            
            if storage_key not in events[channel_id]['events']:
                events[channel_id]['events'][storage_key] = []
            
            event_copy = event_data.copy()
            event_copy.pop('channel_id', None)
            event_copy.pop('channel_name', None)
            
            events[channel_id]['events'][storage_key].append(event_copy)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления события в хранилище: {e}")
            return False

    @staticmethod
    def get_all_events(events: Dict) -> List[Dict]:
        """Получает все события из новой структуры"""
        all_events = []
        for channel_id, channel_data in events.items():
            for date_key, event_list in channel_data['events'].items():
                for event in event_list:
                    event_with_channel = event.copy()
                    event_with_channel['channel_id'] = channel_id
                    event_with_channel['channel_name'] = channel_data['channel_name']
                    all_events.append(event_with_channel)
        return all_events

    @staticmethod
    def get_events_for_channel(events: Dict, channel_id: str) -> List[Dict]:
        """Получает события для конкретного канала"""
        if channel_id not in events:
            return []
        
        channel_events = []
        for date_key, event_list in events[channel_id]['events'].items():
            for event in event_list:
                event_with_channel = event.copy()
                event_with_channel['channel_id'] = channel_id
                event_with_channel['channel_name'] = events[channel_id]['channel_name']
                channel_events.append(event_with_channel)
        
        return channel_events

    @staticmethod
    def delete_event_by_id(events: Dict, event_id: str, user_id: str, user_channel_ids: Set[str]) -> bool:
        """Удаляет событие по ID из новой структуры"""
        for channel_id, channel_data in events.items():
            for date_key in list(channel_data['events'].keys()):
                for i, event in enumerate(channel_data['events'][date_key]):
                    if (event['id'] == event_id and 
                        (event['created_by'] == user_id or channel_id in user_channel_ids)):
                        
                        del channel_data['events'][date_key][i]
                        
                        if not channel_data['events'][date_key]:
                            del channel_data['events'][date_key]
                        
                        if not channel_data['events']:
                            del events[channel_id]
                        
                        return True
        return False
    