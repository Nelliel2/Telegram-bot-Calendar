import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple
from utils.data_manager import DataManager
from managers.channel_manager import ChannelManager

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, application):
        self.application = application

    async def send_event_notifications(self):
        """Отправка уведомлений о событиях из новой структуры"""
            
        events = DataManager.load_events()
        today = datetime.now().strftime("%Y-%m-%d")
        today_md = today[5:]
        current_year = datetime.now().year
        has_changes = False
        
        for channel_id, channel_data in events.items():
            channel_name = channel_data.get('channel_name', 'Неизвестный канал')
            
            if today in channel_data['events']:
                for i, event in enumerate(channel_data['events'][today]):
                    if not event.get('notified', False):
                        updated_event, success = await self._send_and_pin_notification(
                            event, channel_id, channel_name, today, "🎯 СЕГОДНЯ", events
                        )
                        
                        if success and updated_event:
                            events[channel_id]['events'][today][i] = updated_event
                            has_changes = True
            
            yearly_key = f"yearly_{today_md}"
            if yearly_key in channel_data['events']:
                for i, event in enumerate(channel_data['events'][yearly_key]):
                    last_notified_year = event.get('last_notified_year')
                    
                    if last_notified_year != current_year:
                        updated_event, success = await self._send_and_pin_notification(
                            event, channel_id, channel_name, f"{current_year}-{today_md}", "🎉 СЕГОДНЯ", events
                        )
                        
                        if success and updated_event:
                            events[channel_id]['events'][yearly_key][i] = updated_event
                            has_changes = True
        
        if has_changes:
            DataManager.save_events(events)

    async def _send_and_pin_notification(self, event: Dict, channel_id: str, channel_name: str, 
                                    original_date: str, prefix: str, events: Dict) -> Tuple[Dict, bool]:
        """Отправляет и закрепляет уведомление, возвращает обновленное событие"""
        try:
            permissions = await ChannelManager.check_bot_permissions(channel_id, self.application.bot)
            
            if not permissions['can_send_messages']:
                return event, False
            
            message = f"{prefix}: {event['description']}"
            
            sent_message = await self.application.bot.send_message(
                chat_id=channel_id,
                text=message
            )
            
            updated_event = event.copy()
            
            if event['event_type'] == 'single':
                updated_event['notified'] = True
            else:
                updated_event['last_notified_year'] = datetime.now().year
            
            if permissions['can_pin_messages']:
                try:
                    await self.application.bot.pin_chat_message(
                        chat_id=channel_id,
                        message_id=sent_message.message_id,
                        disable_notification=False
                    )
                    
                    updated_event['pinned_message_id'] = sent_message.message_id
                    updated_event['pinned_date'] = datetime.now().strftime("%Y-%m-%d")
                    
                except Exception:
                    updated_event['pinned_message_id'] = None
                    updated_event['pinned_date'] = None
            else:
                updated_event['pinned_message_id'] = None
                updated_event['pinned_date'] = None
            
            return updated_event, True
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления в {channel_name}: {e}")
            return event, False
        
    async def unpin_old_notifications(self):
        """Открепление старых уведомлений"""
        if self.application is None:
            return
            
        events = DataManager.load_events()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        has_changes = False

        for channel_id, channel_data in events.items():
            channel_name = channel_data.get('channel_name', 'Неизвестный канал')
            
            permissions = await ChannelManager.check_bot_permissions(channel_id, self.application.bot)
            
            if not permissions['can_pin_messages']:
                continue
            
            for storage_key in channel_data['events']:
                for i, event in enumerate(channel_data['events'][storage_key]):
                    pinned_date = event.get('pinned_date')
                    message_id = event.get('pinned_message_id')
                    
                    if pinned_date == yesterday and message_id:
                        try:
                            await self.application.bot.unpin_chat_message(
                                chat_id=channel_id,
                                message_id=message_id
                            )
                            
                            events[channel_id]['events'][storage_key][i]['pinned_message_id'] = None
                            events[channel_id]['events'][storage_key][i]['pinned_date'] = None
                            has_changes = True
                            
                        except Exception as e:
                            error_msg = str(e)
                            if any(phrase in error_msg.lower() for phrase in ["message to unpin not found", "bad request", "no rights"]):
                                events[channel_id]['events'][storage_key][i]['pinned_message_id'] = None
                                events[channel_id]['events'][storage_key][i]['pinned_date'] = None
                                has_changes = True
        
        if has_changes:
            DataManager.save_events(events)
