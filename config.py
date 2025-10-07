import os
from dotenv import load_dotenv

load_dotenv()

# Константы
DATA_DIR = "data"
EVENTS_FILE = os.path.join(DATA_DIR, 'channel_events.json')
CHANNELS_FILE = os.path.join(DATA_DIR, 'channels.json')

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Создаем директорию для данных при её отсутствии
os.makedirs(DATA_DIR, exist_ok=True)