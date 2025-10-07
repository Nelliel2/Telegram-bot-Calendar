from datetime import datetime, timedelta
from typing import Optional
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

class Calendar:
    """Упрощенный календарь для выбора дат"""
    
    MONTHS = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    
    @classmethod
    def create_calendar(cls, year: Optional[int] = None, month: Optional[int] = None) -> InlineKeyboardMarkup:
        """Создает календарь для указанного месяца и года"""
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        
        keyboard = []
        
        # Заголовок
        keyboard.append([InlineKeyboardButton(f"{cls.MONTHS[month-1]} {year}", callback_data="ignore")])
        #Дни недели
        keyboard.append([InlineKeyboardButton(day, callback_data="ignore") for day in cls.DAYS])
        
        # Получаем информацию о месяце
        first_day = datetime(year, month, 1)
        next_month = datetime(year + (month // 12), (month % 12) + 1, 1)
        days_in_month = (next_month - timedelta(days=1)).day
        first_weekday = first_day.weekday()
        
        # Создаем дни
        today = now.date()
        is_current_month = (year == now.year and month == now.month)
        week = []
        
        # Пустые ячейки до первого дня
        week.extend([InlineKeyboardButton(" ", callback_data="ignore")] * first_weekday)
        
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            day_text = f"🎯{day}" if (is_current_month and day == today.day) else str(day)
            
            week.append(InlineKeyboardButton(day_text, callback_data=f"calendar_day_{date_str}"))
            
            if len(week) == 7:
                keyboard.append(week)
                week = []
        
        # Заполняем последнюю неделю
        if week:
            week.extend([InlineKeyboardButton(" ", callback_data="ignore")] * (7 - len(week)))
            keyboard.append(week)
        
        # Навигация
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        nav_row = [
            InlineKeyboardButton("←", callback_data=f"calendar_nav_{prev_year}_{prev_month}"),
            InlineKeyboardButton("Сегодня", callback_data="calendar_today"),
            InlineKeyboardButton("→", callback_data=f"calendar_nav_{next_year}_{next_month}")
        ]
        keyboard.append(nav_row)
        
        return InlineKeyboardMarkup(keyboard)
