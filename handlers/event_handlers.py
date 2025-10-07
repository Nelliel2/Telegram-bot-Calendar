from telegram.ext import ContextTypes
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from typing import Dict
import logging
from managers.channel_manager import ChannelManager
from managers.event_manager import EventManager
from telegram.ext import  ContextTypes
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from typing import Dict, List, Optional
from utils.date_utils import DateUtils

logger = logging.getLogger(__name__)

class EventHandlers:
    """Класс для обработчиков бота"""
    def __init__(self, calendar, data_manager, channel_manager, event_manager):
        self.calendar = calendar
        self.data_manager = data_manager
        self.channel_manager = channel_manager
        self.event_manager = event_manager
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(
            "👋 Добро пожаловать! Я бот для управления событиями каналов.\n\n"
            "🗓️ Основные команды:\n"
            "/addevent - Добавить новое событие\n"
            "/events - Просмотреть все события\n"
            "/deleteevent - Удалить событие\n"
            "/mychannels - Показать мои каналы\n\n"
            "/checkperms - Проверить права бота в ваших каналах"
            "📢 Бот автоматически получает доступ ко всем календарям каналов и групп,"
            "в которых вы состоите!\n\n"
            "⏰ Бот автоматически отправляет напоминание о событии в канал и закреляет его!"
        )

    async def check_permissions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверить права бота в каналах"""
        user_id = str(update.effective_user.id)
        
        user_channels = await self.channel_manager.get_user_channels(user_id, context.bot)
        
        if not user_channels:
            await update.message.reply_text("📭 У вас нет общих каналов с ботом.")
            return
        
        response = "🔐 **Права бота в ваших каналах:**\n\n"
        
        for channel_id, channel_info in user_channels.items():
            permissions = await ChannelManager.check_bot_permissions(channel_id, context.bot)
            
            status_icon = "✅" if permissions['can_send_messages'] else "❌"
            pin_status = "✅" if permissions['can_pin_messages'] else "❌"
            admin_status = "✅" if permissions['is_administrator'] else "❌"
            
            response += f"**{channel_info['name']}**\n"
            response += f"  📝 Отправка сообщений: {status_icon}\n"
            response += f"  📌 Закрепление сообщений: {pin_status}\n"
            response += f"  👑 Администратор: {admin_status}\n\n"
        
        response += "💡 **Для полного функционала боту нужны:**\n"
        response += "• Права администратора\n• Разрешение на закрепление сообщений\n"
        response += "• Разрешение на отправку сообщений"
        
        await update.message.reply_text(response, parse_mode='Markdown')

    async def add_event_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать календарь для добавления события"""
        user_id = str(update.effective_user.id)
        
        user_channels = await self.channel_manager.get_user_channels(user_id, context.bot)
        
        if not user_channels:
            await update.message.reply_text(
                "❌ У вас нет общих каналов/групп с ботом.\n\n"
                "💡 Чтобы использовать бота:\n"
                "1. Добавьте бота в канал/группу\n"
                "2. Убедитесь, что вы тоже участник этого канала/группы\n"
                "3. Бот автоматически получит доступ к каналу!\n\n"
                "📋 Используйте /mychannels чтобы посмотреть доступные каналы."
            )
            return
        
        context.user_data['user_channels'] = user_channels
        context.user_data['mode'] = 'adding'
        
        if len(user_channels) > 1:
            keyboard = []
            for chat_id, channel_info in user_channels.items():
                channel_name = channel_info['name']
                keyboard.append([InlineKeyboardButton(channel_name, callback_data=f"select_channel_{chat_id}")])
            
            await update.message.reply_text("📢 Выберите канал для события:", reply_markup=InlineKeyboardMarkup(keyboard))
            context.user_data['waiting_for_channel_selection'] = True
        else:
            chat_id = list(user_channels.keys())[0]
            context.user_data['selected_channel'] = chat_id
            await self._show_calendar(update, context)
    
    async def _show_calendar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать календарь"""
        markup = self.calendar.create_calendar()
        
        if update.callback_query:
            await update.callback_query.message.reply_text("🗓️️ Выберите дату события:", reply_markup=markup)
        else:
            await update.message.reply_text("🗓️️ Выберите дату события:", reply_markup=markup)
    
    async def _handle_channel_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора канала"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("select_channel_"):
            chat_id = query.data.replace("select_channel_", "")
            user_id = str(query.from_user.id)
            
            user_channels = context.user_data.get('user_channels', {})
            if chat_id not in user_channels:
                await query.edit_message_text("❌ Этот канал больше недоступен.")
                return
            
            channel_name = user_channels[chat_id]['name']
            
            context.user_data['selected_channel'] = chat_id
            await query.edit_message_text(f"📢 Выбран канал: {channel_name}")
            await self._show_calendar(update, context)
    
    async def handle_calendar_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback от календаря"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("select_channel_"):
            await self._handle_channel_selection(update, context)
            return
            
        mode = context.user_data.get('mode', 'adding')
        
        if mode == 'deleting':
            await self._handle_delete_calendar_callback(update, context)
        else:
            await self._handle_add_calendar_callback(update, context)
    
    async def _handle_add_calendar_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик календаря для добавления событий"""
        query = update.callback_query
        data = query.data
        
        if data.startswith("calendar_day_") or data == "calendar_today":
            await self._handle_date_selection(update, context)
        elif data.startswith("calendar_nav_"):
            await self._handle_calendar_navigation(update, context)
        elif data.startswith("event_type_"):
            await self._handle_event_type_selection(update, context)
        elif data == "event_cancel":
            await self._handle_event_cancel(update, context)
    
    async def _handle_date_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора даты"""
        query = update.callback_query
        
        if query.data == "calendar_today":
            date_obj = datetime.now()
        else:
            date_str = query.data.replace("calendar_day_", "")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        formatted_date = date_obj.strftime("%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")
        
        user_id = str(query.from_user.id)
        user_channels = context.user_data.get('user_channels', {})
        channel_id = context.user_data.get('selected_channel')
        
        channel_name = user_channels.get(channel_id, {}).get('name', 'Неизвестно')
        
        await query.edit_message_text(f"🗓️ Выбрана дата: {formatted_date}\n📢 Канал: {channel_name}")
        
        context.user_data['selected_date'] = date_str
        context.user_data['waiting_for_event_description'] = True
        
        keyboard = [
            [
                InlineKeyboardButton("🔹 Разовое событие", callback_data="event_type_single"),
                InlineKeyboardButton("🔸 Ежегодное событие", callback_data="event_type_yearly")
            ],
            [InlineKeyboardButton("❌ Отменить", callback_data="event_cancel")]
        ]
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"✏️ Введите описание события для {formatted_date} в канале '{channel_name}':",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _handle_calendar_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик навигации по календарю"""
        query = update.callback_query
        nav_data = query.data.replace("calendar_nav_", "")
        year, month = map(int, nav_data.split("_"))
        markup = self.calendar.create_calendar(year, month)
        await query.edit_message_reply_markup(reply_markup=markup)
    
    async def _handle_event_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора типа события"""
        query = update.callback_query
        await query.answer()
        
        event_type = query.data.replace("event_type_", "")
        context.user_data['event_type'] = event_type
        
        type_text = "🔹 разовое событие" if event_type == "single" else "🔸 ежегодное событие"
        
        context.user_data['waiting_for_event_description'] = True
        
        await query.edit_message_text(f"✅ Выбран тип: {type_text}\n📝 Теперь введите описание события:")
    
    async def _handle_event_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик отмены события"""
        query = update.callback_query
        await query.edit_message_text("❌ Создание события отменено.")
        self.clear_event_context(context)
    
    async def handle_event_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка описания события"""
        user_id = str(update.effective_user.id)
        
        if update.message.text.lower() in ['отмена', 'cancel', 'стоп', 'stop']:
            await update.message.reply_text("❌ Создание события отменено.")
            self.clear_event_context(context)
            return
        
        if context.user_data.get('waiting_for_event_description') and 'selected_date' in context.user_data:
            description = update.message.text
            date_str = context.user_data['selected_date']
            channel_id = context.user_data.get('selected_channel')
            event_type = context.user_data.get('event_type', 'single')
            
            if not channel_id:
                await update.message.reply_text("❌ Ошибка: канал не выбран.")
                self.clear_event_context(context)
                return
            
            success = await self._save_event(description, date_str, channel_id, event_type, user_id, context.bot)
            
            if success:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d.%m.%Y")
                
                user_channels = context.user_data.get('user_channels', {})
                channel_name = user_channels.get(channel_id, {}).get('name', 'Неизвестный канал')
                
                if event_type == 'yearly':
                    response = f"✅ Ежегодное событие добавлено!\n🗓️️ Дата: {formatted_date} (ежегодно)\n📢 Канал: {channel_name}\n📝 Событие: {description}"
                else:
                    response = f"✅ Событие добавлено!\n🗓️️ Дата: {formatted_date}\n📢 Канал: {channel_name}\n📝 Событие: {description}"
                
                await update.message.reply_text(response)
            else:
                await update.message.reply_text("❌ Ошибка при сохранении события.")
            
            self.clear_event_context(context)
    
    async def _save_event(self, description: str, date_str: str, channel_id: str, event_type: str, user_id: str, bot) -> bool:
        """Сохраняет событие в базу данных с новой структурой"""
        success, channel_title, _ = await self.channel_manager.get_channel_info(channel_id, bot)
        if not success:
            return False
        
        events = self.data_manager.load_events()
        event_id = self.event_manager.create_event_id()
        
        event_data = {
            'id': event_id,
            'description': description,
            'created_by': user_id,
            'channel_id': channel_id,
            'channel_name': channel_title,
            'created_at': datetime.now().isoformat(),
            'notified': False,
            'pinned_message_id': None,
            'pinned_date': None,
            'event_type': event_type,
            'original_date': date_str,
            'last_notified_year': None
        }
        
        success = EventManager.add_event_to_storage(events, event_data)
        if success:
            return self.data_manager.save_events(events)
        return False
    
    async def events_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать события"""
        user_id = str(update.effective_user.id)
        events = self.data_manager.load_events()
        
        if not events:
            await update.message.reply_text("📭 Нет запланированных событий.")
            return
        
        user_channels = await self.channel_manager.get_user_channels(user_id, context.bot)
        
        if not user_channels:
            await update.message.reply_text("📭 У вас нет общих каналов с ботом.")
            return
        
        context.user_data['user_channels'] = user_channels
        
        if len(user_channels) > 1 and not context.args:
            keyboard = []
            for chat_id, channel_info in user_channels.items():
                channel_name = channel_info['name']
                keyboard.append([InlineKeyboardButton(f"📢 {channel_name}", callback_data=f"view_events_{chat_id}")])
            
            keyboard.append([InlineKeyboardButton("👁️ Показать все события", callback_data="view_events_all")])
            await update.message.reply_text("📢 Выберите канал для просмотра событий:", reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        channel_id_to_show = None
        if context.args:
            channel_arg = context.args[0]
            normalized_id = self.channel_manager.normalize_chat_id(channel_arg)
            if normalized_id in user_channels:
                channel_id_to_show = normalized_id
        elif len(user_channels) == 1:
            channel_id_to_show = list(user_channels.keys())[0]
        
        if channel_id_to_show:
            await self._show_events_for_channel(update, context, channel_id_to_show, user_channels)
        else:
            await self._show_all_events(update, context, user_channels)
    
    async def _show_events_for_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: str, user_channels: Dict):
        """Показать события для конкретного канала"""
        response = await self._build_events_response(user_channels, context.bot, show_all=False, channel_id=channel_id)
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _show_all_events(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_channels: Dict):
        """Показать все события"""
        response = await self._build_events_response(user_channels, context.bot, show_all=True)
        keyboard = await self._build_channels_keyboard(user_channels, context.bot, current_channel=None)
        
        if isinstance(update, Update) and update.message:
            if keyboard:
                await update.message.reply_text(response, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.edit_message_text(response, parse_mode='Markdown')

    async def handle_events_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback для просмотра событий"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if not data.startswith("view_events_"):
            return
            
        user_id = str(query.from_user.id)
        
        user_channels = await self.channel_manager.get_user_channels(user_id, context.bot)
        
        if not user_channels:
            await query.edit_message_text("📭 У вас нет общих каналов с ботом.")
            return
        
        context.user_data['user_channels'] = user_channels
        
        channel_arg = data.replace("view_events_", "")
        
        if channel_arg == "all":
            await self._show_all_events_callback(update, context, user_channels)
        else:
            if channel_arg in user_channels:
                await self._show_events_for_channel_callback(update, context, channel_arg, user_channels)
            else:
                await query.edit_message_text("❌ Канал не найден.")

    async def _show_events_for_channel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: str, user_channels: Dict):
        """Показать события для канала (callback версия)"""
        query = update.callback_query
        response = await self._build_events_response(user_channels, context.bot, show_all=False, channel_id=channel_id)
        keyboard = await self._build_channels_keyboard(user_channels, context.bot, current_channel=channel_id)
        
        await query.edit_message_text(response, reply_markup=keyboard, parse_mode='Markdown')

    async def _show_all_events_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_channels: Dict):
        """Показать все события (callback версия)"""
        query = update.callback_query
        response = await self._build_events_response(user_channels, context.bot, show_all=True)
        keyboard = await self._build_channels_keyboard(user_channels, context.bot, current_channel=None)
        
        await query.edit_message_text(response, reply_markup=keyboard, parse_mode='Markdown')

    async def _build_events_response(self, user_channels: Dict, bot, show_all: bool = True, channel_id: str = None) -> str:
        """Строит текстовый ответ со списком событий"""
        events = self.data_manager.load_events()
        today = datetime.now().date()
        
        filtered_events = self._filter_and_prepare_events(events, user_channels, today, show_all, channel_id)
        
        if not filtered_events:
            return "📭 Нет событий для ваших каналов." if show_all else "📭 Нет событий для этого канала."
        
        sorted_events = self._sort_events(filtered_events, show_all)
        
        return await self._format_events_response(sorted_events, show_all, today)

    async def _format_events_response(self, events: List[Dict], show_all: bool, today: datetime.date) -> str:
        """Форматирует события в текстовый ответ"""
        if show_all:
            response = "👁️ **Все события**\n"
        else:
            response = "📢 **События канала**\n"
        
        if not events:
            return response + "📭 Нет событий."
        
        current_date = None
        
        for event in events:
            event_date = event.get('next_date')
            if not event_date:
                continue
            
            # Добавляем заголовок даты при смене
            if event_date != current_date:
                current_date = event_date
                formatted_date = event.get('display_date', 'Неизвестная дата')
                formatted_date = DateUtils.format_date_with_weekday(formatted_date) if formatted_date != 'Неизвестная дата' else formatted_date
                if event_date == today:
                    response += f"\n🎯 **Сегодня:**\n"
                else:
                    response += f"\n**{formatted_date}:**\n"
            
            # Добавляем информацию о событии
            event_type_icon = "🔸" if event['event_type'] == 'yearly' else "🔹"
            pinned_status = "📌" if event.get('pinned_message_id') else ""
            response += f"  {event_type_icon} {event['description']} {pinned_status}\n"
        
        return response
        
    def _filter_and_prepare_events(self, events: Dict, user_channels: Dict, today: datetime.date, 
                                show_all: bool, channel_id: str = None) -> List[Dict]:
        """Фильтрует и подготавливает события для отображения из новой структуры"""
        filtered_events = []
        user_channel_ids = set(user_channels.keys())
        
        for channel_id_key, channel_data in events.items():
            if not show_all and channel_id_key != channel_id:
                continue
            if show_all and channel_id_key not in user_channel_ids:
                continue
            
            for storage_key, event_list in channel_data['events'].items():
                for event in event_list:
                    next_date = self.event_manager.calculate_next_date(storage_key, event['event_type'])
                    if next_date and next_date >= today:
                        event_with_channel = event.copy()
                        event_with_channel['channel_id'] = channel_id_key
                        event_with_channel['channel_name'] = channel_data['channel_name']
                        event_with_channel['next_date'] = next_date
                        event_with_channel['display_date'] = next_date.strftime("%d.%m.%Y")
                        filtered_events.append(event_with_channel)
        
        return filtered_events
    
    def _sort_events(self, events: List[Dict], show_all: bool) -> List[Dict]:
        """Сортирует события"""
        if show_all:
            return sorted(events, key=lambda x: (x.get('next_date', datetime.max.date()), x['channel_name']))
        else:
            return sorted(events, key=lambda x: x.get('next_date', datetime.max.date()))

    async def _format_events_response(self, events: List[Dict], show_all: bool, today: datetime.date) -> str:
        """Форматирует события в текстовый ответ"""
        if show_all:
            response = "👁️ **Все события**\n"
        else:
            response = "📢 **События канала**\n"
        
        if not events:
            return response + "📭 Нет событий."
        
        current_date = None
        
        for event in events:
            event_date = event.get('next_date')
            if not event_date:
                continue
            
            # Добавляем заголовок даты при смене
            if event_date != current_date:
                current_date = event_date
                formatted_date = event.get('display_date', 'Неизвестная дата')
                formatted_date = DateUtils.format_date_with_weekday(formatted_date) if formatted_date != 'Неизвестная дата' else formatted_date
                if event_date == today:
                    response += f"\n🎯 **Сегодня:**\n"
                else:
                    response += f"\n**{formatted_date}:**\n"
            
            # Добавляем информацию о событии
            event_type_icon = "🔸" if event['event_type'] == 'yearly' else "🔹"
            pinned_status = "📌" if event.get('pinned_message_id') else ""
            response += f"  {event_type_icon} {event['description']} {pinned_status}\n"
        
        return response
    
    async def _build_channels_keyboard(self, user_channels: Dict, bot, current_channel: str = None) -> Optional[InlineKeyboardMarkup]:
        """Строит клавиатуру для навигации по каналам"""
        if len(user_channels) <= 1:
            return None
        
        keyboard = []
        
        if current_channel:
            user_channels_list = list(user_channels.keys())
            current_index = user_channels_list.index(current_channel)
            
            nav_buttons = []
            if current_index > 0:
                prev_channel = user_channels_list[current_index - 1]
                prev_name = user_channels[prev_channel]['name']
                nav_buttons.append(InlineKeyboardButton(f"← {prev_name}", callback_data=f"view_events_{prev_channel}"))
            
            if current_index < len(user_channels_list) - 1:
                next_channel = user_channels_list[current_index + 1]
                next_name = user_channels[next_channel]['name']
                nav_buttons.append(InlineKeyboardButton(f"{next_name} →", callback_data=f"view_events_{next_channel}"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            keyboard.append([InlineKeyboardButton("👁️ Все события", callback_data="view_events_all")])
        
        else:
            for chat_id, channel_info in user_channels.items():
                channel_name = channel_info['name']
                keyboard.append([InlineKeyboardButton(f"📢 {channel_name}", callback_data=f"view_events_{chat_id}")])
        
        return InlineKeyboardMarkup(keyboard) if keyboard else None

    async def delete_event_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс удаления события"""
        user_id = str(update.effective_user.id)
        
        user_channels = await self.channel_manager.get_user_channels(user_id, context.bot)
        
        if not user_channels:
            await update.message.reply_text("📭 У вас нет общих каналов с ботом.")
            return
        
        context.user_data['user_channels'] = user_channels
        
        markup = self.calendar.create_calendar()
        await update.message.reply_text("🗑️ Выберите дату события для удаления:", reply_markup=markup)
        context.user_data['mode'] = 'deleting'
    
    async def _handle_delete_calendar_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик календаря для удаления событий"""
        query = update.callback_query
        
        if query.data.startswith("calendar_day_") or query.data == "calendar_today":
            await self._handle_delete_date_selection(update, context)
        elif query.data.startswith("calendar_nav_"):
            await self._handle_calendar_navigation(update, context)
    
    async def _handle_delete_date_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора даты для удаления"""
        query = update.callback_query
        
        if query.data == "calendar_today":
            date_obj = datetime.now()
        else:
            date_str = query.data.replace("calendar_day_", "")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        formatted_date = date_obj.strftime("%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")
        
        user_id = str(query.from_user.id)
        events_on_date = await self._get_events_for_date(date_str, user_id, context.bot)
        
        if not events_on_date:
            await query.edit_message_text(f"📭 На {formatted_date} нет событий для удаления.")
            context.user_data.pop('mode', None)
            return
        
        keyboard = []
        for event in events_on_date:
            event_description = event['description']
            if len(event_description) > 30:
                event_description = event_description[:27] + "..."
            
            event_type_icon = "🔸" if event['event_type'] == 'yearly' else "🔹"
            button_text = f"{event_type_icon} {event_description} ({event['channel_name']})"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_confirm_{event['id']}")])
        
        keyboard.append([InlineKeyboardButton("❌ Отменить удаление", callback_data="delete_cancel")])
        
        await query.edit_message_text(
            f"🗑️ События на {formatted_date}:\nВыберите событие для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _get_events_for_date(self, date_str: str, user_id: str, bot) -> List[Dict]:
        """Получает события на указанную дату из новой структуры"""
        events = self.data_manager.load_events()
        
        user_channels = await self.channel_manager.get_user_channels(user_id, bot)
        user_channel_ids = set(user_channels.keys())
        
        events_on_date = []
        
        for channel_id, channel_data in events.items():
            if channel_id not in user_channel_ids:
                continue
                
            if date_str in channel_data['events']:
                for event in channel_data['events'][date_str]:
                    event_with_channel = event.copy()
                    event_with_channel['channel_id'] = channel_id
                    event_with_channel['channel_name'] = channel_data['channel_name']
                    events_on_date.append(event_with_channel)
            
            date_parts = date_str.split('-')
            yearly_key = f"yearly_{date_parts[1]}-{date_parts[2]}"
            if yearly_key in channel_data['events']:
                for event in channel_data['events'][yearly_key]:
                    event_with_channel = event.copy()
                    event_with_channel['channel_id'] = channel_id
                    event_with_channel['channel_name'] = channel_data['channel_name']
                    events_on_date.append(event_with_channel)
        
        return events_on_date
    
    async def handle_delete_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик подтверждения удаления"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("delete_confirm_"):
            event_id = data.replace("delete_confirm_", "")
            user_id = str(query.from_user.id)
            
            # Получаем информацию о событии перед удалением
            events = self.data_manager.load_events()
            event_info = None
            for channel_id, channel_data in events.items():
                for date_key, event_list in channel_data['events'].items():
                    for event in event_list:
                        if event['id'] == event_id:
                            event_info = event
                            break
                    if event_info:
                        break
                if event_info:
                    break
            
            success = await self._delete_event_by_id(event_id, user_id, context.bot)
            
            if success:
                if event_info and event_info.get('pinned_message_id'):
                    await query.edit_message_text("✅ Событие удалено и сообщение откреплено! 📌")
                else:
                    await query.edit_message_text("✅ Событие успешно удалено!")
            else:
                await query.edit_message_text("❌ Не удалось удалить событие.")
            
            context.user_data.pop('mode', None)
            
        elif data == "delete_cancel":
            await query.edit_message_text("❌ Удаление отменено.")
            context.user_data.pop('mode', None)

    async def _delete_event_by_id(self, event_id: str, user_id: str, bot) -> bool:
        """Удаляет событие по ID из новой структуры и открепляет сообщение"""
        events = self.data_manager.load_events()
        
        user_channels = await self.channel_manager.get_user_channels(user_id, bot)
        user_channel_ids = set(user_channels.keys())
        
        # Сначала находим событие, чтобы получить информацию о закрепленном сообщении
        event_to_delete = None
        channel_id_to_delete = None
        
        for channel_id, channel_data in events.items():
            for date_key in list(channel_data['events'].keys()):
                for i, event in enumerate(channel_data['events'][date_key]):
                    if (event['id'] == event_id and 
                        (event['created_by'] == user_id or channel_id in user_channel_ids)):
                        event_to_delete = event
                        channel_id_to_delete = channel_id
                        break
                if event_to_delete:
                    break
            if event_to_delete:
                break
        
        if not event_to_delete:
            return False
        
        # Открепляем сообщение, если оно закреплено
        pinned_message_id = event_to_delete.get('pinned_message_id')
        if pinned_message_id:
            try:
                permissions = await ChannelManager.check_bot_permissions(channel_id_to_delete, bot)
                if permissions['can_pin_messages']:
                    await bot.unpin_chat_message(
                        chat_id=channel_id_to_delete,
                        message_id=pinned_message_id
                    )
                    logger.info(f"📌 Сообщение откреплено при удалении события: {event_id}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось открепить сообщение при удалении события: {e}")
        
        # Удаляем событие из структуры данных
        success = EventManager.delete_event_by_id(events, event_id, user_id, user_channel_ids)
        if success:
            return self.data_manager.save_events(events)
        return False
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды отмены"""
        if (context.user_data.get('waiting_for_event_description') or 
            context.user_data.get('waiting_for_channel_selection')):
            
            self.clear_event_context(context)
            await update.message.reply_text("❌ Текущая операция отменена.")
        else:
            await update.message.reply_text("ℹ️ Нет активных операций для отмены.")

    async def my_channels_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать каналы пользователя (динамически)"""
        user_id = str(update.effective_user.id)
        
        user_channels = await self.channel_manager.get_user_channels(user_id, context.bot)
        
        if not user_channels:
            await update.message.reply_text(
                "📭 У вас нет общих каналов/групп с ботом.\n\n"
                "💡 Чтобы использовать бота:\n"
                "1. Добавьте бота в канал/группу\n"
                "2. Убедитесь, что вы тоже участник этого канала/группы\n"
                "3. Бот автоматически получит доступ к каналу!"
            )
            return
        
        response = "📢 Ваши каналы и группы:\n\n"
        for chat_id, channel_info in user_channels.items():
            success, current_title, _ = await self.channel_manager.get_channel_info(chat_id, context.bot)
            status_icon = "✅" if success else "⚠️"
            status_text = " (активен)" if success else " (возможны проблемы с доступом)"
            channel_name = current_title if success else channel_info['name']
            response += f"{status_icon} {channel_name}{status_text}\n\n"

        response += "💡 Бот автоматически обновляет список каналов!"
        await update.message.reply_text(response)

    def clear_event_context(self, context: ContextTypes.DEFAULT_TYPE):
        """Очищает временные данные создания события"""
        keys_to_remove = [
            'waiting_for_event_description', 'selected_date', 
            'selected_channel', 'waiting_for_channel_selection',
            'event_type', 'mode', 'deleting_event'
        ]
        for key in keys_to_remove:
            context.user_data.pop(key, None)