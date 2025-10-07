# Telegram-Bot-Calendar - Отслеживание событий телеграмм-канала ![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python) ![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-22.5-2CA5E0?style=flat-square&logo=telegram) ![Status](https://img.shields.io/badge/Status-Inactive-red?style=flat-square)

Бот для управления событиями в Telegram-каналах с автоматическими уведомлениями и закреплением сообщений.

🌐 **Бот в Telegram**: [@BingpupCalendarBot](https://t.me/BingpupCalendarBot)
https://t.me/BingpupCalendarBot

## 🚀 Функциональность

- 📅 Создание разовых и ежегодных событий
- 🔔 Автоматические уведомления о событиях
- 📌 Автоматическое закрепление сообщений
- 👥 Поддержка множества каналов
- 🗑️ Удобное удаление событий

## 📸 Пример использования

Добавление события:

![Запись добавления нового события](https://github.com/user-attachments/assets/93544218-136a-470a-93fa-4e1def68556d)

Автоматическое закрепление записи в день события:

<img width="260" alt="image" src="https://github.com/user-attachments/assets/6b36ad7d-276c-48e5-ae39-92dd1a67844c" />

## ⚡ Быстрый старт

### 1. Добавьте бота в канал
- Пригласите [@BingpupCalendarBot](https://t.me/BingpupCalendarBot) в ваш канал
- Выдайте права администратора
- Включите разрешения: "Отправка сообщений" и "Закрепление сообщений"
  
### 2. Использование в канале
```
/start - описание всех команд
/addevent - добавить новое событие
/events - просмотреть все события
/deleteevent - удалить событие
/mychannels - список доступных каналов
/checkperms - Проверить права бота в ваших каналах
```

## 🛠️ Для разработчиков

### Структура проекта
```
Telegram-bot-Calendar/
├── handlers/ # Обработчики команд
│ ├── channel_handlers.py
│ └── event_handlers.py
├── managers/ # Бизнес-логика
│ ├── channel_manager.py
│ └── event_manager.py
├── services/ # Фоновые сервисы
│ ├── notification_service.py
│ └── scheduler.py
├── utils/ # Вспомогательные утилиты
│ ├── calendar.py
│ ├── data_manager.py
│ └── date_utils.py
├── main.py # Точка входа
├── config.py # Конфигурация
├── requirements.txt # Зависимости
└── README.md # Документация
```

### Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Nelliel2/Telegram-bot-Calendar.git
cd Telegram-bot-Calendar
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл .env:
```env
BOT_TOKEN=your_bot_token_here
```

4. Запустите бота:
```bash
python main.py
```   
## ⚠️ Текущий статус
**Бот временно неактивен** - хостинг находится в процессе настройки. Код полностью рабочий и готов к развертыванию.

## ❗ Важные примечания
* Все участники канала могут создавать и удалять события
* Бот требует права на отправку и закрепление сообщений
* На данный момент работает только по Московскому времени (UTC+3)
* Поддерживает как разовые, так и ежегодные события
* Автоматически открепляет старые уведомленя
