
from datetime import datetime
from typing import Optional

class DateUtils:
    """Утилиты для работы с датами"""
    
    DAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    DAYS_FULL = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    @classmethod
    def get_weekday_short(cls, date_str: str) -> Optional[str]:
        """Получить короткое название дня недели"""
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            return cls.DAYS_SHORT[date_obj.weekday()]
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def get_weekday_full(cls, date_str: str) -> Optional[str]:
        """Получить полное название дня недели"""
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            return cls.DAYS_FULL[date_obj.weekday()]
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def format_date_with_weekday(cls, date_str: str) -> str:
        """Форматировать дату с днем недели"""
        weekday = cls.get_weekday_short(date_str)
        if weekday:
            return f"{date_str} ({weekday})"
        return date_str
