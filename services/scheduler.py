import asyncio
import logging
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, application):
        self.application = application
        self.notification_service = NotificationService(application)

    async def start(self):
        """Проверка расписания"""
        while True:
            try:
                await self.notification_service.send_event_notifications()
                await self.notification_service.unpin_old_notifications()
            except Exception as e:
                logger.error(f"Ошибка в schedule_checker: {e}")
            
            await asyncio.sleep(60)  
